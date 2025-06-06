"""
Enhanced Metaphor Extraction for CANOPY

This module provides advanced metaphor extraction capabilities with
structured Claude 3 Haiku prompts, Redis caching, and robust fallback mechanisms.
"""

import json
import asyncio
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import re
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict
from redis.asyncio import Redis
from structured_logging import get_logger

# For LLM integration
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from models.emotional_state import SymbolicMapping, EmotionalMetaphor

logger = get_logger(__name__)

class MetaphorDomain(Enum):
    """Domains for metaphor classification."""
    NATURAL = "natural"
    ARCHITECTURAL = "architectural"
    JOURNEY = "journey"
    CONTAINER = "container"
    MECHANICAL = "mechanical"
    ORGANIC = "organic"
    CELESTIAL = "celestial"
    ELEMENTAL = "elemental"

class MetaphorTheme(Enum):
    """Themes for metaphor analysis."""
    GROWTH = "growth"
    TRANSFORMATION = "transformation"
    MOVEMENT = "movement"
    STABILITY = "stability"
    CONFLICT = "conflict"
    HARMONY = "harmony"
    ISOLATION = "isolation"
    CONNECTION = "connection"

@dataclass
class PromptTemplate:
    """Template for structured Claude prompts."""
    system_prompt: str
    user_template: str
    max_tokens: int = 1000
    temperature: float = 0.4
    response_format: str = "json"

class PromptTemplates:
    """Collection of structured Claude 3 Haiku prompts for metaphor extraction."""
    
    METAPHOR_EXTRACTION = PromptTemplate(
        system_prompt="""You are CANOPY, an advanced symbolic analysis system for emotional wellness applications. 

Your role is to extract metaphors and symbolic meanings from user input while maintaining strict HIPAA compliance and emotional safety.

CRITICAL RULES:
1. NEVER include any personally identifiable information in responses
2. NEVER attempt to diagnose or provide medical advice
3. Focus on symbolic representation, not problem-solving
4. Ensure all responses maintain emotional safety and support
5. If input contains crisis indicators, note them but do not provide crisis intervention advice

Your responses must be valid JSON objects with the specified structure.""",
        
        user_template="""Analyze the following text for metaphors and symbolic content:

Text: "{text}"

{context_section}

Please provide a JSON response with this exact structure:
{{
    "primary_symbol": "string - main symbolic element identified",
    "archetype": "string - primary Jungian archetype (hero, shadow, anima, animus, mentor, trickster, self, persona, caregiver, sage, explorer, creator, ruler, innocent, magician, lover, everyman, jester, outlaw, destroyer)",
    "alternative_symbols": ["string array - 2-3 alternative symbolic representations"],
    "valence": "float - emotional valence from -1.0 (negative) to 1.0 (positive)",
    "arousal": "float - emotional arousal from 0.0 (calm) to 1.0 (intense)",
    "metaphors": [
        {{
            "text": "string - exact metaphorical phrase from input",
            "symbol": "string - symbolic meaning",
            "confidence": "float - confidence from 0.0 to 1.0",
            "domain": "string - metaphor domain (natural, architectural, journey, container, mechanical, organic, celestial, elemental)",
            "theme": "string - metaphor theme (growth, transformation, movement, stability, conflict, harmony, isolation, connection)"
        }}
    ],
    "confidence": "float - overall confidence in analysis from 0.0 to 1.0",
    "safety_flags": ["string array - any safety concerns detected"],
    "symbolic_complexity": "int - complexity score from 1 (simple) to 5 (highly complex)"
}}

Ensure all JSON values are properly formatted and all required fields are present.""",
        max_tokens=1200,
        temperature=0.3
    )
    
    SYMBOLIC_EVOLUTION = PromptTemplate(
        system_prompt="""You are CANOPY's symbolic evolution analyzer. You track how symbolic representations change over time while maintaining HIPAA compliance.

CRITICAL RULES:
1. NEVER reference specific personal details from previous sessions
2. Focus on symbolic patterns, not individual circumstances
3. Maintain emotional safety in all analyses
4. Provide supportive and growth-oriented interpretations""",
        
        user_template="""Analyze the symbolic evolution in this sequence:

Current Symbol: {current_symbol}
Previous Symbols: {previous_symbols}

Provide analysis as JSON:
{{
    "evolution_pattern": "string - emerging, stable, transitional, or exploratory",
    "symbolic_growth": "string - description of growth or change",
    "continuity_themes": ["string array - consistent themes across symbols"],
    "transformation_indicators": ["string array - signs of symbolic transformation"],
    "stability_score": "float - stability from 0.0 to 1.0",
    "growth_trajectory": "string - positive, neutral, or concerning"
}}""",
        max_tokens=800,
        temperature=0.4
    )

