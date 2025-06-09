"""
EmpathyFine - Empathy-Focused LLM Training Studio

A state-of-the-art GUI application for training empathy-focused language models
with multi-framework support, advanced evaluation metrics, and bias mitigation tools.
"""

# Import version information
from .version import (
    __version__,
    __version_info__,
    __release_date__,
    __app_name__,
    __app_full_name__,
    __description__,
    __author__,
    __author_email__,
    __license__,
    __url__,
    __documentation_url__,
    __issues_url__,
    __status__,
    __python_requires__,
    get_version_string,
    get_version_info
)

# Make key items available at package level
__all__ = [
    "__version__",
    "__app_name__",
    "__author__",
    "get_version_string",
    "get_version_info"
] 