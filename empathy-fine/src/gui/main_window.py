"""
Main Window for EmpathyFine
PyQt6 application with draggable panels and modern UI

This module implements the main application window for EmpathyFine.
It provides a modern GUI with multiple panels, tabs, and a comprehensive
menu system. The window supports themes, project management, and
coordinates all the different components of the application.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QToolBar, QStatusBar, QDockWidget,
    QMenuBar, QMenu, QMessageBox, QLabel, QPushButton, QTextEdit,
    QTreeWidget, QTreeWidgetItem, QDialog, QDialogButtonBox,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QGroupBox, QFormLayout, QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, QSettings, QTimer, pyqtSignal, QThread, QSize, QDateTime
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QFont, QPalette, QColor

# Import custom modules
from ..core.project_manager import ProjectManager, ProjectConfig
from .panels.conversation_simulator import ConversationSimulator
from .panels.dataset_hub import DatasetHub
from .panels.training_panel import TrainingPanel
from .panels.evaluation_panel import EvaluationPanel
from .panels.visualization_panel import VisualizationPanel
from .dialogs.project_wizard import ProjectWizard
from .utils.theme_manager import ThemeManager

# Set up module logger
logger = logging.getLogger(__name__)


class EmpathyFineMainWindow(QMainWindow):
    """
    Main application window for EmpathyFine.
    
    This class manages the entire application UI, including:
    - Project management (create, open, save, delete)
    - Panel coordination (conversation, dataset, training, etc.)
    - Theme management
    - Menu and toolbar actions
    - Status updates and logging
    
    The window uses a three-panel layout:
    - Left: Project explorer
    - Center: Main workspace with tabs
    - Right: Properties and preview
    
    Signals:
        project_changed: Emitted when a new project is loaded
        training_started: Emitted when training begins
        training_stopped: Emitted when training ends
    """
    
    # Custom signals for inter-component communication
    project_changed = pyqtSignal(ProjectConfig)  # Emitted with new project config
    training_started = pyqtSignal()  # Emitted when training starts
    training_stopped = pyqtSignal()  # Emitted when training stops
    
    def __init__(self):
        """
        Initialize the main window.
        
        Sets up the project manager, theme manager, and application settings.
        Creates the UI components and restores the previous window state.
        """
        super().__init__()
        
        # Initialize core components
        self.project_manager = ProjectManager()  # Handles project operations
        self.theme_manager = ThemeManager()  # Manages application themes
        self.settings = QSettings("EmpathyFine", "MainWindow")  # Persistent settings
        
        # Application state
        self.current_project: Optional[ProjectConfig] = None  # Currently loaded project
        self.is_training = False  # Training status flag
        
        # Setup UI components
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_docks()
        
        # Apply saved theme
        self.theme_manager.apply_theme(self)
        
        # Restore window geometry and state from previous session
        self.restore_state()
        
        # Show welcome message in preview panel
        self.show_welcome()
        
    def setup_ui(self):
        """
        Setup the main UI layout.
        
        Creates a three-panel layout using QSplitter:
        - Left panel: Project explorer and quick actions
        - Center panel: Main workspace with tabbed interface
        - Right panel: Properties and live preview
        
        The panels are resizable and maintain their proportions.
        """
        self.setWindowTitle("EmpathyFine - Empathy-Focused LLM Training Studio")
        self.setGeometry(100, 100, 1400, 900)  # Default window size
        self.setMinimumSize(1200, 700)  # Minimum window size
        
        # Central widget with main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for cleaner look
        
        # Create main splitter for resizable panels
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Left panel - Project tree and quick actions
        self.left_panel = self.create_left_panel()
        self.main_splitter.addWidget(self.left_panel)
        
        # Center panel - Main workspace with tabs
        self.center_panel = self.create_center_panel()
        self.main_splitter.addWidget(self.center_panel)
        
        # Right panel - Properties and live preview
        self.right_panel = self.create_right_panel()
        self.main_splitter.addWidget(self.right_panel)
        
        # Set initial splitter sizes (pixels)
        self.main_splitter.setSizes([250, 900, 250])
        
        # Configure stretch factors (0 = fixed size, 1 = stretchable)
        self.main_splitter.setStretchFactor(0, 0)  # Left panel fixed
        self.main_splitter.setStretchFactor(1, 1)  # Center panel stretches
        self.main_splitter.setStretchFactor(2, 0)  # Right panel fixed
        
    def create_left_panel(self) -> QWidget:
        """
        Create the left panel with project tree.
        
        The left panel contains:
        - Project Explorer label
        - Tree widget showing all available projects
        - Quick action buttons (New Project, Open Project)
        
        Returns:
            QWidget: The configured left panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Project label with bold font
        label = QLabel("Project Explorer")
        label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(label)
        
        # Project tree widget
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabel("Projects")
        # Connect double-click to open project
        self.project_tree.itemDoubleClicked.connect(self.on_project_item_clicked)
        layout.addWidget(self.project_tree)
        
        # Quick actions section
        quick_actions = QWidget()
        actions_layout = QVBoxLayout(quick_actions)
        
        # New project button
        new_project_btn = QPushButton("New Project")
        new_project_btn.clicked.connect(self.new_project)
        actions_layout.addWidget(new_project_btn)
        
        # Open project button
        open_project_btn = QPushButton("Open Project")
        open_project_btn.clicked.connect(self.open_project)
        actions_layout.addWidget(open_project_btn)
        
        layout.addWidget(quick_actions)
        
        # Refresh project list on startup
        self.refresh_project_tree()
        
        return panel
        
    def create_center_panel(self) -> QWidget:
        """
        Create the center panel with main tabs.
        
        The center panel contains the main workspace with tabs:
        - Conversation Simulator: Test model responses
        - Dataset Hub: Manage training datasets
        - Training: Configure and monitor training
        - Evaluation: Evaluate model performance
        - Visualization: View training metrics
        
        Returns:
            QWidget: The configured center panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget for main functionality
        self.main_tabs = QTabWidget()
        self.main_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.main_tabs.setMovable(True)  # Allow tab reordering
        layout.addWidget(self.main_tabs)
        
        # Add tabs for each major component
        # Conversation Simulator - Real-time chat testing
        self.conversation_tab = ConversationSimulator()
        self.main_tabs.addTab(self.conversation_tab, "💬 Conversation Simulator")
        
        # Dataset Hub - Dataset management and validation
        self.dataset_tab = DatasetHub()
        self.main_tabs.addTab(self.dataset_tab, "📊 Dataset Hub")
        
        # Training Panel - Model training configuration
        self.training_tab = TrainingPanel()
        self.main_tabs.addTab(self.training_tab, "🚀 Training")
        
        # Evaluation Panel - Model evaluation metrics
        self.evaluation_tab = EvaluationPanel()
        self.main_tabs.addTab(self.evaluation_tab, "📈 Evaluation")
        
        # Visualization Panel - Metrics and charts
        self.visualization_tab = VisualizationPanel()
        self.main_tabs.addTab(self.visualization_tab, "📊 Visualization")
        
        # Connect training panel signals to main window handlers
        self.training_tab.training_started.connect(self.on_training_started)
        self.training_tab.training_stopped.connect(self.on_training_stopped)
        
        return panel
        
    def create_right_panel(self) -> QWidget:
        """
        Create the right panel with properties and preview.
        
        The right panel contains:
        - Properties section: Shows current project/selection details
        - Live preview section: Shows real-time updates and previews
        
        Returns:
            QWidget: The configured right panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Properties section
        props_label = QLabel("Properties")
        props_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(props_label)
        
        # Properties display (read-only text)
        self.properties_widget = QTextEdit()
        self.properties_widget.setReadOnly(True)
        self.properties_widget.setMaximumHeight(200)
        layout.addWidget(self.properties_widget)
        
        # Live preview section
        preview_label = QLabel("Live Preview")
        preview_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(preview_label)
        
        # Preview display (supports HTML)
        self.preview_widget = QTextEdit()
        self.preview_widget.setReadOnly(True)
        layout.addWidget(self.preview_widget)
        
        return panel
        
    def setup_menus(self):
        """
        Setup application menus.
        
        Creates the complete menu bar with:
        - File menu: Project operations, import/export
        - Edit menu: Undo/redo, preferences
        - View menu: UI visibility toggles, themes
        - Tools menu: Dataset validator, bias scanner
        - Help menu: Documentation, about dialog
        
        All menu items are connected to their respective handler methods.
        """
        menubar = self.menuBar()
        
        # File menu - Project and file operations
        file_menu = menubar.addMenu("&File")
        
        # New project action with standard shortcut
        new_action = QAction("&New Project", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        # Open project action
        open_action = QAction("&Open Project", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        # Save project action
        save_action = QAction("&Save Project", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Import dataset action
        import_action = QAction("&Import Dataset", self)
        import_action.triggered.connect(self.import_dataset)
        file_menu.addAction(import_action)
        
        # Export model action
        export_action = QAction("&Export Model", self)
        export_action.triggered.connect(self.export_model)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit application
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu - Editing and preferences
        edit_menu = menubar.addMenu("&Edit")
        
        # Undo action (placeholder - not implemented)
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(undo_action)
        
        # Redo action (placeholder - not implemented)
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # Preferences dialog
        preferences_action = QAction("&Preferences", self)
        preferences_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(preferences_action)
        
        # View menu - UI customization
        view_menu = menubar.addMenu("&View")
        
        # Simple/Advanced view toggle
        simple_view_action = QAction("&Simple View", self)
        simple_view_action.setCheckable(True)
        simple_view_action.triggered.connect(self.toggle_view_mode)
        view_menu.addAction(simple_view_action)
        
        view_menu.addSeparator()
        
        # Add dock visibility toggles (added dynamically)
        for dock in self.findChildren(QDockWidget):
            action = dock.toggleViewAction()
            view_menu.addAction(action)
            
        # Tools menu - Additional tools and utilities
        tools_menu = menubar.addMenu("&Tools")
        
        # Dataset validator tool
        dataset_validator_action = QAction("&Dataset Validator", self)
        dataset_validator_action.triggered.connect(self.show_dataset_validator)
        tools_menu.addAction(dataset_validator_action)
        
        # Bias scanner tool
        bias_scanner_action = QAction("&Bias Scanner", self)
        bias_scanner_action.triggered.connect(self.show_bias_scanner)
        tools_menu.addAction(bias_scanner_action)
        
        tools_menu.addSeparator()
        
        # Theme submenu
        theme_menu = tools_menu.addMenu("&Theme")
        
        # Add available themes
        for theme_name in ["Light", "Dark", "Blue", "Custom"]:
            theme_action = QAction(theme_name, self)
            theme_action.setCheckable(True)
            # Lambda captures theme_name for each action
            theme_action.triggered.connect(lambda checked, name=theme_name: self.change_theme(name))
            theme_menu.addAction(theme_action)
            
        # Help menu - Documentation and support
        help_menu = menubar.addMenu("&Help")
        
        # Documentation link
        documentation_action = QAction("&Documentation", self)
        documentation_action.triggered.connect(self.show_documentation)
        help_menu.addAction(documentation_action)
        
        help_menu.addSeparator()
        
        # About dialog
        about_action = QAction("&About EmpathyFine", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_toolbar(self):
        """Setup application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(True)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # New project
        new_action = QAction("New", self)
        new_action.setToolTip("Create new project")
        toolbar.addAction(new_action)
        
        # Open project
        open_action = QAction("Open", self)
        open_action.setToolTip("Open existing project")
        toolbar.addAction(open_action)
        
        # Save project
        save_action = QAction("Save", self)
        save_action.setToolTip("Save current project")
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Training controls
        self.start_training_action = QAction("Start Training", self)
        self.start_training_action.setToolTip("Start model training")
        self.start_training_action.triggered.connect(self.start_training)
        toolbar.addAction(self.start_training_action)
        
        self.stop_training_action = QAction("Stop Training", self)
        self.stop_training_action.setToolTip("Stop model training")
        self.stop_training_action.setEnabled(False)
        self.stop_training_action.triggered.connect(self.stop_training)
        toolbar.addAction(self.stop_training_action)
        
        toolbar.addSeparator()
        
        # Quick access
        evaluate_action = QAction("Evaluate", self)
        evaluate_action.setToolTip("Run evaluation")
        toolbar.addAction(evaluate_action)
        
        export_action = QAction("Export", self)
        export_action.setToolTip("Export model")
        toolbar.addAction(export_action)
        
    def setup_statusbar(self):
        """Setup application status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Project status
        self.project_status = QLabel("No project loaded")
        self.status_bar.addWidget(self.project_status)
        
        # Training status
        self.training_status = QLabel("Ready")
        self.status_bar.addWidget(self.training_status)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # GPU status
        self.gpu_status = QLabel("GPU: Checking...")
        self.status_bar.addPermanentWidget(self.gpu_status)
        
        # Check GPU availability
        self.check_gpu_status()
        
    def setup_docks(self):
        """Setup dockable panels"""
        # Console dock
        console_dock = QDockWidget("Console", self)
        console_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        
        self.console_widget = QTextEdit()
        self.console_widget.setReadOnly(True)
        self.console_widget.setMaximumHeight(150)
        console_dock.setWidget(self.console_widget)
        
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, console_dock)
        
        # Metrics dock
        metrics_dock = QDockWidget("Live Metrics", self)
        metrics_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        
        self.metrics_widget = QTextEdit()
        self.metrics_widget.setReadOnly(True)
        metrics_dock.setWidget(self.metrics_widget)
        
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, metrics_dock)
        
    def show_welcome(self):
        """Show welcome screen"""
        welcome_text = """
        <h1>Welcome to EmpathyFine</h1>
        <p>State-of-the-art GUI for training empathy-focused language models.</p>
        
        <h3>Getting Started:</h3>
        <ul>
            <li>Create a new project or open an existing one</li>
            <li>Import your empathy-focused dataset</li>
            <li>Configure training parameters</li>
            <li>Start training and monitor progress</li>
            <li>Evaluate model empathy and bias</li>
        </ul>
        
        <p>Visit the <a href="#">documentation</a> for detailed guides.</p>
        """
        
        self.preview_widget.setHtml(welcome_text)
        
    def refresh_project_tree(self):
        """Refresh the project tree with available projects"""
        self.project_tree.clear()
        
        projects = self.project_manager.list_projects()
        for project_name in projects:
            item = QTreeWidgetItem([project_name])
            self.project_tree.addTopLevelItem(item)
            
    def new_project(self):
        """Create a new project"""
        wizard = ProjectWizard(self)
        if wizard.exec() == QDialog.DialogCode.Accepted:
            config = wizard.get_project_config()
            if self.project_manager.create_project(config):
                self.current_project = config
                self.project_changed.emit(config)
                self.refresh_project_tree()
                self.update_project_status()
                self.log_message(f"Created new project: {config.name}")
            else:
                QMessageBox.critical(self, "Error", "Failed to create project")
                
    def open_project(self):
        """Open an existing project"""
        from .dialogs.project_selector import ProjectSelector
        
        dialog = ProjectSelector(self.project_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            project_name = dialog.selected_project
            config = self.project_manager.load_project(project_name)
            if config:
                self.current_project = config
                self.project_changed.emit(config)
                self.update_project_status()
                self.log_message(f"Opened project: {project_name}")
            else:
                QMessageBox.critical(self, "Error", "Failed to open project")
                
    def save_project(self):
        """Save current project"""
        if self.current_project:
            if self.project_manager.save_project():
                self.log_message("Project saved successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to save project")
        else:
            QMessageBox.information(self, "Info", "No project to save")
            
    def import_dataset(self):
        """Import a dataset"""
        if not self.current_project:
            QMessageBox.information(self, "Info", "Please open a project first")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Dataset", "", 
            "Dataset Files (*.jsonl *.csv);;All Files (*.*)"
        )
        
        if file_path:
            # Pass to dataset hub
            self.dataset_tab.import_dataset(file_path)
            
    def export_model(self):
        """Export trained model"""
        if not self.current_project:
            QMessageBox.information(self, "Info", "No project loaded")
            return
            
        # TODO: Implement model export
        self.log_message("Model export not yet implemented")
        
    def show_preferences(self):
        """Show preferences dialog"""
        from .dialogs.preferences_dialog import PreferencesDialog
        
        dialog = PreferencesDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Apply preferences
            self.log_message("Preferences updated")
            
    def toggle_view_mode(self, simple: bool):
        """Toggle between simple and advanced view"""
        # Hide/show advanced panels
        if simple:
            self.right_panel.hide()
            for dock in self.findChildren(QDockWidget):
                dock.hide()
        else:
            self.right_panel.show()
            for dock in self.findChildren(QDockWidget):
                dock.show()
                
        self.log_message(f"Switched to {'simple' if simple else 'advanced'} view")
        
    def change_theme(self, theme_name: str):
        """Change application theme"""
        self.theme_manager.set_theme(theme_name)
        self.theme_manager.apply_theme(self)
        self.log_message(f"Applied {theme_name} theme")
        
    def show_dataset_validator(self):
        """Show dataset validator tool"""
        from .dialogs.dataset_validator import DatasetValidator
        
        dialog = DatasetValidator(self)
        dialog.exec()
        
    def show_bias_scanner(self):
        """Show bias scanner tool"""
        from .dialogs.bias_scanner import BiasScanner
        
        dialog = BiasScanner(self)
        dialog.exec()
        
    def show_documentation(self):
        """Show documentation"""
        import webbrowser
        webbrowser.open("https://empathyfine.docs.ai")
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About EmpathyFine",
            """<h2>EmpathyFine v1.0.0</h2>
            <p>State-of-the-art GUI for training empathy-focused language models.</p>
            <p>Created with ❤️ for the AI community.</p>
            <p>© 2024 EmpathyFine Team</p>"""
        )
        
    def start_training(self):
        """Start model training"""
        if not self.current_project:
            QMessageBox.information(self, "Info", "Please open a project first")
            return
            
        self.is_training = True
        self.start_training_action.setEnabled(False)
        self.stop_training_action.setEnabled(True)
        self.training_status.setText("Training...")
        self.progress_bar.setVisible(True)
        
        # Notify training panel
        self.training_tab.start_training()
        self.training_started.emit()
        
        self.log_message("Training started")
        
    def stop_training(self):
        """Stop model training"""
        self.is_training = False
        self.start_training_action.setEnabled(True)
        self.stop_training_action.setEnabled(False)
        self.training_status.setText("Ready")
        self.progress_bar.setVisible(False)
        
        # Notify training panel
        self.training_tab.stop_training()
        self.training_stopped.emit()
        
        self.log_message("Training stopped")
        
    def on_training_started(self):
        """Handle training started signal"""
        self.start_training()
        
    def on_training_stopped(self):
        """Handle training stopped signal"""
        self.stop_training()
        
    def on_project_item_clicked(self, item, column):
        """Handle project tree item click"""
        project_name = item.text(0)
        self.open_project_by_name(project_name)
        
    def open_project_by_name(self, project_name: str):
        """Open a project by name"""
        config = self.project_manager.load_project(project_name)
        if config:
            self.current_project = config
            self.project_changed.emit(config)
            self.update_project_status()
            self.log_message(f"Opened project: {project_name}")
            
    def update_project_status(self):
        """Update project status in UI"""
        if self.current_project:
            self.project_status.setText(f"Project: {self.current_project.name}")
            self.setWindowTitle(f"EmpathyFine - {self.current_project.name}")
            
            # Update properties
            props_text = f"""
            <b>Project:</b> {self.current_project.name}<br>
            <b>Model:</b> {self.current_project.base_model}<br>
            <b>Framework:</b> {self.current_project.framework}<br>
            <b>Created:</b> {self.current_project.created_at[:10]}<br>
            """
            self.properties_widget.setHtml(props_text)
        else:
            self.project_status.setText("No project loaded")
            self.setWindowTitle("EmpathyFine - Empathy-Focused LLM Training Studio")
            
    def check_gpu_status(self):
        """Check GPU availability"""
        try:
            import torch
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                self.gpu_status.setText(f"GPU: {device_name} ({memory:.1f}GB)")
            else:
                self.gpu_status.setText("GPU: Not available")
        except:
            self.gpu_status.setText("GPU: Unknown")
            
    def log_message(self, message: str):
        """Log message to console"""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.console_widget.append(f"[{timestamp}] {message}")
        
    def update_metrics(self, metrics: dict):
        """Update live metrics display"""
        text = ""
        for key, value in metrics.items():
            text += f"<b>{key}:</b> {value}<br>"
        self.metrics_widget.setHtml(text)
        
    def restore_state(self):
        """Restore window state from settings"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
            
    def closeEvent(self, event):
        """Handle window close event"""
        # Save state
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        
        # Check for unsaved changes
        if self.current_project and self.is_training:
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "Training is in progress. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
                
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("EmpathyFine")
    app.setOrganizationName("EmpathyFine")
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = EmpathyFineMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 