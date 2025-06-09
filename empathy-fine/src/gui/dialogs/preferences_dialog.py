"""
Preferences Dialog
Application preferences and settings
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget,
    QFormLayout, QComboBox, QCheckBox, QSpinBox,
    QDialogButtonBox, QGroupBox
)
from PyQt6.QtCore import Qt


class PreferencesDialog(QDialog):
    """Dialog for application preferences"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Create tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # General tab
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "General")
        
        # Training tab
        training_tab = self.create_training_tab()
        tabs.addTab(training_tab, "Training")
        
        # Appearance tab
        appearance_tab = self.create_appearance_tab()
        tabs.addTab(appearance_tab, "Appearance")
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def create_general_tab(self) -> QWidget:
        """Create general preferences tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Workspace settings
        workspace_group = QGroupBox("Workspace")
        workspace_layout = QFormLayout(workspace_group)
        
        self.auto_save_check = QCheckBox("Auto-save projects")
        self.auto_save_check.setChecked(True)
        workspace_layout.addRow(self.auto_save_check)
        
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(1, 60)
        self.auto_save_interval.setValue(5)
        self.auto_save_interval.setSuffix(" minutes")
        workspace_layout.addRow("Auto-save interval:", self.auto_save_interval)
        
        layout.addWidget(workspace_group)
        
        # Logging settings
        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout(logging_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["Debug", "Info", "Warning", "Error"])
        self.log_level_combo.setCurrentText("Info")
        logging_layout.addRow("Log level:", self.log_level_combo)
        
        layout.addWidget(logging_group)
        
        layout.addStretch()
        return widget
        
    def create_training_tab(self) -> QWidget:
        """Create training preferences tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Default settings
        defaults_group = QGroupBox("Default Training Settings")
        defaults_layout = QFormLayout(defaults_group)
        
        self.default_epochs = QSpinBox()
        self.default_epochs.setRange(1, 100)
        self.default_epochs.setValue(3)
        defaults_layout.addRow("Default epochs:", self.default_epochs)
        
        self.default_batch_size = QSpinBox()
        self.default_batch_size.setRange(1, 128)
        self.default_batch_size.setValue(4)
        defaults_layout.addRow("Default batch size:", self.default_batch_size)
        
        layout.addWidget(defaults_group)
        
        # GPU settings
        gpu_group = QGroupBox("GPU Settings")
        gpu_layout = QFormLayout(gpu_group)
        
        self.use_gpu_check = QCheckBox("Use GPU if available")
        self.use_gpu_check.setChecked(True)
        gpu_layout.addRow(self.use_gpu_check)
        
        self.gpu_memory_fraction = QSpinBox()
        self.gpu_memory_fraction.setRange(10, 100)
        self.gpu_memory_fraction.setValue(90)
        self.gpu_memory_fraction.setSuffix("%")
        gpu_layout.addRow("GPU memory limit:", self.gpu_memory_fraction)
        
        layout.addWidget(gpu_group)
        
        layout.addStretch()
        return widget
        
    def create_appearance_tab(self) -> QWidget:
        """Create appearance preferences tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Theme settings
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Blue", "Custom"])
        theme_layout.addRow("Theme:", self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(10)
        theme_layout.addRow("Font size:", self.font_size_spin)
        
        layout.addWidget(theme_group)
        
        layout.addStretch()
        return widget 