#!/usr/bin/env python3
"""
Test imports for EmpathyFine
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing imports...")

try:
    from src.core.project_manager import ProjectManager, ProjectConfig
    print("✓ Core modules imported successfully")
except ImportError as e:
    print(f"✗ Failed to import core modules: {e}")

try:
    from src.gui.main_window import EmpathyFineMainWindow
    print("✓ Main window imported successfully")
except ImportError as e:
    print(f"✗ Failed to import main window: {e}")

try:
    from src.gui.panels import (
        ConversationSimulator,
        DatasetHub,
        TrainingPanel,
        EvaluationPanel,
        VisualizationPanel
    )
    print("✓ All panels imported successfully")
except ImportError as e:
    print(f"✗ Failed to import panels: {e}")

try:
    from src.gui.dialogs import ProjectWizard
    print("✓ Dialogs imported successfully")
except ImportError as e:
    print(f"✗ Failed to import dialogs: {e}")

try:
    from src.gui.utils import ThemeManager
    print("✓ Utils imported successfully")
except ImportError as e:
    print(f"✗ Failed to import utils: {e}")

print("\nAll imports completed!") 