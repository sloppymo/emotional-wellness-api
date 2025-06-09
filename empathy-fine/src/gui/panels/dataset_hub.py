"""
Dataset Hub Panel
Manage and validate empathy-focused datasets
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QLineEdit, QTextEdit, QGroupBox,
    QSplitter, QTreeWidget, QTreeWidgetItem, QCheckBox, QSpinBox,
    QProgressBar, QFileDialog, QMessageBox, QTabWidget, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QColor

import json
import jsonlines
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DatasetWorker(QThread):
    """Worker thread for dataset operations"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, operation: str, file_path: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.file_path = file_path
        self.kwargs = kwargs
        
    def run(self):
        """Execute dataset operation"""
        try:
            if self.operation == "load":
                self.load_dataset()
            elif self.operation == "validate":
                self.validate_dataset()
            elif self.operation == "augment":
                self.augment_dataset()
            else:
                self.error.emit(f"Unknown operation: {self.operation}")
        except Exception as e:
            self.error.emit(str(e))
            
    def load_dataset(self):
        """Load dataset from file"""
        self.status.emit("Loading dataset...")
        
        file_path = Path(self.file_path)
        examples = []
        
        if file_path.suffix == ".jsonl":
            with jsonlines.open(file_path) as reader:
                total = sum(1 for _ in jsonlines.open(file_path))
                reader = jsonlines.open(file_path)
                
                for i, obj in enumerate(reader):
                    examples.append(obj)
                    progress = int((i + 1) / total * 100)
                    self.progress.emit(progress)
                    
        elif file_path.suffix == ".csv":
            df = pd.read_csv(file_path)
            total = len(df)
            
            for i, row in df.iterrows():
                examples.append(row.to_dict())
                progress = int((i + 1) / total * 100)
                self.progress.emit(progress)
                
        self.finished.emit({
            "examples": examples,
            "count": len(examples),
            "file_path": str(file_path)
        })
        
    def validate_dataset(self):
        """Validate dataset for empathy requirements"""
        self.status.emit("Validating dataset...")
        
        # Load dataset
        with jsonlines.open(self.file_path) as reader:
            examples = list(reader)
            
        issues = []
        empathy_scores = []
        
        for i, example in enumerate(examples):
            progress = int((i + 1) / len(examples) * 100)
            self.progress.emit(progress)
            
            # Check required fields
            if "context" not in example or "response" not in example:
                issues.append(f"Example {i}: Missing required fields")
                continue
                
            # Check empathy indicators
            response = example.get("response", "").lower()
            empathy_keywords = ["understand", "feel", "support", "hear", "sorry"]
            keyword_count = sum(1 for kw in empathy_keywords if kw in response)
            
            if keyword_count == 0:
                issues.append(f"Example {i}: No empathy indicators found")
                
            empathy_scores.append(keyword_count / len(empathy_keywords))
            
        avg_empathy = sum(empathy_scores) / len(empathy_scores) if empathy_scores else 0
        
        self.finished.emit({
            "valid": len(issues) == 0,
            "issues": issues,
            "avg_empathy_score": avg_empathy,
            "total_examples": len(examples)
        })
        
    def augment_dataset(self):
        """Augment dataset with variations"""
        self.status.emit("Augmenting dataset...")
        
        # Placeholder for augmentation logic
        self.progress.emit(100)
        self.finished.emit({"augmented": True})


