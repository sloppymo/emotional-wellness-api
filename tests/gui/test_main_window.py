import pytest
from PyQt6.QtWidgets import QApplication, QPushButton, QDialogButtonBox, QLineEdit, QTextEdit, QComboBox
from src.gui.main_window import EmpathyFineMainWindow

@pytest.fixture(scope="session")
def app(qapp):
    # qapp is a pytest-qt fixture that provides a QApplication
    return qapp

@pytest.fixture
def main_window(app):
    window = EmpathyFineMainWindow()
    window.show()
    yield window
    window.close()

def test_main_window_starts(main_window):
    """Test that the main window starts and is visible."""
    assert main_window.isVisible()
    assert main_window.windowTitle().startswith("EmpathyFine")

def test_tab_switching(main_window, qtbot):
    """Test that tabs can be switched without crashing."""
    tabs = main_window.main_tabs
    initial_index = tabs.currentIndex()
    # Switch to each tab and back
    for i in range(tabs.count()):
        tabs.setCurrentIndex(i)
        assert tabs.currentIndex() == i
    # Return to initial tab
    tabs.setCurrentIndex(initial_index)
    assert tabs.currentIndex() == initial_index

def test_theme_switching(main_window, qtbot):
    """Test that themes can be switched without crashing."""
    # Switch to each theme and check no crash
    for theme in ["Light", "Dark", "Blue"]:
        main_window.change_theme(theme)
        assert main_window.theme_manager.current_theme == theme

def test_create_new_project(main_window, qtbot):
    """Simulate creating a new project via the New Project button and wizard dialog."""
    # Find the 'New Project' button in the left panel
    new_btn = None
    for btn in main_window.left_panel.findChildren(QPushButton):
        if btn.text() == "New Project":
            new_btn = btn
            break
    assert new_btn is not None, "New Project button not found"

    # Click the button
    qtbot.mouseClick(new_btn, qtbot.MouseButton.LeftButton)

    # The ProjectWizard dialog should now be active
    wizard = None
    for widget in QApplication.topLevelWidgets():
        if widget.windowTitle() == "New Project Wizard":
            wizard = widget
            break
    assert wizard is not None, "ProjectWizard dialog did not appear"

    # Fill out the form
    name_edit = wizard.findChild(QLineEdit)
    desc_edit = wizard.findChild(QTextEdit)
    base_model_combo = wizard.findChild(QComboBox)
    framework_combo = wizard.findChild(QComboBox)

    assert name_edit is not None
    assert desc_edit is not None
    assert base_model_combo is not None
    assert framework_combo is not None

    qtbot.keyClicks(name_edit, "test-project")
    qtbot.keyClicks(desc_edit, "A test project for automated GUI testing.")
    base_model_combo.setCurrentIndex(1)  # Select second model
    framework_combo.setCurrentIndex(0)   # Select first framework

    # Click OK
    button_box = wizard.findChild(QDialogButtonBox)
    assert button_box is not None
    ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
    qtbot.mouseClick(ok_button, qtbot.MouseButton.LeftButton)

    # Wait for dialog to close
    qtbot.waitUntil(lambda: not wizard.isVisible(), timeout=2000)

    # Check that the project was created and is now current
    assert main_window.current_project is not None
    assert main_window.current_project.name == "test-project"
    assert "test-project" in main_window.project_status.text()

def test_dataset_hub_tab(main_window, qtbot):
    """Test that the Dataset Hub tab loads without crashing."""
    # Switch to Dataset Hub tab (index 1)
    main_window.main_tabs.setCurrentIndex(1)
    assert main_window.main_tabs.currentIndex() == 1
    
    # Check that the dataset hub panel is accessible
    dataset_tab = main_window.dataset_tab
    assert dataset_tab is not None

def test_training_panel_tab(main_window, qtbot):
    """Test that the Training Panel tab loads without crashing."""
    # Switch to Training Panel tab (index 2)
    main_window.main_tabs.setCurrentIndex(2)
    assert main_window.main_tabs.currentIndex() == 2
    
    # Check that the training panel is accessible
    training_tab = main_window.training_tab
    assert training_tab is not None

def test_conversation_simulator_tab(main_window, qtbot):
    """Test that the Conversation Simulator tab loads without crashing."""
    # Switch to Conversation Simulator tab (index 0)
    main_window.main_tabs.setCurrentIndex(0)
    assert main_window.main_tabs.currentIndex() == 0
    
    # Check that the conversation simulator is accessible
    conversation_tab = main_window.conversation_tab
    assert conversation_tab is not None 