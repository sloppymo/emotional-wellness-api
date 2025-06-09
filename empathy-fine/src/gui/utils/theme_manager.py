"""
Theme Manager
Manages application themes and styling
"""

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QPalette, QColor


class ThemeManager:
    """Manages application themes"""
    
    def __init__(self):
        self.current_theme = "Light"
        self.themes = {
            "Light": self.light_theme,
            "Dark": self.dark_theme,
            "Blue": self.blue_theme,
            "Custom": self.custom_theme
        }
        
    def apply_theme(self, widget: QWidget, theme_name: str = None):
        """Apply theme to widget"""
        if theme_name:
            self.current_theme = theme_name
            
        theme_func = self.themes.get(self.current_theme, self.light_theme)
        theme_func(widget)
        
    def set_theme(self, theme_name: str):
        """Set current theme"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            
    def light_theme(self, widget: QWidget):
        """Apply light theme"""
        # Standard light theme - PyQt default
        widget.setStyleSheet("")
        
    def dark_theme(self, widget: QWidget):
        """Apply dark theme"""
        dark_stylesheet = """
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QGroupBox {
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QPushButton {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            padding: 5px 15px;
            border-radius: 3px;
        }
        
        QPushButton:hover {
            background-color: #484848;
        }
        
        QPushButton:pressed {
            background-color: #222222;
        }
        
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            padding: 3px;
            border-radius: 3px;
        }
        
        QComboBox {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            padding: 3px;
            border-radius: 3px;
        }
        
        QTableWidget {
            background-color: #2b2b2b;
            alternate-background-color: #3c3c3c;
            gridline-color: #555555;
        }
        
        QHeaderView::section {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            padding: 3px;
        }
        
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #2b2b2b;
        }
        
        QTabBar::tab {
            background-color: #3c3c3c;
            padding: 5px 10px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #484848;
        }
        """
        
        widget.setStyleSheet(dark_stylesheet)
        
    def blue_theme(self, widget: QWidget):
        """Apply blue theme"""
        blue_stylesheet = """
        QWidget {
            background-color: #f0f4f8;
            color: #2d3748;
        }
        
        QGroupBox {
            border: 1px solid #cbd5e0;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: white;
        }
        
        QPushButton {
            background-color: #4299e1;
            color: white;
            border: none;
            padding: 5px 15px;
            border-radius: 3px;
        }
        
        QPushButton:hover {
            background-color: #3182ce;
        }
        
        QPushButton:pressed {
            background-color: #2c5282;
        }
        
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
            background-color: white;
            border: 1px solid #e2e8f0;
            padding: 3px;
            border-radius: 3px;
        }
        
        QComboBox {
            background-color: white;
            border: 1px solid #e2e8f0;
            padding: 3px;
            border-radius: 3px;
        }
        
        QTableWidget {
            background-color: white;
            alternate-background-color: #f7fafc;
            gridline-color: #e2e8f0;
        }
        
        QHeaderView::section {
            background-color: #edf2f7;
            border: 1px solid #e2e8f0;
            padding: 3px;
        }
        
        QTabWidget::pane {
            border: 1px solid #e2e8f0;
            background-color: white;
        }
        
        QTabBar::tab {
            background-color: #edf2f7;
            padding: 5px 10px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid #4299e1;
        }
        """
        
        widget.setStyleSheet(blue_stylesheet)
        
    def custom_theme(self, widget: QWidget):
        """Apply custom theme (placeholder)"""
        # Users can define their own theme here
        self.light_theme(widget) 