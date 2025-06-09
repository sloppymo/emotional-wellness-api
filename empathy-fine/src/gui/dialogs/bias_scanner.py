"""
Bias Scanner Dialog
Scan datasets and model outputs for potential biases

This dialog provides tools to detect and analyze biases in:
- Training datasets
- Model responses
- Evaluation results

The scanner checks for biases across protected categories including
gender, race, age, religion, and socioeconomic status.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QPushButton,
    QDialogButtonBox, QLabel, QProgressBar, QComboBox,
    QCheckBox, QGroupBox, QHBoxLayout
)
from PyQt6.QtCore import Qt


class BiasScanner(QDialog):
    """
    Dialog for scanning and analyzing biases.
    
    Provides functionality to:
    - Select bias categories to scan
    - Choose scanning depth (quick/thorough)
    - Display detailed bias analysis results
    - Export bias reports
    """
    
    def __init__(self, parent=None):
        """
        Initialize the bias scanner dialog.
        
        Args:
            parent: Parent widget (typically the main window)
        """
        super().__init__(parent)
        
        self.setWindowTitle("Bias Scanner")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel(
            "Scan your dataset or model outputs for potential biases "
            "across protected categories."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Bias categories selection
        categories_group = QGroupBox("Bias Categories to Scan")
        categories_layout = QVBoxLayout(categories_group)
        
        # Create checkboxes for each bias category
        self.bias_checkboxes = {}
        bias_categories = [
            ("Gender", "gender", True),
            ("Race/Ethnicity", "race", True),
            ("Age", "age", True),
            ("Religion", "religion", True),
            ("Socioeconomic Status", "socioeconomic", True),
            ("Disability", "disability", False),
            ("Sexual Orientation", "orientation", False)
        ]
        
        for display_name, key, default_checked in bias_categories:
            checkbox = QCheckBox(display_name)
            checkbox.setChecked(default_checked)
            self.bias_checkboxes[key] = checkbox
            categories_layout.addWidget(checkbox)
            
        layout.addWidget(categories_group)
        
        # Scan settings
        settings_layout = QHBoxLayout()
        
        settings_layout.addWidget(QLabel("Scan Mode:"))
        self.scan_mode_combo = QComboBox()
        self.scan_mode_combo.addItems(["Quick Scan", "Thorough Analysis", "Deep Inspection"])
        settings_layout.addWidget(self.scan_mode_combo)
        
        settings_layout.addStretch()
        
        layout.addLayout(settings_layout)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Bias scan results will appear here...")
        layout.addWidget(self.results_text)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        self.scan_btn = QPushButton("Run Bias Scan")
        self.scan_btn.clicked.connect(self.run_scan)
        button_layout.addWidget(self.scan_btn)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        button_layout.addWidget(buttons)
        
        layout.addLayout(button_layout)
        
    def run_scan(self):
        """
        Run the bias scan with selected settings.
        
        This is currently a placeholder that shows example results.
        In a real implementation, this would:
        1. Load the dataset or model outputs
        2. Apply bias detection algorithms
        3. Generate detailed analysis reports
        """
        # Get selected categories
        selected_categories = [
            name for name, checkbox in self.bias_checkboxes.items() 
            if checkbox.isChecked()
        ]
        
        # Get scan mode
        scan_mode = self.scan_mode_combo.currentText()
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(50)  # Mock progress
        
        # Generate mock results
        results = f"""Bias Scan Results
{'='*50}

Scan Mode: {scan_mode}
Categories Scanned: {', '.join(selected_categories)}

Summary:
--------
✗ Gender Bias Detected (Score: 0.73)
  - Male pronouns: 68%
  - Female pronouns: 32%
  - Gender-neutral: <1%
  
✓ Race/Ethnicity: Balanced (Score: 0.12)
  - No significant bias detected
  
⚠ Age Bias: Moderate (Score: 0.45)
  - Youth-oriented language: 43%
  - Age-neutral language: 57%
  
✓ Religion: Balanced (Score: 0.08)
  - No religious bias detected
  
✗ Socioeconomic Bias Detected (Score: 0.61)
  - Upper-class contexts: 48%
  - Middle-class contexts: 41%
  - Lower-class contexts: 11%

Recommendations:
---------------
1. Balance gender representation in training data
2. Include more diverse socioeconomic contexts
3. Review age-related language patterns

Detailed Analysis:
-----------------
[This would contain specific examples and statistics]
"""
        
        # Display results
        self.results_text.setText(results)
        
        # Hide progress bar
        self.progress_bar.setVisible(False) 