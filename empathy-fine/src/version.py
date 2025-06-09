"""
Version information for EmpathyFine

This module centralizes all version-related information for the application.
"""

# Version info
__version__ = "0.1.0"
__version_info__ = (0, 1, 0)
__release_date__ = "2024-01-09"

# Application info
__app_name__ = "EmpathyFine"
__app_full_name__ = "EmpathyFine - Empathy-Focused LLM Training Studio"
__description__ = "State-of-the-art GUI for training empathy-focused language models"

# Author info
__author__ = "EmpathyFine Team"
__author_email__ = "team@empathyfine.ai"
__license__ = "MIT"

# Project URLs
__url__ = "https://github.com/empathyfine/empathy-fine"
__documentation_url__ = "https://empathyfine.docs.ai"
__issues_url__ = "https://github.com/empathyfine/empathy-fine/issues"

# Development status
__status__ = "Alpha"
__python_requires__ = ">=3.8"

def get_version_string() -> str:
    """Get the full version string with status."""
    return f"{__version__} ({__status__})"

def get_version_info() -> dict:
    """Get complete version information as a dictionary."""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "release_date": __release_date__,
        "app_name": __app_name__,
        "status": __status__,
        "python_requires": __python_requires__
    } 