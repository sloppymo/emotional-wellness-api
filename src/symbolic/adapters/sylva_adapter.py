"""
SYLVA adapter for integrating CANOPY with other subsystems.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from src.utils.structured_logging import get_logger
from src.symbolic.canopy import CanopyProcessor
from src.symbolic.canopy.metaphor_extraction import SymbolicMapping

logger = get_logger(__name__)

@dataclass
class SylvaContext:
    """Context for SYLVA processing."""
    user_id: str
    session_id: str
    timestamp: datetime
    processing_flags: Dict[str, Any]

@dataclass
class ProcessingResult:
    """Result of SYLVA processing."""
    success: bool
    output: Optional[SymbolicMapping] = None
    error: Optional[str] = None
    processing_time: float = 0.0

class SylvaAdapter:
    """Adapter for integrating CANOPY with SYLVA framework."""
    
    async def process(
        self,
        processor: CanopyProcessor,
        context: SylvaContext,
        input_text: str,
        biomarkers: Optional[Dict[str, float]] = None
    ) -> ProcessingResult:
        """Process input through CANOPY with SYLVA integration."""
        start_time = datetime.utcnow()
        
        try:
            if not input_text:
                raise ValueError("Input text cannot be empty")
            
            # Convert SYLVA context to CANOPY context
            canopy_context = self._convert_context(context)
            
            # Process through CANOPY
            result = await processor.process(
                text=input_text,
                user_id=context.user_id,
                biomarkers=biomarkers,
                context=canopy_context
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                "Successfully processed through SYLVA",
                user_id=context.user_id,
                session_id=context.session_id,
                processing_time=processing_time
            )
            
            return ProcessingResult(
                success=True,
                output=result,
                processing_time=processing_time
            )
        
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(
                "Failed to process through SYLVA",
                error=str(e),
                user_id=context.user_id,
                session_id=context.session_id,
                processing_time=processing_time
            )
            
            return ProcessingResult(
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    def _convert_context(self, context: SylvaContext) -> Dict[str, Any]:
        """Convert SYLVA context to CANOPY context."""
        return {
            "session_id": context.session_id,
            "timestamp": context.timestamp.isoformat(),
            "cultural_context": context.processing_flags.get("cultural_context"),
            "enable_cultural_adaptation": context.processing_flags.get(
                "enable_cultural_adaptation",
                True
            )
        } 