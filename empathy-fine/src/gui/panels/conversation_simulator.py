"""
Conversation Simulator Panel
Real-time chat interface for testing model responses
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QComboBox, QSlider, QGroupBox,
    QSplitter, QListWidget, QListWidgetItem, QCheckBox,
    QSpinBox, QToolButton, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor

import json
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ChatMessage:
    """Represents a single chat message"""
    def __init__(self, role: str, content: str, timestamp: datetime = None,
                 emotion: str = None, empathy_score: float = None):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.emotion = emotion
        self.empathy_score = empathy_score
        
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "emotion": self.emotion,
            "empathy_score": self.empathy_score
        }


class ConversationSimulator(QWidget):
    """Interactive conversation simulator for testing empathy responses"""
    
    # Signals
    message_sent = pyqtSignal(str)  # User message
    response_received = pyqtSignal(str, float)  # Response, empathy score
    conversation_saved = pyqtSignal(list)  # List of messages
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # State
        self.conversation_history: List[ChatMessage] = []
        self.current_model = None
        self.is_generating = False
        
        # Emotion settings
        self.emotion_intensity = 3  # 1-5 scale
        self.current_emotion = "neutral"
        self.enable_empathy_mode = True
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Top controls
        controls = self.create_controls()
        layout.addWidget(controls)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, 1)
        
        # Left: Chat interface
        chat_widget = self.create_chat_interface()
        splitter.addWidget(chat_widget)
        
        # Right: Analysis panel
        analysis_widget = self.create_analysis_panel()
        splitter.addWidget(analysis_widget)
        
        splitter.setSizes([600, 300])
        
    def create_controls(self) -> QWidget:
        """Create top control panel"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Model selector
        layout.addWidget(QLabel("Model:"))
        self.model_selector = QComboBox()
        self.model_selector.addItems([
            "Base Model",
            "Fine-tuned v1",
            "Fine-tuned v2",
            "OpenAI GPT-3.5",
            "OpenAI GPT-4"
        ])
        self.model_selector.currentTextChanged.connect(self.on_model_changed)
        layout.addWidget(self.model_selector)
        
        # Persona selector
        layout.addWidget(QLabel("Persona:"))
        self.persona_selector = QComboBox()
        self.persona_selector.addItems([
            "Default",
            "Therapist",
            "Friend",
            "Counselor",
            "Support Agent",
            "Custom..."
        ])
        layout.addWidget(self.persona_selector)
        
        # Emotion control
        layout.addWidget(QLabel("Emotion:"))
        self.emotion_selector = QComboBox()
        self.emotion_selector.addItems([
            "Neutral",
            "Joy",
            "Sadness",
            "Anger",
            "Fear",
            "Surprise",
            "Disgust"
        ])
        self.emotion_selector.currentTextChanged.connect(self.on_emotion_changed)
        layout.addWidget(self.emotion_selector)
        
        # Intensity slider
        layout.addWidget(QLabel("Intensity:"))
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(1, 5)
        self.intensity_slider.setValue(3)
        self.intensity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.intensity_slider.setMaximumWidth(100)
        self.intensity_slider.valueChanged.connect(self.on_intensity_changed)
        layout.addWidget(self.intensity_slider)
        
        self.intensity_label = QLabel("3")
        layout.addWidget(self.intensity_label)
        
        # Empathy mode
        self.empathy_checkbox = QCheckBox("Empathy Mode")
        self.empathy_checkbox.setChecked(True)
        self.empathy_checkbox.toggled.connect(self.on_empathy_toggled)
        layout.addWidget(self.empathy_checkbox)
        
        layout.addStretch()
        
        # Action buttons
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_conversation)
        layout.addWidget(self.clear_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_conversation)
        layout.addWidget(self.save_btn)
        
        return widget
        
    def create_chat_interface(self) -> QWidget:
        """Create the main chat interface"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Arial", 10))
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)
        self.message_input.setFont(QFont("Arial", 11))
        input_layout.addWidget(self.message_input)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setDefault(True)
        input_layout.addWidget(self.send_btn)
        
        # Voice input button (placeholder)
        self.voice_btn = QToolButton()
        self.voice_btn.setText("🎤")
        self.voice_btn.setToolTip("Voice input (coming soon)")
        input_layout.addWidget(self.voice_btn)
        
        layout.addLayout(input_layout)
        
        return widget
        
    def create_analysis_panel(self) -> QWidget:
        """Create the analysis panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Empathy Analysis
        empathy_group = QGroupBox("Empathy Analysis")
        empathy_layout = QVBoxLayout(empathy_group)
        
        # Current score
        score_layout = QHBoxLayout()
        score_layout.addWidget(QLabel("Current Score:"))
        self.empathy_score_label = QLabel("N/A")
        self.empathy_score_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        score_layout.addWidget(self.empathy_score_label)
        score_layout.addStretch()
        empathy_layout.addLayout(score_layout)
        
        # Empathy dimensions
        self.empathy_dimensions = {
            "Cognitive": QLabel("0.0"),
            "Emotional": QLabel("0.0"),
            "Compassionate": QLabel("0.0")
        }
        
        for dimension, label in self.empathy_dimensions.items():
            dim_layout = QHBoxLayout()
            dim_layout.addWidget(QLabel(f"{dimension}:"))
            label.setFont(QFont("Arial", 10))
            dim_layout.addWidget(label)
            dim_layout.addStretch()
            empathy_layout.addLayout(dim_layout)
            
        layout.addWidget(empathy_group)
        
        # Emotion Detection
        emotion_group = QGroupBox("Emotion Detection")
        emotion_layout = QVBoxLayout(emotion_group)
        
        self.detected_emotions = QListWidget()
        self.detected_emotions.setMaximumHeight(100)
        emotion_layout.addWidget(self.detected_emotions)
        
        layout.addWidget(emotion_group)
        
        # Response Metrics
        metrics_group = QGroupBox("Response Metrics")
        metrics_layout = QVBoxLayout(metrics_group)
        
        self.response_time_label = QLabel("Response Time: N/A")
        metrics_layout.addWidget(self.response_time_label)
        
        self.word_count_label = QLabel("Word Count: N/A")
        metrics_layout.addWidget(self.word_count_label)
        
        self.sentiment_label = QLabel("Sentiment: N/A")
        metrics_layout.addWidget(self.sentiment_label)
        
        layout.addWidget(metrics_group)
        
        # Suggestions
        suggestions_group = QGroupBox("Improvement Suggestions")
        suggestions_layout = QVBoxLayout(suggestions_group)
        
        self.suggestions_list = QTextEdit()
        self.suggestions_list.setReadOnly(True)
        self.suggestions_list.setMaximumHeight(100)
        suggestions_layout.addWidget(self.suggestions_list)
        
        layout.addWidget(suggestions_group)
        
        layout.addStretch()
        
        return widget
        
    def send_message(self):
        """Send user message and get response"""
        message_text = self.message_input.text().strip()
        if not message_text or self.is_generating:
            return
            
        # Clear input
        self.message_input.clear()
        
        # Add user message
        user_msg = ChatMessage("user", message_text, emotion=self.current_emotion)
        self.conversation_history.append(user_msg)
        self.add_message_to_display(user_msg)
        
        # Emit signal
        self.message_sent.emit(message_text)
        
        # Generate response
        self.generate_response(message_text)
        
    def generate_response(self, user_message: str):
        """Generate AI response"""
        self.is_generating = True
        self.send_btn.setEnabled(False)
        self.send_btn.setText("Generating...")
        
        # Start timer for response time
        start_time = datetime.now()
        
        # Simulate response generation (replace with actual model call)
        QTimer.singleShot(1000, lambda: self.on_response_generated(
            user_message, start_time
        ))
        
    def on_response_generated(self, user_message: str, start_time: datetime):
        """Handle generated response"""
        # Simulate response (replace with actual model output)
        response_text = self.generate_mock_response(user_message)
        
        # Calculate metrics
        response_time = (datetime.now() - start_time).total_seconds()
        empathy_score = self.calculate_mock_empathy_score(response_text)
        
        # Create assistant message
        assistant_msg = ChatMessage(
            "assistant", 
            response_text,
            empathy_score=empathy_score
        )
        self.conversation_history.append(assistant_msg)
        self.add_message_to_display(assistant_msg)
        
        # Update analysis
        self.update_analysis(assistant_msg, response_time)
        
        # Reset UI
        self.is_generating = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send")
        
        # Emit signal
        self.response_received.emit(response_text, empathy_score)
        
    def generate_mock_response(self, user_message: str) -> str:
        """Generate mock empathetic response"""
        # This is a placeholder - replace with actual model
        responses = {
            "sad": "I can sense that you're going through a difficult time. It's completely natural to feel this way. Would you like to talk more about what's troubling you?",
            "angry": "I understand you're feeling frustrated right now. Those feelings are valid, and I'm here to listen without judgment. What's been bothering you the most?",
            "happy": "It's wonderful to hear such positivity in your message! Your joy is contagious. What's been bringing you this happiness?",
            "default": "Thank you for sharing that with me. I'm here to listen and support you. Can you tell me more about how you're feeling?"
        }
        
        # Simple emotion detection
        emotion = "default"
        lower_msg = user_message.lower()
        if any(word in lower_msg for word in ["sad", "depressed", "down", "unhappy"]):
            emotion = "sad"
        elif any(word in lower_msg for word in ["angry", "mad", "frustrated", "annoyed"]):
            emotion = "angry"
        elif any(word in lower_msg for word in ["happy", "joy", "excited", "great"]):
            emotion = "happy"
            
        return responses.get(emotion, responses["default"])
        
    def calculate_mock_empathy_score(self, response: str) -> float:
        """Calculate mock empathy score"""
        # Placeholder scoring
        empathy_keywords = [
            "understand", "feel", "hear", "listen", "support",
            "valid", "natural", "sorry", "appreciate", "acknowledge"
        ]
        
        word_count = len(response.split())
        keyword_count = sum(1 for word in empathy_keywords if word in response.lower())
        
        score = min(1.0, keyword_count / 5.0)
        return round(score, 2)
        
    def add_message_to_display(self, message: ChatMessage):
        """Add message to chat display"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Format based on role
        if message.role == "user":
            color = QColor(50, 100, 200)
            prefix = "You: "
        else:
            color = QColor(50, 150, 50)
            prefix = "Assistant: "
            
        # Add timestamp
        time_format = QTextCharFormat()
        time_format.setForeground(QColor(150, 150, 150))
        cursor.insertText(f"[{message.timestamp.strftime('%H:%M:%S')}] ", time_format)
        
        # Add message
        msg_format = QTextCharFormat()
        msg_format.setForeground(color)
        msg_format.setFontWeight(QFont.Weight.Bold)
        cursor.insertText(prefix, msg_format)
        
        default_format = QTextCharFormat()
        cursor.insertText(message.content + "\n\n", default_format)
        
        # Scroll to bottom
        self.chat_display.ensureCursorVisible()
        
    def update_analysis(self, message: ChatMessage, response_time: float):
        """Update analysis panel with message metrics"""
        # Empathy score
        if message.empathy_score is not None:
            self.empathy_score_label.setText(f"{message.empathy_score:.2f}")
            
            # Update dimensions (mock data)
            self.empathy_dimensions["Cognitive"].setText(f"{message.empathy_score * 0.8:.2f}")
            self.empathy_dimensions["Emotional"].setText(f"{message.empathy_score * 1.1:.2f}")
            self.empathy_dimensions["Compassionate"].setText(f"{message.empathy_score * 0.9:.2f}")
            
        # Response metrics
        self.response_time_label.setText(f"Response Time: {response_time:.2f}s")
        word_count = len(message.content.split())
        self.word_count_label.setText(f"Word Count: {word_count}")
        
        # Detected emotions (mock)
        self.detected_emotions.clear()
        emotions = ["Empathy: High", "Tone: Supportive", "Clarity: Good"]
        for emotion in emotions:
            self.detected_emotions.addItem(emotion)
            
        # Suggestions
        suggestions = [
            "✓ Good use of empathetic language",
            "→ Consider asking more open-ended questions",
            "→ Try reflecting the user's emotions more explicitly"
        ]
        self.suggestions_list.setText("\n".join(suggestions))
        
    def clear_conversation(self):
        """Clear the conversation history"""
        self.conversation_history.clear()
        self.chat_display.clear()
        self.empathy_score_label.setText("N/A")
        self.detected_emotions.clear()
        self.suggestions_list.clear()
        
    def save_conversation(self):
        """Save conversation to file"""
        if not self.conversation_history:
            return
            
        # Convert to serializable format
        conversation_data = [msg.to_dict() for msg in self.conversation_history]
        
        # Emit signal
        self.conversation_saved.emit(conversation_data)
        
        # Also save to file (optional)
        filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(conversation_data, f, indent=2)
            logger.info(f"Conversation saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            
    def on_model_changed(self, model_name: str):
        """Handle model selection change"""
        self.current_model = model_name
        logger.info(f"Selected model: {model_name}")
        
    def on_emotion_changed(self, emotion: str):
        """Handle emotion selection change"""
        self.current_emotion = emotion.lower()
        logger.info(f"Selected emotion: {emotion}")
        
    def on_intensity_changed(self, value: int):
        """Handle intensity slider change"""
        self.emotion_intensity = value
        self.intensity_label.setText(str(value))
        
    def on_empathy_toggled(self, checked: bool):
        """Handle empathy mode toggle"""
        self.enable_empathy_mode = checked
        logger.info(f"Empathy mode: {'enabled' if checked else 'disabled'}") 