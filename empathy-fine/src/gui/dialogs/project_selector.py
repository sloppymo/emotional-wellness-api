"""
Project Selector Dialog
Select existing projects to open
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
    QDialogButtonBox, QLabel
)
from PyQt6.QtCore import Qt

from ...core.project_manager import ProjectManager


class ProjectSelector(QDialog):
    """Dialog for selecting existing projects"""
    
    def __init__(self, project_manager: ProjectManager, parent=None):
        super().__init__(parent)
        
        self.project_manager = project_manager
        self.selected_project = None
        
        self.setWindowTitle("Open Project")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        self.setup_ui()
        self.load_projects()
        
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Label
        label = QLabel("Select a project to open:")
        layout.addWidget(label)
        
        # Project list
        self.project_list = QListWidget()
        self.project_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.project_list)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def load_projects(self):
        """Load available projects"""
        projects = self.project_manager.list_projects()
        
        for project_name in projects:
            item = QListWidgetItem(project_name)
            self.project_list.addItem(item)
            
        if projects:
            self.project_list.setCurrentRow(0)
            
    def accept(self):
        """Accept the selection"""
        current_item = self.project_list.currentItem()
        if current_item:
            self.selected_project = current_item.text()
            super().accept() 