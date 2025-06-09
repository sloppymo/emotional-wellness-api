"""
Project Wizard Dialog
Create new EmpathyFine projects
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QPushButton, QDialogButtonBox,
    QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt

from ...core.project_manager import ProjectConfig


class ProjectWizard(QDialog):
    """Wizard dialog for creating new projects"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("New Project Wizard")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Project info
        info_group = QGroupBox("Project Information")
        info_layout = QFormLayout(info_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("my-empathy-model")
        info_layout.addRow("Project Name:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("A brief description of your project...")
        self.description_edit.setMaximumHeight(80)
        info_layout.addRow("Description:", self.description_edit)
        
        layout.addWidget(info_group)
        
        # Model settings
        model_group = QGroupBox("Model Settings")
        model_layout = QFormLayout(model_group)
        
        self.base_model_combo = QComboBox()
        self.base_model_combo.addItems([
            "microsoft/DialoGPT-medium",
            "facebook/blenderbot-400M-distill",
            "google/flan-t5-base",
            "EleutherAI/gpt-neo-1.3B"
        ])
        model_layout.addRow("Base Model:", self.base_model_combo)
        
        self.framework_combo = QComboBox()
        self.framework_combo.addItems(["huggingface", "openai"])
        model_layout.addRow("Framework:", self.framework_combo)
        
        layout.addWidget(model_group)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_project_config(self) -> ProjectConfig:
        """Get the project configuration"""
        return ProjectConfig(
            name=self.name_edit.text() or "untitled-project",
            description=self.description_edit.toPlainText(),
            base_model=self.base_model_combo.currentText(),
            framework=self.framework_combo.currentText()
        ) 