class DatasetHub(QWidget):
    """Dataset management hub for empathy-focused datasets"""
    
    # Signals
    dataset_loaded = pyqtSignal(str, int)  # path, count
    dataset_validated = pyqtSignal(bool, list)  # valid, issues
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # State
        self.current_dataset_path = None
        self.dataset_examples = []
        self.worker = None
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Dataset Overview tab
        self.overview_tab = self.create_overview_tab()
        self.tabs.addTab(self.overview_tab, "Overview")
        
        # Dataset Editor tab
        self.editor_tab = self.create_editor_tab()
        self.tabs.addTab(self.editor_tab, "Editor")
        
        # Augmentation tab
        self.augmentation_tab = self.create_augmentation_tab()
        self.tabs.addTab(self.augmentation_tab, "Augmentation")
        
        # Validation tab
        self.validation_tab = self.create_validation_tab()
        self.tabs.addTab(self.validation_tab, "Validation")
        
    def create_overview_tab(self) -> QWidget:
        """Create dataset overview tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("Load Dataset")
        self.load_btn.clicked.connect(self.load_dataset)
        controls_layout.addWidget(self.load_btn)
        
        self.new_btn = QPushButton("New Dataset")
        self.new_btn.clicked.connect(self.new_dataset)
        controls_layout.addWidget(self.new_btn)
        
        self.save_btn = QPushButton("Save Dataset")
        self.save_btn.clicked.connect(self.save_dataset)
        controls_layout.addWidget(self.save_btn)
        
        controls_layout.addStretch()
        
        self.validate_btn = QPushButton("Validate")
        self.validate_btn.clicked.connect(self.validate_dataset)
        controls_layout.addWidget(self.validate_btn)
        
        layout.addLayout(controls_layout)
        
        # Dataset info
        info_group = QGroupBox("Dataset Information")
        info_layout = QVBoxLayout(info_group)
        
        self.dataset_path_label = QLabel("No dataset loaded")
        info_layout.addWidget(self.dataset_path_label)
        
        stats_layout = QHBoxLayout()
        self.example_count_label = QLabel("Examples: 0")
        stats_layout.addWidget(self.example_count_label)
        
        self.empathy_score_label = QLabel("Avg Empathy: N/A")
        stats_layout.addWidget(self.empathy_score_label)
        
        self.validation_status_label = QLabel("Validation: Not checked")
        stats_layout.addWidget(self.validation_status_label)
        
        stats_layout.addStretch()
        info_layout.addLayout(stats_layout)
        
        layout.addWidget(info_group)
        
        # Examples table
        examples_group = QGroupBox("Dataset Examples")
        examples_layout = QVBoxLayout(examples_group)
        
        self.examples_table = QTableWidget()
        self.examples_table.setColumnCount(4)
        self.examples_table.setHorizontalHeaderLabels([
            "Context", "Response", "Emotion", "Empathy Score"
        ])
        self.examples_table.horizontalHeader().setStretchLastSection(True)
        self.examples_table.setAlternatingRowColors(True)
        self.examples_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        examples_layout.addWidget(self.examples_table)
        
        layout.addWidget(examples_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return widget
        
    def create_editor_tab(self) -> QWidget:
        """Create dataset editor tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Editor controls
        controls_layout = QHBoxLayout()
        
        self.add_example_btn = QPushButton("Add Example")
        self.add_example_btn.clicked.connect(self.add_example)
        controls_layout.addWidget(self.add_example_btn)
        
        self.remove_example_btn = QPushButton("Remove Example")
        self.remove_example_btn.clicked.connect(self.remove_example)
        controls_layout.addWidget(self.remove_example_btn)
        
        self.duplicate_example_btn = QPushButton("Duplicate")
        self.duplicate_example_btn.clicked.connect(self.duplicate_example)
        controls_layout.addWidget(self.duplicate_example_btn)
        
        controls_layout.addStretch()
        
        self.emotion_tag_combo = QComboBox()
        self.emotion_tag_combo.addItems([
            "Neutral", "Joy", "Sadness", "Anger", "Fear", "Surprise", "Disgust"
        ])
        controls_layout.addWidget(QLabel("Emotion:"))
        controls_layout.addWidget(self.emotion_tag_combo)
        
        self.apply_tag_btn = QPushButton("Apply Tag")
        self.apply_tag_btn.clicked.connect(self.apply_emotion_tag)
        controls_layout.addWidget(self.apply_tag_btn)
        
        layout.addLayout(controls_layout)
        
        # Example editor
        editor_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(editor_splitter)
        
        # Context editor
        context_widget = QWidget()
        context_layout = QVBoxLayout(context_widget)
        context_layout.addWidget(QLabel("Context:"))
        
        self.context_editor = QTextEdit()
        self.context_editor.setPlaceholderText(
            "Enter the conversation context here..."
        )
        context_layout.addWidget(self.context_editor)
        
        editor_splitter.addWidget(context_widget)
        
        # Response editor
        response_widget = QWidget()
        response_layout = QVBoxLayout(response_widget)
        response_layout.addWidget(QLabel("Response:"))
        
        self.response_editor = QTextEdit()
        self.response_editor.setPlaceholderText(
            "Enter the empathetic response here..."
        )
        response_layout.addWidget(self.response_editor)
        
        editor_splitter.addWidget(response_widget)
        
        # Metadata editor
        metadata_widget = QWidget()
        metadata_layout = QVBoxLayout(metadata_widget)
        metadata_layout.addWidget(QLabel("Metadata:"))
        
        self.metadata_editor = QTextEdit()
        self.metadata_editor.setPlaceholderText(
            '{\n  "emotion": "sadness",\n  "intensity": 3\n}'
        )
        self.metadata_editor.setMaximumHeight(150)
        metadata_layout.addWidget(self.metadata_editor)
        
        layout.addWidget(metadata_widget)
        
        # Navigation
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("< Previous")
        self.prev_btn.clicked.connect(self.prev_example)
        nav_layout.addWidget(self.prev_btn)
        
        self.example_index_label = QLabel("0 / 0")
        self.example_index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.example_index_label)
        
        self.next_btn = QPushButton("Next >")
        self.next_btn.clicked.connect(self.next_example)
        nav_layout.addWidget(self.next_btn)
        
        nav_layout.addStretch()
        
        self.save_example_btn = QPushButton("Save Changes")
        self.save_example_btn.clicked.connect(self.save_current_example)
        nav_layout.addWidget(self.save_example_btn)
        
        layout.addLayout(nav_layout)
        
        return widget
        
    def create_augmentation_tab(self) -> QWidget:
        """Create dataset augmentation tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Augmentation methods
        methods_group = QGroupBox("Augmentation Methods")
        methods_layout = QVBoxLayout(methods_group)
        
        self.synonym_check = QCheckBox("Synonym Replacement")
        self.synonym_check.setChecked(True)
        methods_layout.addWidget(self.synonym_check)
        
        self.paraphrase_check = QCheckBox("Paraphrasing")
        methods_layout.addWidget(self.paraphrase_check)
        
        self.emotion_variation_check = QCheckBox("Emotion Intensity Variation")
        self.emotion_variation_check.setChecked(True)
        methods_layout.addWidget(self.emotion_variation_check)
        
        self.persona_variation_check = QCheckBox("Persona Variation")
        methods_layout.addWidget(self.persona_variation_check)
        
        layout.addWidget(methods_group)
        
        # Augmentation settings
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        aug_factor_layout = QHBoxLayout()
        aug_factor_layout.addWidget(QLabel("Augmentation Factor:"))
        self.aug_factor_spin = QSpinBox()
        self.aug_factor_spin.setRange(1, 10)
        self.aug_factor_spin.setValue(2)
        aug_factor_layout.addWidget(self.aug_factor_spin)
        aug_factor_layout.addWidget(QLabel("x"))
        aug_factor_layout.addStretch()
        settings_layout.addLayout(aug_factor_layout)
        
        self.preserve_original_check = QCheckBox("Preserve Original Examples")
        self.preserve_original_check.setChecked(True)
        settings_layout.addWidget(self.preserve_original_check)
        
        layout.addWidget(settings_group)
        
        # Preview
        preview_group = QGroupBox("Augmentation Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.aug_preview_text = QTextEdit()
        self.aug_preview_text.setReadOnly(True)
        preview_layout.addWidget(self.aug_preview_text)
        
        layout.addWidget(preview_group)
        
        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        self.preview_aug_btn = QPushButton("Preview")
        self.preview_aug_btn.clicked.connect(self.preview_augmentation)
        actions_layout.addWidget(self.preview_aug_btn)
        
        self.apply_aug_btn = QPushButton("Apply Augmentation")
        self.apply_aug_btn.clicked.connect(self.apply_augmentation)
        actions_layout.addWidget(self.apply_aug_btn)
        
        layout.addLayout(actions_layout)
        
        return widget
        
    def create_validation_tab(self) -> QWidget:
        """Create dataset validation tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Validation criteria
        criteria_group = QGroupBox("Validation Criteria")
        criteria_layout = QVBoxLayout(criteria_group)
        
        self.check_empathy_keywords = QCheckBox("Check for empathy keywords")
        self.check_empathy_keywords.setChecked(True)
        criteria_layout.addWidget(self.check_empathy_keywords)
        
        self.check_emotion_tags = QCheckBox("Verify emotion tags")
        self.check_emotion_tags.setChecked(True)
        criteria_layout.addWidget(self.check_emotion_tags)
        
        self.check_response_length = QCheckBox("Check response length")
        self.check_response_length.setChecked(True)
        criteria_layout.addWidget(self.check_response_length)
        
        self.check_bias = QCheckBox("Scan for potential bias")
        self.check_bias.setChecked(True)
        criteria_layout.addWidget(self.check_bias)
        
        layout.addWidget(criteria_group)
        
        # Validation results
        results_group = QGroupBox("Validation Results")
        results_layout = QVBoxLayout(results_group)
        
        self.validation_results_text = QTextEdit()
        self.validation_results_text.setReadOnly(True)
        results_layout.addWidget(self.validation_results_text)
        
        layout.addWidget(results_group)
        
        # Statistics
        stats_group = QGroupBox("Dataset Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        stats_layout.addWidget(self.stats_text)
        
        layout.addWidget(stats_group)
        
        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        self.run_validation_btn = QPushButton("Run Validation")
        self.run_validation_btn.clicked.connect(self.run_validation)
        actions_layout.addWidget(self.run_validation_btn)
        
        self.export_report_btn = QPushButton("Export Report")
        self.export_report_btn.clicked.connect(self.export_validation_report)
        actions_layout.addWidget(self.export_report_btn)
        
        layout.addLayout(actions_layout)
        
        return widget
        
    def load_dataset(self):
        """Load dataset from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Dataset", "", 
            "Dataset Files (*.jsonl *.csv);;All Files (*.*)"
        )
        
        if file_path:
            self.import_dataset(file_path)
            
    def import_dataset(self, file_path: str):
        """Import dataset from file path"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create worker thread
        self.worker = DatasetWorker("load", file_path)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.on_dataset_loaded)
        self.worker.error.connect(self.on_error)
        self.worker.start()
        
    def on_dataset_loaded(self, result: dict):
        """Handle dataset loaded"""
        self.progress_bar.setVisible(False)
        
        self.dataset_examples = result["examples"]
        self.current_dataset_path = result["file_path"]
        
        # Update UI
        self.dataset_path_label.setText(f"Path: {self.current_dataset_path}")
        self.example_count_label.setText(f"Examples: {result['count']}")
        
        # Populate table
        self.populate_examples_table()
        
        # Update editor
        if self.dataset_examples:
            self.current_example_index = 0
            self.display_example(0)
            
        # Emit signal
        self.dataset_loaded.emit(self.current_dataset_path, result['count'])
        
        logger.info(f"Loaded dataset: {result['count']} examples")
        
    def populate_examples_table(self):
        """Populate examples table with dataset"""
        self.examples_table.setRowCount(len(self.dataset_examples))
        
        for i, example in enumerate(self.dataset_examples):
            # Context
            context_item = QTableWidgetItem(example.get("context", "")[:100] + "...")
            self.examples_table.setItem(i, 0, context_item)
            
            # Response
            response_item = QTableWidgetItem(example.get("response", "")[:100] + "...")
            self.examples_table.setItem(i, 1, response_item)
            
            # Emotion
            emotion = example.get("emotion", "neutral")
            emotion_item = QTableWidgetItem(emotion)
            self.examples_table.setItem(i, 2, emotion_item)
            
            # Empathy score (calculate simple score)
            response_text = example.get("response", "").lower()
            empathy_keywords = ["understand", "feel", "support", "hear", "sorry"]
            score = sum(1 for kw in empathy_keywords if kw in response_text) / 5.0
            score_item = QTableWidgetItem(f"{score:.2f}")
            self.examples_table.setItem(i, 3, score_item)
            
    def new_dataset(self):
        """Create new dataset"""
        self.dataset_examples = []
        self.current_dataset_path = None
        self.examples_table.setRowCount(0)
        self.dataset_path_label.setText("New dataset (unsaved)")
        self.example_count_label.setText("Examples: 0")
        self.empathy_score_label.setText("Avg Empathy: N/A")
        
    def save_dataset(self):
        """Save current dataset"""
        if not self.dataset_examples:
            QMessageBox.information(self, "Info", "No dataset to save")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Dataset", "", 
            "JSONL Files (*.jsonl);;CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                if file_path.endswith(".jsonl"):
                    with jsonlines.open(file_path, mode='w') as writer:
                        writer.write_all(self.dataset_examples)
                elif file_path.endswith(".csv"):
                    df = pd.DataFrame(self.dataset_examples)
                    df.to_csv(file_path, index=False)
                    
                self.current_dataset_path = file_path
                self.dataset_path_label.setText(f"Path: {file_path}")
                QMessageBox.information(self, "Success", "Dataset saved successfully")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save dataset: {str(e)}")
                
    def validate_dataset(self):
        """Validate current dataset"""
        if not self.current_dataset_path:
            QMessageBox.information(self, "Info", "No dataset loaded")
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create worker thread
        self.worker = DatasetWorker("validate", self.current_dataset_path)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.on_validation_complete)
        self.worker.error.connect(self.on_error)
        self.worker.start()
        
    def on_validation_complete(self, result: dict):
        """Handle validation complete"""
        self.progress_bar.setVisible(False)
        
        if result["valid"]:
            self.validation_status_label.setText("Validation: ✓ Passed")
            self.validation_status_label.setStyleSheet("color: green")
        else:
            self.validation_status_label.setText("Validation: ✗ Failed")
            self.validation_status_label.setStyleSheet("color: red")
            
        self.empathy_score_label.setText(
            f"Avg Empathy: {result['avg_empathy_score']:.2f}"
        )
        
        # Show detailed results
        self.tabs.setCurrentIndex(3)  # Switch to validation tab
        
        results_text = f"Validation Results\n"
        results_text += f"{'='*50}\n"
        results_text += f"Total Examples: {result['total_examples']}\n"
        results_text += f"Average Empathy Score: {result['avg_empathy_score']:.2f}\n"
        results_text += f"Valid: {'Yes' if result['valid'] else 'No'}\n\n"
        
        if result["issues"]:
            results_text += "Issues Found:\n"
            for issue in result["issues"][:10]:  # Show first 10 issues
                results_text += f"- {issue}\n"
            if len(result["issues"]) > 10:
                results_text += f"... and {len(result['issues']) - 10} more issues\n"
                
        self.validation_results_text.setText(results_text)
        
        # Emit signal
        self.dataset_validated.emit(result["valid"], result["issues"])
        
    def add_example(self):
        """Add new example to dataset"""
        new_example = {
            "context": "New conversation context",
            "response": "New empathetic response",
            "emotion": "neutral",
            "metadata": {}
        }
        
        self.dataset_examples.append(new_example)
        self.current_example_index = len(self.dataset_examples) - 1
        self.display_example(self.current_example_index)
        self.populate_examples_table()
        self.example_count_label.setText(f"Examples: {len(self.dataset_examples)}")
        
    def remove_example(self):
        """Remove current example from dataset"""
        if not self.dataset_examples:
            return
            
        if self.current_example_index < len(self.dataset_examples):
            del self.dataset_examples[self.current_example_index]
            
            if self.current_example_index >= len(self.dataset_examples):
                self.current_example_index = len(self.dataset_examples) - 1
                
            if self.dataset_examples:
                self.display_example(self.current_example_index)
            else:
                self.context_editor.clear()
                self.response_editor.clear()
                self.metadata_editor.clear()
                
            self.populate_examples_table()
            self.example_count_label.setText(f"Examples: {len(self.dataset_examples)}")
            
    def duplicate_example(self):
        """Duplicate current example"""
        if not self.dataset_examples or self.current_example_index >= len(self.dataset_examples):
            return
            
        current = self.dataset_examples[self.current_example_index]
        duplicate = current.copy()
        
        self.dataset_examples.insert(self.current_example_index + 1, duplicate)
        self.current_example_index += 1
        self.display_example(self.current_example_index)
        self.populate_examples_table()
        self.example_count_label.setText(f"Examples: {len(self.dataset_examples)}")
        
    def prev_example(self):
        """Navigate to previous example"""
        if self.current_example_index > 0:
            self.save_current_example()
            self.current_example_index -= 1
            self.display_example(self.current_example_index)
            
    def next_example(self):
        """Navigate to next example"""
        if self.current_example_index < len(self.dataset_examples) - 1:
            self.save_current_example()
            self.current_example_index += 1
            self.display_example(self.current_example_index)
            
    def display_example(self, index: int):
        """Display example at given index"""
        if 0 <= index < len(self.dataset_examples):
            example = self.dataset_examples[index]
            
            self.context_editor.setText(example.get("context", ""))
            self.response_editor.setText(example.get("response", ""))
            
            metadata = example.get("metadata", {})
            self.metadata_editor.setText(json.dumps(metadata, indent=2))
            
            # Update navigation label
            self.example_index_label.setText(
                f"{index + 1} / {len(self.dataset_examples)}"
            )
            
            # Update navigation buttons
            self.prev_btn.setEnabled(index > 0)
            self.next_btn.setEnabled(index < len(self.dataset_examples) - 1)
            
    def save_current_example(self):
        """Save changes to current example"""
        if not self.dataset_examples or self.current_example_index >= len(self.dataset_examples):
            return
            
        example = self.dataset_examples[self.current_example_index]
        example["context"] = self.context_editor.toPlainText()
        example["response"] = self.response_editor.toPlainText()
        
        try:
            metadata_text = self.metadata_editor.toPlainText()
            if metadata_text.strip():
                example["metadata"] = json.loads(metadata_text)
        except json.JSONDecodeError:
            logger.warning("Invalid metadata JSON")
            
        # Update table
        self.populate_examples_table()
        
    def apply_emotion_tag(self):
        """Apply emotion tag to current example"""
        if not self.dataset_examples or self.current_example_index >= len(self.dataset_examples):
            return
            
        emotion = self.emotion_tag_combo.currentText().lower()
        self.dataset_examples[self.current_example_index]["emotion"] = emotion
        
        # Update metadata editor
        metadata = self.dataset_examples[self.current_example_index].get("metadata", {})
        metadata["emotion"] = emotion
        self.metadata_editor.setText(json.dumps(metadata, indent=2))
        
        # Update table
        self.populate_examples_table()
        
    def preview_augmentation(self):
        """Preview augmentation results"""
        if not self.dataset_examples:
            QMessageBox.information(self, "Info", "No dataset loaded")
            return
            
        # Get first example for preview
        example = self.dataset_examples[0]
        
        preview_text = "Augmentation Preview\n"
        preview_text += "="*50 + "\n\n"
        preview_text += f"Original:\n"
        preview_text += f"Context: {example.get('context', '')}\n"
        preview_text += f"Response: {example.get('response', '')}\n\n"
        
        if self.synonym_check.isChecked():
            preview_text += "Synonym Replacement:\n"
            preview_text += f"Response: {self.apply_synonym_replacement(example['response'])}\n\n"
            
        if self.emotion_variation_check.isChecked():
            preview_text += "Emotion Variation:\n"
            for intensity in [1, 3, 5]:
                preview_text += f"Intensity {intensity}: [Modified response would appear here]\n"
                
        self.aug_preview_text.setText(preview_text)
        
    def apply_synonym_replacement(self, text: str) -> str:
        """Apply simple synonym replacement (placeholder)"""
        # This is a placeholder - in real implementation would use NLTK/spaCy
        replacements = {
            "understand": "comprehend",
            "feel": "sense",
            "support": "help",
            "difficult": "challenging"
        }
        
        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
            
        return result
        
    def apply_augmentation(self):
        """Apply augmentation to dataset"""
        if not self.dataset_examples:
            QMessageBox.information(self, "Info", "No dataset loaded")
            return
            
        # Placeholder for augmentation
        QMessageBox.information(
            self, "Info", 
            "Augmentation would be applied here.\n"
            f"Factor: {self.aug_factor_spin.value()}x"
        )
        
    def run_validation(self):
        """Run detailed validation"""
        self.validate_dataset()
        
    def export_validation_report(self):
        """Export validation report"""
        if not self.validation_results_text.toPlainText():
            QMessageBox.information(self, "Info", "No validation results to export")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Validation Report", 
            f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.validation_results_text.toPlainText())
                QMessageBox.information(self, "Success", "Report exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export report: {str(e)}")
                
    def update_status(self, message: str):
        """Update status message"""
        # Could be shown in a status bar
        logger.info(message)
        
    def on_error(self, error: str):
        """Handle error"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", error)
        
    # Properties for index tracking
    @property
    def current_example_index(self):
        return getattr(self, '_current_example_index', 0)
        
    @current_example_index.setter
    def current_example_index(self, value):
        self._current_example_index = value 