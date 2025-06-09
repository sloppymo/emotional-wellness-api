import pytest
from PyQt6.QtWidgets import QApplication

def test_simple_qt(qtbot):
    """Simple test to verify pytest-qt is working."""
    assert True

def test_qapplication(qapp):
    """Test that QApplication fixture works."""
    assert isinstance(qapp, QApplication) 