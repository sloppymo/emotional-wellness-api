"""
Training Panel
Configure and monitor model training with LoRA support
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QSlider,
    QCheckBox, QTextEdit, QProgressBar, QTableWidget,
    QTableWidgetItem, QTabWidget, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QFont

import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class TrainingWorker(QThread):
    """Worker thread for model training"""
    progress = pyqtSignal(int, str)  # epoch, status
    metrics = pyqtSignal(dict)  # training metrics
    finished = pyqtSignal(str)  # model path
    error = pyqtSignal(str)
    
    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.is_running = True
        
    def run(self):
        """Run training process"""
        try:
            # Simulate training (replace with actual training code)
            total_epochs = self.config.get("epochs", 3)
            
            for epoch in range(total_epochs):
                if not self.is_running:
                    break
                    
                self.progress.emit(epoch + 1, f"Training epoch {epoch + 1}/{total_epochs}")
                
                # Simulate batch training
                for step in range(100):
                    if not self.is_running:
                        break
                        
                    # Emit metrics
                    metrics = {
                        "epoch": epoch + 1,
                        "step": step,
                        "loss": 2.5 - (epoch * 0.5) - (step * 0.001),
                        "accuracy": 0.6 + (epoch * 0.1) + (step * 0.001),
                        "learning_rate": self.config.get("learning_rate", 5e-5),
                        "empathy_score": 0.5 + (epoch * 0.15)
                    }
                    self.metrics.emit(metrics)
                    
                    # Sleep to simulate processing
                    self.msleep(50)
                    
            if self.is_running:
                self.finished.emit("model/fine_tuned_model.pth")
                
        except Exception as e:
            self.error.emit(str(e))
            
    def stop(self):
        """Stop training"""
        self.is_running = False


class TrainingPanel(QWidget):
    """Panel for configuring and monitoring model training"""
    
    # Signals
    training_started = pyqtSignal()
    training_stopped = pyqtSignal()
    training_completed = pyqtSignal(str)  # model path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # State
        self.is_training = False
        self.training_worker = None
        self.training_metrics = []
        self.current_config = {}
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Configuration tab
        self.config_tab = self.create_config_tab()
        self.tabs.addTab(self.config_tab, "Configuration")
        
        # Monitoring tab
        self.monitoring_tab = self.create_monitoring_tab()
        self.tabs.addTab(self.monitoring_tab, "Monitoring")
        
        # History tab
        self.history_tab = self.create_history_tab()
        self.tabs.addTab(self.history_tab, "History")
        
    def create_config_tab(self) -> QWidget:
        """Create training configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Model configuration
        model_group = QGroupBox("Model Configuration")
        model_layout = QFormLayout(model_group)
        
        # Base model
        self.base_model_combo = QComboBox()
        self.base_model_combo.addItems([
            "microsoft/DialoGPT-medium",
            "facebook/blenderbot-400M-distill",
            "google/flan-t5-base",
            "EleutherAI/gpt-neo-1.3B",
            "Custom..."
        ])
        model_layout.addRow("Base Model:", self.base_model_combo)
        
        # Framework
        self.framework_combo = QComboBox()
        self.framework_combo.addItems(["Hugging Face", "OpenAI"])
        self.framework_combo.currentTextChanged.connect(self.on_framework_changed)
        model_layout.addRow("Framework:", self.framework_combo)
        
        layout.addWidget(model_group)
        
        # LoRA Configuration
        lora_group = QGroupBox("LoRA Configuration")
        lora_layout = QFormLayout(lora_group)
        
        # Enable LoRA
        self.enable_lora_check = QCheckBox("Enable LoRA")
        self.enable_lora_check.setChecked(True)
        self.enable_lora_check.toggled.connect(self.on_lora_toggled)
        lora_layout.addRow(self.enable_lora_check)
        
        # LoRA rank
        self.lora_rank_spin = QSpinBox()
        self.lora_rank_spin.setRange(1, 64)
        self.lora_rank_spin.setValue(8)
        lora_layout.addRow("LoRA Rank (r):", self.lora_rank_spin)
        
        # LoRA alpha
        self.lora_alpha_spin = QSpinBox()
        self.lora_alpha_spin.setRange(1, 128)
        self.lora_alpha_spin.setValue(16)
        lora_layout.addRow("LoRA Alpha (α):", self.lora_alpha_spin)
        
        # LoRA dropout
        self.lora_dropout_spin = QDoubleSpinBox()
        self.lora_dropout_spin.setRange(0.0, 0.5)
        self.lora_dropout_spin.setSingleStep(0.05)
        self.lora_dropout_spin.setValue(0.1)
        lora_layout.addRow("LoRA Dropout:", self.lora_dropout_spin)
        
        # Target modules
        self.target_modules_edit = QLineEdit("q_proj,v_proj")
        lora_layout.addRow("Target Modules:", self.target_modules_edit)
        
        layout.addWidget(lora_group)
        
        # Training parameters
        training_group = QGroupBox("Training Parameters")
        training_layout = QFormLayout(training_group)
        
        # Epochs
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 100)
        self.epochs_spin.setValue(3)
        training_layout.addRow("Epochs:", self.epochs_spin)
        
        # Batch size
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 128)
        self.batch_size_spin.setValue(4)
        training_layout.addRow("Batch Size:", self.batch_size_spin)
        
        # Learning rate
        self.learning_rate_spin = QDoubleSpinBox()
        self.learning_rate_spin.setRange(1e-6, 1e-2)
        self.learning_rate_spin.setDecimals(6)
        self.learning_rate_spin.setSingleStep(1e-5)
        self.learning_rate_spin.setValue(5e-5)
        training_layout.addRow("Learning Rate:", self.learning_rate_spin)
        
        # Warmup steps
        self.warmup_steps_spin = QSpinBox()
        self.warmup_steps_spin.setRange(0, 1000)
        self.warmup_steps_spin.setValue(100)
        training_layout.addRow("Warmup Steps:", self.warmup_steps_spin)
        
        # Gradient accumulation
        self.grad_accum_spin = QSpinBox()
        self.grad_accum_spin.setRange(1, 32)
        self.grad_accum_spin.setValue(1)
        training_layout.addRow("Gradient Accumulation:", self.grad_accum_spin)
        
        layout.addWidget(training_group)
        
        # Empathy-specific settings
        empathy_group = QGroupBox("Empathy Training Settings")
        empathy_layout = QFormLayout(empathy_group)
        
        # Empathy loss weight
        self.empathy_weight_spin = QDoubleSpinBox()
        self.empathy_weight_spin.setRange(0.0, 1.0)
        self.empathy_weight_spin.setSingleStep(0.1)
        self.empathy_weight_spin.setValue(0.3)
        empathy_layout.addRow("Empathy Loss Weight:", self.empathy_weight_spin)
        
        # Emotion balancing
        self.emotion_balance_check = QCheckBox("Balance emotion distribution")
        self.emotion_balance_check.setChecked(True)
        empathy_layout.addRow(self.emotion_balance_check)
        
        # Persona consistency
        self.persona_consistency_check = QCheckBox("Enforce persona consistency")
        empathy_layout.addRow(self.persona_consistency_check)
        
        layout.addWidget(empathy_group)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        self.validate_btn = QPushButton("Validate Config")
        self.validate_btn.clicked.connect(self.validate_config)
        actions_layout.addWidget(self.validate_btn)
        
        self.save_config_btn = QPushButton("Save Config")
        self.save_config_btn.clicked.connect(self.save_config)
        actions_layout.addWidget(self.save_config_btn)
        
        self.load_config_btn = QPushButton("Load Config")
        self.load_config_btn.clicked.connect(self.load_config)
        actions_layout.addWidget(self.load_config_btn)
        
        self.start_btn = QPushButton("Start Training")
        self.start_btn.clicked.connect(self.start_training)
        self.start_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; }"
        )
        actions_layout.addWidget(self.start_btn)
        
        layout.addLayout(actions_layout)
        
        return widget
        
    def create_monitoring_tab(self) -> QWidget:
        """Create training monitoring tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        self.stop_btn = QPushButton("Stop Training")
        self.stop_btn.clicked.connect(self.stop_training)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; }"
        )
        status_layout.addWidget(self.stop_btn)
        
        layout.addLayout(status_layout)
        
        # Progress
        progress_group = QGroupBox("Training Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.epoch_label = QLabel("Epoch: 0/0")
        progress_layout.addWidget(self.epoch_label)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.eta_label = QLabel("ETA: Calculating...")
        progress_layout.addWidget(self.eta_label)
        
        layout.addWidget(progress_group)
        
        # Live metrics
        metrics_group = QGroupBox("Live Metrics")
        metrics_layout = QVBoxLayout(metrics_group)
        
        # Metrics display
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        self.metrics_text.setMaximumHeight(200)
        self.metrics_text.setFont(QFont("Consolas", 10))
        metrics_layout.addWidget(self.metrics_text)
        
        layout.addWidget(metrics_group)
        
        # Recent checkpoints
        checkpoints_group = QGroupBox("Recent Checkpoints")
        checkpoints_layout = QVBoxLayout(checkpoints_group)
        
        self.checkpoints_table = QTableWidget()
        self.checkpoints_table.setColumnCount(4)
        self.checkpoints_table.setHorizontalHeaderLabels([
            "Checkpoint", "Epoch", "Loss", "Empathy Score"
        ])
        self.checkpoints_table.horizontalHeader().setStretchLastSection(True)
        checkpoints_layout.addWidget(self.checkpoints_table)
        
        layout.addWidget(checkpoints_group)
        
        # Console output
        console_group = QGroupBox("Training Console")
        console_layout = QVBoxLayout(console_group)
        
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setMaximumHeight(150)
        self.console_text.setFont(QFont("Consolas", 9))
        console_layout.addWidget(self.console_text)
        
        layout.addWidget(console_group)
        
        return widget
        
    def create_history_tab(self) -> QWidget:
        """Create training history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Training runs table
        runs_group = QGroupBox("Training History")
        runs_layout = QVBoxLayout(runs_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Model", "Dataset", "Epochs", "Final Loss", "Status"
        ])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        runs_layout.addWidget(self.history_table)
        
        # Actions
        history_actions = QHBoxLayout()
        
        self.load_checkpoint_btn = QPushButton("Load Checkpoint")
        self.load_checkpoint_btn.clicked.connect(self.load_checkpoint)
        history_actions.addWidget(self.load_checkpoint_btn)
        
        self.compare_runs_btn = QPushButton("Compare Runs")
        self.compare_runs_btn.clicked.connect(self.compare_runs)
        history_actions.addWidget(self.compare_runs_btn)
        
        self.export_metrics_btn = QPushButton("Export Metrics")
        self.export_metrics_btn.clicked.connect(self.export_metrics)
        history_actions.addWidget(self.export_metrics_btn)
        
        history_actions.addStretch()
        
        self.delete_run_btn = QPushButton("Delete Run")
        self.delete_run_btn.clicked.connect(self.delete_run)
        history_actions.addWidget(self.delete_run_btn)
        
        runs_layout.addLayout(history_actions)
        
        layout.addWidget(runs_group)
        
        # Run details
        details_group = QGroupBox("Run Details")
        details_layout = QVBoxLayout(details_group)
        
        self.run_details_text = QTextEdit()
        self.run_details_text.setReadOnly(True)
        details_layout.addWidget(self.run_details_text)
        
        layout.addWidget(details_group)
        
        return widget
        
    def on_framework_changed(self, framework: str):
        """Handle framework change"""
        if framework == "OpenAI":
            # Disable LoRA settings for OpenAI
            self.enable_lora_check.setChecked(False)
            self.enable_lora_check.setEnabled(False)
            self.lora_rank_spin.setEnabled(False)
            self.lora_alpha_spin.setEnabled(False)
            self.lora_dropout_spin.setEnabled(False)
            self.target_modules_edit.setEnabled(False)
        else:
            # Enable LoRA settings for Hugging Face
            self.enable_lora_check.setEnabled(True)
            self.on_lora_toggled(self.enable_lora_check.isChecked())
            
    def on_lora_toggled(self, checked: bool):
        """Handle LoRA toggle"""
        self.lora_rank_spin.setEnabled(checked)
        self.lora_alpha_spin.setEnabled(checked)
        self.lora_dropout_spin.setEnabled(checked)
        self.target_modules_edit.setEnabled(checked)
        
    def validate_config(self):
        """Validate training configuration"""
        config = self.get_config()
        
        # Basic validation
        issues = []
        
        if config["batch_size"] > 32 and not config.get("gradient_accumulation", 1) > 1:
            issues.append("Large batch size without gradient accumulation may cause OOM")
            
        if config["learning_rate"] > 1e-3:
            issues.append("Learning rate may be too high for fine-tuning")
            
        if config.get("lora_enabled") and config["lora_rank"] > 32:
            issues.append("LoRA rank > 32 may not provide additional benefits")
            
        if issues:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Configuration Issues",
                "The following issues were found:\n\n" + "\n".join(f"• {issue}" for issue in issues)
            )
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Success", "Configuration is valid!")
            
    def save_config(self):
        """Save training configuration"""
        from PyQt6.QtWidgets import QFileDialog
        
        config = self.get_config()
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", 
            f"training_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=2)
                    
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", "Configuration saved successfully!")
                
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")
                
    def load_config(self):
        """Load training configuration"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                    
                self.set_config(config)
                
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", "Configuration loaded successfully!")
                
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to load configuration: {str(e)}")
                
    def get_config(self) -> Dict:
        """Get current configuration"""
        config = {
            "base_model": self.base_model_combo.currentText(),
            "framework": self.framework_combo.currentText(),
            "epochs": self.epochs_spin.value(),
            "batch_size": self.batch_size_spin.value(),
            "learning_rate": self.learning_rate_spin.value(),
            "warmup_steps": self.warmup_steps_spin.value(),
            "gradient_accumulation": self.grad_accum_spin.value(),
            "empathy_weight": self.empathy_weight_spin.value(),
            "emotion_balance": self.emotion_balance_check.isChecked(),
            "persona_consistency": self.persona_consistency_check.isChecked(),
        }
        
        if self.enable_lora_check.isChecked() and self.framework_combo.currentText() != "OpenAI":
            config.update({
                "lora_enabled": True,
                "lora_rank": self.lora_rank_spin.value(),
                "lora_alpha": self.lora_alpha_spin.value(),
                "lora_dropout": self.lora_dropout_spin.value(),
                "target_modules": self.target_modules_edit.text().split(",")
            })
        else:
            config["lora_enabled"] = False
            
        return config
        
    def set_config(self, config: Dict):
        """Set configuration from dict"""
        self.base_model_combo.setCurrentText(config.get("base_model", "microsoft/DialoGPT-medium"))
        self.framework_combo.setCurrentText(config.get("framework", "Hugging Face"))
        self.epochs_spin.setValue(config.get("epochs", 3))
        self.batch_size_spin.setValue(config.get("batch_size", 4))
        self.learning_rate_spin.setValue(config.get("learning_rate", 5e-5))
        self.warmup_steps_spin.setValue(config.get("warmup_steps", 100))
        self.grad_accum_spin.setValue(config.get("gradient_accumulation", 1))
        self.empathy_weight_spin.setValue(config.get("empathy_weight", 0.3))
        self.emotion_balance_check.setChecked(config.get("emotion_balance", True))
        self.persona_consistency_check.setChecked(config.get("persona_consistency", False))
        
        if config.get("lora_enabled", False):
            self.enable_lora_check.setChecked(True)
            self.lora_rank_spin.setValue(config.get("lora_rank", 8))
            self.lora_alpha_spin.setValue(config.get("lora_alpha", 16))
            self.lora_dropout_spin.setValue(config.get("lora_dropout", 0.1))
            self.target_modules_edit.setText(",".join(config.get("target_modules", ["q_proj", "v_proj"])))
            
    def start_training(self):
        """Start model training"""
        if self.is_training:
            return
            
        # Get configuration
        self.current_config = self.get_config()
        
        # Update UI
        self.is_training = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Training...")
        self.status_label.setStyleSheet("color: green")
        
        # Switch to monitoring tab
        self.tabs.setCurrentIndex(1)
        
        # Clear previous metrics
        self.metrics_text.clear()
        self.console_text.clear()
        self.training_metrics = []
        
        # Create worker thread
        self.training_worker = TrainingWorker(self.current_config)
        self.training_worker.progress.connect(self.on_training_progress)
        self.training_worker.metrics.connect(self.on_training_metrics)
        self.training_worker.finished.connect(self.on_training_finished)
        self.training_worker.error.connect(self.on_training_error)
        self.training_worker.start()
        
        # Log to console
        self.log_console(f"Starting training with config: {json.dumps(self.current_config, indent=2)}")
        
        # Emit signal
        self.training_started.emit()
        
    def stop_training(self):
        """Stop model training"""
        if not self.is_training:
            return
            
        if self.training_worker:
            self.training_worker.stop()
            self.training_worker.wait()
            
        self.is_training = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Stopped")
        self.status_label.setStyleSheet("color: orange")
        
        self.log_console("Training stopped by user")
        
        # Emit signal
        self.training_stopped.emit()
        
    def on_training_progress(self, epoch: int, status: str):
        """Handle training progress update"""
        self.epoch_label.setText(f"Epoch: {epoch}/{self.current_config['epochs']}")
        self.status_label.setText(status)
        
        # Update progress bar
        progress = int((epoch / self.current_config['epochs']) * 100)
        self.progress_bar.setValue(progress)
        
        # Estimate time remaining
        # TODO: Implement proper ETA calculation
        self.eta_label.setText("ETA: Calculating...")
        
    def on_training_metrics(self, metrics: Dict):
        """Handle training metrics update"""
        self.training_metrics.append(metrics)
        
        # Update metrics display
        metrics_text = f"Epoch: {metrics['epoch']}\n"
        metrics_text += f"Step: {metrics['step']}\n"
        metrics_text += f"Loss: {metrics['loss']:.4f}\n"
        metrics_text += f"Accuracy: {metrics['accuracy']:.4f}\n"
        metrics_text += f"Learning Rate: {metrics['learning_rate']:.6f}\n"
        metrics_text += f"Empathy Score: {metrics['empathy_score']:.3f}\n"
        
        self.metrics_text.setText(metrics_text)
        
        # Log to console (sample every 10 steps)
        if metrics['step'] % 10 == 0:
            self.log_console(
                f"[Epoch {metrics['epoch']}, Step {metrics['step']}] "
                f"Loss: {metrics['loss']:.4f}, Acc: {metrics['accuracy']:.4f}"
            )
            
    def on_training_finished(self, model_path: str):
        """Handle training completion"""
        self.is_training = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Completed")
        self.status_label.setStyleSheet("color: blue")
        self.progress_bar.setValue(100)
        
        self.log_console(f"Training completed! Model saved to: {model_path}")
        
        # Add to checkpoints table
        row = self.checkpoints_table.rowCount()
        self.checkpoints_table.insertRow(row)
        self.checkpoints_table.setItem(row, 0, QTableWidgetItem(model_path))
        self.checkpoints_table.setItem(row, 1, QTableWidgetItem(str(self.current_config['epochs'])))
        
        if self.training_metrics:
            last_metrics = self.training_metrics[-1]
            self.checkpoints_table.setItem(row, 2, QTableWidgetItem(f"{last_metrics['loss']:.4f}"))
            self.checkpoints_table.setItem(row, 3, QTableWidgetItem(f"{last_metrics['empathy_score']:.3f}"))
            
        # Add to history
        self.add_to_history(model_path, "Completed")
        
        # Emit signal
        self.training_completed.emit(model_path)
        
    def on_training_error(self, error: str):
        """Handle training error"""
        self.is_training = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Error")
        self.status_label.setStyleSheet("color: red")
        
        self.log_console(f"Training error: {error}")
        
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Training Error", f"An error occurred during training:\n\n{error}")
        
        # Add to history
        self.add_to_history("N/A", "Failed")
        
    def log_console(self, message: str):
        """Log message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_text.append(f"[{timestamp}] {message}")
        
    def add_to_history(self, model_path: str, status: str):
        """Add training run to history"""
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)
        
        self.history_table.setItem(row, 0, QTableWidgetItem(datetime.now().strftime("%Y-%m-%d %H:%M")))
        self.history_table.setItem(row, 1, QTableWidgetItem(self.current_config['base_model']))
        self.history_table.setItem(row, 2, QTableWidgetItem("Current Dataset"))  # TODO: Get actual dataset name
        self.history_table.setItem(row, 3, QTableWidgetItem(str(self.current_config['epochs'])))
        
        if self.training_metrics:
            final_loss = self.training_metrics[-1]['loss']
            self.history_table.setItem(row, 4, QTableWidgetItem(f"{final_loss:.4f}"))
        else:
            self.history_table.setItem(row, 4, QTableWidgetItem("N/A"))
            
        self.history_table.setItem(row, 5, QTableWidgetItem(status))
        
    def load_checkpoint(self):
        """Load a saved checkpoint"""
        # TODO: Implement checkpoint loading
        pass
        
    def compare_runs(self):
        """Compare multiple training runs"""
        # TODO: Implement run comparison
        pass
        
    def export_metrics(self):
        """Export training metrics"""
        if not self.training_metrics:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Info", "No metrics to export")
            return
            
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Metrics",
            f"training_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump({
                        "config": self.current_config,
                        "metrics": self.training_metrics
                    }, f, indent=2)
                    
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", "Metrics exported successfully!")
                
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to export metrics: {str(e)}")
                
    def delete_run(self):
        """Delete selected training run from history"""
        current_row = self.history_table.currentRow()
        if current_row >= 0:
            self.history_table.removeRow(current_row) 