"""
Accessibility Internationalization Module

This module provides internationalization support for accessibility features,
including language detection, translation, and cultural adaptations.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import logging
from pydantic import BaseModel
import re

logger = logging.getLogger(__name__)


class LanguageCode(str, Enum):
    """ISO 639-1 language codes for supported languages."""
    EN = "en"  # English
    ES = "es"  # Spanish
    FR = "fr"  # French
    DE = "de"  # German
    ZH = "zh"  # Chinese
    JA = "ja"  # Japanese
    AR = "ar"  # Arabic
    RU = "ru"  # Russian
    PT = "pt"  # Portuguese
    HI = "hi"  # Hindi
    ASL = "asl"  # American Sign Language (special case)
    BSL = "bsl"  # British Sign Language (special case)


class ReadingDirection(str, Enum):
    """Reading directions for different languages."""
    LTR = "ltr"  # Left to right
    RTL = "rtl"  # Right to left
    TTB = "ttb"  # Top to bottom


class LanguageComplexityLevel(BaseModel):
    """Model for language complexity levels."""
    level: int  # 1-10
    vocabulary_size: int
    max_sentence_length: int
    max_paragraph_length: int
    use_idioms: bool
    use_metaphors: bool
    use_technical_terms: bool
    use_passive_voice: bool


class CulturalConsideration(BaseModel):
    """Model for cultural considerations in accessibility."""
    culture_code: str
    color_associations: Dict[str, str]
    symbol_meanings: Dict[str, str]
    taboo_topics: List[str]
    communication_style: str
    emotional_expression: str


class LanguageProfile(BaseModel):
    """Model for language-specific accessibility profile."""
    code: LanguageCode
    name: str
    reading_direction: ReadingDirection
    complexity_levels: Dict[int, LanguageComplexityLevel]
    cultural_considerations: Optional[List[CulturalConsideration]] = None
    special_characters: Optional[List[str]] = None
    screen_reader_compatibility: Optional[Dict[str, str]] = None


# Define language profiles
LANGUAGE_PROFILES = {
    LanguageCode.EN: LanguageProfile(
        code=LanguageCode.EN,
        name="English",
        reading_direction=ReadingDirection.LTR,
        complexity_levels={
            1: LanguageComplexityLevel(
                level=1,
                vocabulary_size=500,
                max_sentence_length=8,
                max_paragraph_length=3,
                use_idioms=False,
                use_metaphors=False,
                use_technical_terms=False,
                use_passive_voice=False
            ),
            5: LanguageComplexityLevel(
                level=5,
                vocabulary_size=2000,
                max_sentence_length=15,
                max_paragraph_length=5,
                use_idioms=True,
                use_metaphors=True,
                use_technical_terms=False,
                use_passive_voice=True
            ),
            10: LanguageComplexityLevel(
                level=10,
                vocabulary_size=10000,
                max_sentence_length=30,
                max_paragraph_length=10,
                use_idioms=True,
                use_metaphors=True,
                use_technical_terms=True,
                use_passive_voice=True
            )
        },
        cultural_considerations=[
            CulturalConsideration(
                culture_code="us",
                color_associations={"red": "danger", "green": "success"},
                symbol_meanings={"thumbs_up": "approval"},
                taboo_topics=["politics", "religion"],
                communication_style="direct",
                emotional_expression="moderate"
            )
        ],
        screen_reader_compatibility={
            "aria_labels": "Use ARIA labels for all interactive elements",
            "heading_structure": "Use proper heading structure"
        }
    ),
    LanguageCode.ES: LanguageProfile(
        code=LanguageCode.ES,
        name="Spanish",
        reading_direction=ReadingDirection.LTR,
        complexity_levels={
            1: LanguageComplexityLevel(
                level=1,
                vocabulary_size=500,
                max_sentence_length=8,
                max_paragraph_length=3,
                use_idioms=False,
                use_metaphors=False,
                use_technical_terms=False,
                use_passive_voice=False
            ),
            5: LanguageComplexityLevel(
                level=5,
                vocabulary_size=2000,
                max_sentence_length=15,
                max_paragraph_length=5,
                use_idioms=True,
                use_metaphors=True,
                use_technical_terms=False,
                use_passive_voice=True
            ),
            10: LanguageComplexityLevel(
                level=10,
                vocabulary_size=10000,
                max_sentence_length=30,
                max_paragraph_length=10,
                use_idioms=True,
                use_metaphors=True,
                use_technical_terms=True,
                use_passive_voice=True
            )
        },
        special_characters=["á", "é", "í", "ó", "ú", "ñ", "¿", "¡"],
        cultural_considerations=[
            CulturalConsideration(
                culture_code="es",
                color_associations={"red": "passion", "yellow": "joy"},
                symbol_meanings={"thumbs_up": "approval"},
                taboo_topics=["civil war"],
                communication_style="indirect",
                emotional_expression="expressive"
            )
        ]
    ),
    LanguageCode.AR: LanguageProfile(
        code=LanguageCode.AR,
        name="Arabic",
        reading_direction=ReadingDirection.RTL,
        complexity_levels={
            1: LanguageComplexityLevel(
                level=1,
                vocabulary_size=500,
                max_sentence_length=8,
                max_paragraph_length=3,
                use_idioms=False,
                use_metaphors=False,
                use_technical_terms=False,
                use_passive_voice=False
            ),
            5: LanguageComplexityLevel(
                level=5,
                vocabulary_size=2000,
                max_sentence_length=15,
                max_paragraph_length=5,
                use_idioms=True,
                use_metaphors=True,
                use_technical_terms=False,
                use_passive_voice=True
            ),
            10: LanguageComplexityLevel(
                level=10,
                vocabulary_size=10000,
                max_sentence_length=30,
                max_paragraph_length=10,
                use_idioms=True,
                use_metaphors=True,
                use_technical_terms=True,
                use_passive_voice=True
            )
        },
        cultural_considerations=[
            CulturalConsideration(
                culture_code="sa",
                color_associations={"green": "islam", "white": "purity"},
                symbol_meanings={"thumbs_up": "approval"},
                taboo_topics=["alcohol", "dating"],
                communication_style="indirect",
                emotional_expression="reserved"
            )
        ]
    ),
    LanguageCode.ASL: LanguageProfile(
        code=LanguageCode.ASL,
        name="American Sign Language",
        reading_direction=ReadingDirection.LTR,
        complexity_levels={
            1: LanguageComplexityLevel(
                level=1,
                vocabulary_size=300,
                max_sentence_length=5,
                max_paragraph_length=3,
                use_idioms=False,
                use_metaphors=False,
                use_technical_terms=False,
                use_passive_voice=False
            ),
            5: LanguageComplexityLevel(
                level=5,
                vocabulary_size=1000,
                max_sentence_length=10,
                max_paragraph_length=5,
                use_idioms=True,
                use_metaphors=True,
                use_technical_terms=False,
                use_passive_voice=False
            ),
            10: LanguageComplexityLevel(
                level=10,
                vocabulary_size=5000,
                max_sentence_length=20,
                max_paragraph_length=10,
                use_idioms=True,
                use_metaphors=True,
                use_technical_terms=True,
                use_passive_voice=False
            )
        },
        screen_reader_compatibility={
            "video_descriptions": "Include ASL video translations",
            "visual_alerts": "Use visual alerts for notifications"
        }
    )
}


class LanguageDetector:
    """
    Utility for detecting the language of text.
    """
    
    @staticmethod
    def detect_language(text: str) -> LanguageCode:
        """
        Detect the language of text.
        
        Args:
            text: Text to detect language of
            
        Returns:
            Detected language code
        """
        # This is a simplified implementation
        # In a real implementation, this would use a language detection library
        
        # Check for Arabic characters
        if re.search(r'[\u0600-\u06FF]', text):
            return LanguageCode.AR
        
        # Check for Spanish characters
        if re.search(r'[áéíóúñ¿¡]', text):
            return LanguageCode.ES
        
        # Default to English
        return LanguageCode.EN


class I18nAdapter:
    """
    Adapter for internationalization of accessibility features.
    """
    
    def __init__(self, language_code: LanguageCode = LanguageCode.EN):
        """
        Initialize the adapter.
        
        Args:
            language_code: Language code
        """
        self.language_code = language_code
        self.language_profile = LANGUAGE_PROFILES.get(
            language_code, LANGUAGE_PROFILES[LanguageCode.EN]
        )
    
    def get_complexity_level(self, level: int) -> LanguageComplexityLevel:
        """
        Get the language complexity level.
        
        Args:
            level: Complexity level (1-10)
            
        Returns:
            Language complexity level
        """
        # Clamp level to valid range
        level = max(1, min(10, level))
        
        # Find the closest defined level
        defined_levels = list(self.language_profile.complexity_levels.keys())
        closest_level = min(defined_levels, key=lambda x: abs(x - level))
        
        return self.language_profile.complexity_levels[closest_level]
    
    def adapt_text_direction(self, content: Dict) -> Dict:
        """
        Adapt content for text direction.
        
        Args:
            content: Content to adapt
            
        Returns:
            Adapted content
        """
        content["reading_direction"] = self.language_profile.reading_direction.value
        return content
    
    def adapt_complexity(self, text: str, target_level: int) -> str:
        """
        Adapt text to target complexity level.
        
        Args:
            text: Text to adapt
            target_level: Target complexity level
            
        Returns:
            Adapted text
        """
        # This is a simplified implementation
        # In a real implementation, this would use NLP techniques
        
        complexity_level = self.get_complexity_level(target_level)
        
        # Simulate complexity adaptation
        if target_level <= 3:
            # Very simple language
            return f"{text}\n\n[Simplified to basic {self.language_profile.name}]"
        elif target_level <= 7:
            # Moderate complexity
            return f"{text}\n\n[Adapted to moderate {self.language_profile.name}]"
        else:
            # Full complexity
            return text
    
    def get_cultural_considerations(self, culture_code: Optional[str] = None) -> List[CulturalConsideration]:
        """
        Get cultural considerations for the language.
        
        Args:
            culture_code: Optional culture code to filter by
            
        Returns:
            List of cultural considerations
        """
        if not self.language_profile.cultural_considerations:
            return []
        
        if culture_code:
            return [
                c for c in self.language_profile.cultural_considerations
                if c.culture_code == culture_code
            ]
        else:
            return self.language_profile.cultural_considerations
    
    def get_screen_reader_guidance(self) -> Dict[str, str]:
        """
        Get screen reader guidance for the language.
        
        Returns:
            Screen reader guidance
        """
        return self.language_profile.screen_reader_compatibility or {}


def get_i18n_adapter(language_code: LanguageCode = LanguageCode.EN) -> I18nAdapter:
    """
    Get an internationalization adapter for the specified language.
    
    Args:
        language_code: Language code
        
    Returns:
        I18nAdapter instance
    """
    return I18nAdapter(language_code)