class MetaphorCache:
    """Redis-based distributed cache for metaphor extraction results."""
    
    def __init__(self, redis_client: Redis, ttl_hours: int = 24):
        """
        Initialize the metaphor cache.
        
        Args:
            redis_client: Redis client instance
            ttl_hours: Time-to-live for cached entries in hours
        """
        self.redis = redis_client
        self.ttl_seconds = ttl_hours * 3600
        self.cache_prefix = "canopy:metaphor_cache"
        self._logger = get_logger(f"{__name__}.MetaphorCache")
    
    def _generate_cache_key(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a cache key from input text and context.
        
        Args:
            text: Input text (PHI is hashed, not stored)
            context: Optional context data
            
        Returns:
            Cache key string
        """
        # Create hash of text to avoid storing PHI
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # Include relevant context elements (not user-specific data)
        context_elements = []
        if context:
            # Only include non-PHI context elements
            safe_context = {k: v for k, v in context.items() 
                          if k in ['biomarker_types', 'session_type', 'interaction_mode']}
            if safe_context:
                context_str = json.dumps(safe_context, sort_keys=True)
                context_hash = hashlib.sha256(context_str.encode()).hexdigest()[:8]
                context_elements.append(context_hash)
        
        key_parts = [self.cache_prefix, text_hash[:16]] + context_elements
        return ":".join(key_parts)
    
    async def get(self, text: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached metaphor extraction result.
        
        Args:
            text: Input text
            context: Optional context data
            
        Returns:
            Cached result or None if not found
        """
        try:
            cache_key = self._generate_cache_key(text, context)
            cached_data = await self.redis.get(cache_key)
            
            if cached_data:
                result = json.loads(cached_data)
                self._logger.debug(f"Cache hit for metaphor extraction")
                return result
            
            return None
            
        except Exception as e:
            self._logger.error(f"Error retrieving from metaphor cache: {str(e)}")
            return None
    
    async def set(
        self, 
        text: str, 
        result: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Cache metaphor extraction result.
        
        Args:
            text: Input text
            result: Extraction result to cache
            context: Optional context data
        """
        try:
            cache_key = self._generate_cache_key(text, context)
            
            # Add cache metadata
            cache_data = {
                "result": result,
                "cached_at": datetime.now().isoformat(),
                "text_length": len(text)
            }
            
            await self.redis.setex(
                cache_key, 
                self.ttl_seconds, 
                json.dumps(cache_data, default=str)
            )
            
            self._logger.debug(f"Cached metaphor extraction result")
            
        except Exception as e:
            self._logger.error(f"Error caching metaphor result: {str(e)}")
    
    async def clear_user_cache(self, user_pattern: str) -> int:
        """
        Clear cache entries for a specific pattern (for user data deletion).
        
        Args:
            user_pattern: Pattern to match for deletion
            
        Returns:
            Number of entries deleted
        """
        try:
            pattern = f"{self.cache_prefix}:*{user_pattern}*"
            keys = await self.redis.keys(pattern)
            
            if keys:
                deleted = await self.redis.delete(*keys)
                self._logger.info(f"Cleared {deleted} cache entries for pattern: {user_pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            self._logger.error(f"Error clearing user cache: {str(e)}")
            return 0

class FallbackMetaphorExtractor:
    """Rule-based fallback metaphor extractor for when LLM services fail."""
    
    def __init__(self):
        """Initialize the fallback extractor with rule patterns."""
        self._logger = get_logger(f"{__name__}.FallbackMetaphorExtractor")
        
        # Symbolic pattern mappings
        self.symbol_patterns = {
            # Water metaphors
            r'\b(water|ocean|river|stream|flow|current|tide|wave|sink|swim|drown|float)\b': {
                'symbol': 'water',
                'archetype': 'self',
                'domain': MetaphorDomain.ELEMENTAL,
                'theme': MetaphorTheme.MOVEMENT
            },
            
            # Fire metaphors
            r'\b(fire|flame|burn|spark|ignite|blaze|ember|ashes|smoke)\b': {
                'symbol': 'fire',
                'archetype': 'creator',
                'domain': MetaphorDomain.ELEMENTAL,
                'theme': MetaphorTheme.TRANSFORMATION
            },
            
            # Journey metaphors
            r'\b(path|road|journey|walk|travel|destination|lost|found|crossroads|bridge)\b': {
                'symbol': 'path',
                'archetype': 'hero',
                'domain': MetaphorDomain.JOURNEY,
                'theme': MetaphorTheme.MOVEMENT
            },
            
            # Growth metaphors
            r'\b(tree|root|branch|leaf|seed|bloom|grow|flourish|wither|garden)\b': {
                'symbol': 'tree',
                'archetype': 'sage',
                'domain': MetaphorDomain.ORGANIC,
                'theme': MetaphorTheme.GROWTH
            },
            
            # Container metaphors
            r'\b(box|container|bottle|vessel|shell|cocoon|cage|room|house|prison)\b': {
                'symbol': 'container',
                'archetype': 'innocent',
                'domain': MetaphorDomain.CONTAINER,
                'theme': MetaphorTheme.STABILITY
            },
            
            # Light/dark metaphors
            r'\b(light|dark|shadow|bright|dim|glow|sunshine|darkness|dawn|dusk)\b': {
                'symbol': 'light',
                'archetype': 'magician',
                'domain': MetaphorDomain.CELESTIAL,
                'theme': MetaphorTheme.TRANSFORMATION
            }
        }
        
        # Compile patterns for efficiency
        self.compiled_patterns = {
            re.compile(pattern, re.IGNORECASE): data 
            for pattern, data in self.symbol_patterns.items()
        }
        
        # Emotional valence patterns
        self.valence_patterns = {
            'positive': re.compile(r'\b(happy|joy|love|peace|calm|bright|warm|grow|heal|hope)\b', re.IGNORECASE),
            'negative': re.compile(r'\b(sad|pain|fear|dark|cold|broken|lost|hurt|angry|trapped)\b', re.IGNORECASE),
            'neutral': re.compile(r'\b(think|consider|wonder|maybe|perhaps|somewhat|kind of)\b', re.IGNORECASE)
        }
        
        # Arousal patterns
        self.arousal_patterns = {
            'high': re.compile(r'\b(intense|overwhelming|racing|panic|explode|rush|urgent|extreme)\b', re.IGNORECASE),
            'medium': re.compile(r'\b(strong|significant|noticeable|clear|definite|marked)\b', re.IGNORECASE),
            'low': re.compile(r'\b(gentle|mild|soft|quiet|peaceful|calm|still|subtle)\b', re.IGNORECASE)
        }
    
    def extract(
        self, 
        text: str, 
        biomarkers: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> SymbolicMapping:
        """
        Extract metaphors using rule-based patterns.
        
        Args:
            text: Input text for analysis
            biomarkers: Optional biomarker data
            context: Optional context information
            
        Returns:
            SymbolicMapping with extracted information
        """
        self._logger.info("Using fallback metaphor extraction")
        
        # Find symbolic patterns
        found_symbols = []
        primary_symbol = "unknown"
        archetype = "self"
        domain = MetaphorDomain.NATURAL
        theme = MetaphorTheme.STABILITY
        
        for pattern, symbol_data in self.compiled_patterns.items():
            matches = pattern.findall(text.lower())
            if matches:
                found_symbols.append({
                    'matches': matches,
                    'symbol': symbol_data['symbol'],
                    'archetype': symbol_data['archetype'],
                    'domain': symbol_data['domain'],
                    'theme': symbol_data['theme']
                })
        
        # Use most frequent symbol as primary
        if found_symbols:
            # Count matches for each symbol
            symbol_counts = {}
            for symbol_info in found_symbols:
                symbol = symbol_info['symbol']
                count = len(symbol_info['matches'])
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + count
            
            # Select primary symbol
            primary_symbol = max(symbol_counts, key=symbol_counts.get)
            primary_info = next(s for s in found_symbols if s['symbol'] == primary_symbol)
            archetype = primary_info['archetype']
            domain = primary_info['domain']
            theme = primary_info['theme']
        
        # Calculate valence
        valence = 0.0
        pos_matches = len(self.valence_patterns['positive'].findall(text))
        neg_matches = len(self.valence_patterns['negative'].findall(text))
        
        if pos_matches > neg_matches:
            valence = min(0.8, pos_matches * 0.2)
        elif neg_matches > pos_matches:
            valence = max(-0.8, -neg_matches * 0.2)
        
        # Calculate arousal
        arousal = 0.3  # Default medium-low
        if self.arousal_patterns['high'].search(text):
            arousal = 0.8
        elif self.arousal_patterns['medium'].search(text):
            arousal = 0.6
        elif self.arousal_patterns['low'].search(text):
            arousal = 0.2
        
        # Create metaphors list
        metaphors = []
        for symbol_info in found_symbols[:3]:  # Limit to top 3
            for match in symbol_info['matches'][:2]:  # Limit matches per symbol
                metaphors.append(EmotionalMetaphor(
                    text=match,
                    symbol=symbol_info['symbol'],
                    confidence=0.6
                ))
        
        # Generate alternative symbols
        alternative_symbols = []
        if len(found_symbols) > 1:
            alternative_symbols = [s['symbol'] for s in found_symbols[1:4]]
        else:
            # Default alternatives based on primary symbol
            alt_map = {
                'water': ['river', 'ocean'],
                'fire': ['light', 'energy'],
                'path': ['journey', 'bridge'],
                'tree': ['growth', 'roots'],
                'container': ['shelter', 'boundary'],
                'light': ['hope', 'clarity']
            }
            alternative_symbols = alt_map.get(primary_symbol, ['symbol', 'meaning'])
        
        return SymbolicMapping(
            primary_symbol=primary_symbol,
            archetype=archetype,
            alternative_symbols=alternative_symbols,
            valence=valence,
            arousal=arousal,
            metaphors=metaphors,
            timestamp=datetime.now(),
            confidence=0.5  # Lower confidence for fallback
        )

class EnhancedMetaphorExtractor:
    """
    Enhanced metaphor extraction system with Claude 3 Haiku integration,
    Redis caching, and sophisticated fallback mechanisms.
    """
    
    def __init__(
        self, 
        redis_client: Redis,
        api_key: Optional[str] = None,
        cache_ttl_hours: int = 24,
        enable_caching: bool = True
    ):
        """
        Initialize the enhanced metaphor extractor.
        
        Args:
            redis_client: Redis client for caching
            api_key: Anthropic API key
            cache_ttl_hours: Cache TTL in hours
            enable_caching: Whether to enable caching
        """
        self._logger = get_logger(f"{__name__}.EnhancedMetaphorExtractor")
        
        # Initialize components
        self.redis = redis_client
        self.enable_caching = enable_caching
        
        if enable_caching:
            self.cache = MetaphorCache(redis_client, cache_ttl_hours)
        
        self.fallback_extractor = FallbackMetaphorExtractor()
        self.prompt_templates = PromptTemplates()
        
        # Initialize Claude client
        self.anthropic_client = None
        if ANTHROPIC_AVAILABLE and api_key:
            self.anthropic_client = Anthropic(api_key=api_key)
            self._logger.info("Enhanced metaphor extractor initialized with Claude integration")
        else:
            self._logger.warning("Claude client not available, using fallback only")
        
        # Statistics
        self.stats = {
            'total_extractions': 0,
            'claude_extractions': 0,
            'fallback_extractions': 0,
            'cache_hits': 0,
            'errors': 0
        }
    
    async def extract_metaphors(
        self,
        text: str,
        biomarkers: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> SymbolicMapping:
        """
        Extract metaphors from input text with caching and fallback.
        
        Args:
            text: Input text for analysis
            biomarkers: Optional biomarker data
            context: Optional context information
            use_cache: Whether to use caching
            
        Returns:
            SymbolicMapping with extracted metaphors and symbols
        """
        self.stats['total_extractions'] += 1
        
        # Check cache first
        if self.enable_caching and use_cache:
            cached_result = await self.cache.get(text, context)
            if cached_result and 'result' in cached_result:
                self.stats['cache_hits'] += 1
                self._logger.debug("Using cached metaphor extraction result")
                return self._dict_to_symbolic_mapping(cached_result['result'])
        
        # Try Claude extraction first
        if self.anthropic_client:
            try:
                result = await self._extract_with_claude(text, biomarkers, context)
                self.stats['claude_extractions'] += 1
                
                # Cache the result
                if self.enable_caching and use_cache:
                    await self.cache.set(text, self._symbolic_mapping_to_dict(result), context)
                
                return result
                
            except Exception as e:
                self._logger.error(f"Claude extraction failed: {str(e)}")
                self.stats['errors'] += 1
        
        # Fall back to rule-based extraction
        try:
            result = self.fallback_extractor.extract(text, biomarkers, context)
            self.stats['fallback_extractions'] += 1
            
            # Cache fallback result with shorter TTL
            if self.enable_caching and use_cache:
                await self.cache.set(text, self._symbolic_mapping_to_dict(result), context)
            
            return result
            
        except Exception as e:
            self._logger.error(f"Fallback extraction failed: {str(e)}")
            self.stats['errors'] += 1
            
            # Return minimal default mapping
            return self._create_default_mapping(text)
    
    async def _extract_with_claude(
        self,
        text: str,
        biomarkers: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> SymbolicMapping:
        """Extract metaphors using Claude 3 Haiku."""
        # Prepare context section
        context_section = ""
        if context:
            safe_context = {k: v for k, v in context.items() 
                          if k not in ['user_id', 'session_id', 'personal_info']}
            if safe_context:
                context_section = f"Additional context: {json.dumps(safe_context)}"
        
        if biomarkers:
            biomarker_types = list(biomarkers.keys())
            context_section += f"\nBiomarker types available: {biomarker_types}"
        
        # Format prompt
        prompt = self.prompt_templates.METAPHOR_EXTRACTION.user_template.format(
            text=text,
            context_section=context_section
        )
        
        # Make API call with retry logic
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=self.prompt_templates.METAPHOR_EXTRACTION.max_tokens,
                    temperature=self.prompt_templates.METAPHOR_EXTRACTION.temperature,
                    system=self.prompt_templates.METAPHOR_EXTRACTION.system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Parse response
                content = response.content[0].text
                return self._parse_claude_response(content, text)
                
            except Exception as e:
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self._logger.warning(f"Claude API attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
                    await asyncio.sleep(wait_time)
                else:
                    raise e
    
    def _parse_claude_response(self, content: str, original_text: str) -> SymbolicMapping:
        """Parse Claude's JSON response into a SymbolicMapping."""
        try:
            # Extract JSON from response
            start = content.find('{')
            end = content.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_content = content[start:end]
                data = json.loads(json_content)
            else:
                raise ValueError("No valid JSON found in Claude response")
            
            # Convert metaphors
            metaphors = []
            for m_data in data.get('metaphors', []):
                metaphors.append(EmotionalMetaphor(
                    text=m_data.get('text', ''),
                    symbol=m_data.get('symbol', ''),
                    confidence=m_data.get('confidence', 0.5)
                ))
            
            return SymbolicMapping(
                primary_symbol=data.get('primary_symbol', 'unknown'),
                archetype=data.get('archetype', 'self'),
                alternative_symbols=data.get('alternative_symbols', []),
                valence=data.get('valence', 0.0),
                arousal=data.get('arousal', 0.5),
                metaphors=metaphors,
                timestamp=datetime.now(),
                confidence=data.get('confidence', 0.7)
            )
            
        except Exception as e:
            self._logger.error(f"Failed to parse Claude response: {str(e)}")
            raise e
    
    def _symbolic_mapping_to_dict(self, mapping: SymbolicMapping) -> Dict[str, Any]:
        """Convert SymbolicMapping to dictionary for caching."""
        return {
            'primary_symbol': mapping.primary_symbol,
            'archetype': mapping.archetype,
            'alternative_symbols': mapping.alternative_symbols,
            'valence': mapping.valence,
            'arousal': mapping.arousal,
            'metaphors': [
                {
                    'text': m.text,
                    'symbol': m.symbol,
                    'confidence': m.confidence
                }
                for m in mapping.metaphors
            ],
            'confidence': mapping.confidence,
            'timestamp': mapping.timestamp.isoformat()
        }
    
    def _dict_to_symbolic_mapping(self, data: Dict[str, Any]) -> SymbolicMapping:
        """Convert dictionary to SymbolicMapping."""
        metaphors = []
        for m_data in data.get('metaphors', []):
            metaphors.append(EmotionalMetaphor(
                text=m_data.get('text', ''),
                symbol=m_data.get('symbol', ''),
                confidence=m_data.get('confidence', 0.5)
            ))
        
        return SymbolicMapping(
            primary_symbol=data.get('primary_symbol', 'unknown'),
            archetype=data.get('archetype', 'self'),
            alternative_symbols=data.get('alternative_symbols', []),
            valence=data.get('valence', 0.0),
            arousal=data.get('arousal', 0.5),
            metaphors=metaphors,
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            confidence=data.get('confidence', 0.5)
        )
    
    def _create_default_mapping(self, text: str) -> SymbolicMapping:
        """Create a default mapping when all extraction methods fail."""
        return SymbolicMapping(
            primary_symbol="unknown",
            archetype="self",
            alternative_symbols=["symbol", "meaning"],
            valence=0.0,
            arousal=0.3,
            metaphors=[],
            timestamp=datetime.now(),
            confidence=0.1
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        return self.stats.copy()
    
    async def clear_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries matching pattern."""
        if not self.enable_caching:
            return 0
        
        if pattern:
            return await self.cache.clear_user_cache(pattern)
        else:
            # Clear all cache entries (admin function)
            keys = await self.redis.keys(f"{self.cache.cache_prefix}:*")
            if keys:
                deleted = await self.redis.delete(*keys)
                self._logger.info(f"Cleared {deleted} cache entries")
                return deleted
            return 0 