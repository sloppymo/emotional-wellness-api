"""
MOSS Processor Module

This module provides the core processing capabilities for the MOSS system,
handling the orchestration of crisis detection and intervention workflows.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from functools import lru_cache

from .crisis_classifier import CrisisClassifier, RiskAssessment, CrisisContext
from .prompt_templates import GeneratedPrompt, generate_crisis_prompt
from structured_logging import get_logger

logger = get_logger(__name__)

class MossProcessor:
    """
    Core processor for the MOSS system that orchestrates crisis detection
    and intervention workflows.
    """
    
    def __init__(self):
        """Initialize the MOSS processor."""
        self._classifier = CrisisClassifier()
        self._logger = get_logger(f"{__name__}.MossProcessor")
        self._logger.info("MossProcessor initialized")
    
    async def process_input(
        self,
        text: str,
        user_id: Optional[str] = None,
        context: Optional[CrisisContext] = None
    ) -> Dict[str, Any]:
        """
        Process user input through the MOSS system.
        
        Args:
            text: The input text to process
            user_id: Optional user identifier
            context: Optional crisis context
            
        Returns:
            Dict containing assessment and generated prompt
        """
        # Perform risk assessment
        assessment = await self._classifier.assess_crisis_risk(
            text=text,
            user_id=user_id,
            context=context
        )
        
        # Generate appropriate prompt based on assessment
        prompt = await generate_crisis_prompt(assessment)
        
        return {
            "assessment": assessment,
            "prompt": prompt
        }

@lru_cache(maxsize=1)
def get_moss_processor() -> MossProcessor:
    """Get or create the singleton MOSS processor instance."""
    return MossProcessor()

# Update crisis_classifier.py to remove circular import
import os

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
classifier_path = os.path.join(current_dir, "crisis_classifier.py")

with open(classifier_path, "r") as f:
    content = f.read()

# Remove the MossProcessor import
content = content.replace(
    "from ..moss import MossProcessor, get_moss_processor",
    "# MossProcessor moved to processor.py"
)

with open(classifier_path, "w") as f:
    f.write(content)

# Update __init__.py to expose MossProcessor
with open("src/symbolic/moss/__init__.py", "r") as f:
    content = f.read()

# Add MossProcessor to exports
content = content.replace(
    "__all__ = [",
    """__all__ = [
    # Core processor
    "MossProcessor",
    "get_moss_processor",
    
    # Crisis classifier"""
)

with open("src/symbolic/moss/__init__.py", "w") as f:
    f.write(content) 