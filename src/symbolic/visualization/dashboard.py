"""
Visualization dashboard for VELURIA and ROOT systems.

This module provides visualization capabilities for:
1. Crisis intervention analytics (VELURIA)
2. Longitudinal analysis (ROOT)
3. Pattern recognition insights
4. Predictive analytics
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from models.emotional_state import EmotionalState, SafetyStatus, InterventionRecord
from src.symbolic.veluria.pattern_detection import PatternAnalysis, RiskPrediction
from src.symbolic.root import TrendAnalysis, PatternRecognitionResult

class Dashboard:
    """Visualization dashboard for emotional wellness analytics"""
    
    def __init__(self):
        """Initialize the dashboard"""
        self.color_scheme = {
            "primary": "#2C3E50",
            "secondary": "#E74C3C",
            "accent": "#3498DB",
            "success": "#2ECC71",
            "warning": "#F1C40F",
            "danger": "#E74C3C",
            "info": "#3498DB",
            "light": "#ECF0F1",
            "dark": "#2C3E50"
        }
        
        self.theme = {
            "background": "#FFFFFF",
            "text": "#2C3E50",
            "grid": "#ECF0F1"
        }
    
    def create_crisis_dashboard(
        self,
        pattern_analysis: PatternAnalysis,
        risk_prediction: RiskPrediction,
        intervention_history: List[InterventionRecord]
    ) -> go.Figure:
        """
        Create crisis intervention analytics dashboard.
        
        Args:
            pattern_analysis: Crisis pattern analysis results
            risk_prediction: Risk prediction results
            intervention_history: Historical intervention records
            
        Returns:
            Plotly figure containing the dashboard
        """
        # Create subplot grid
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                "Risk Level Timeline",
                "Intervention Effectiveness",
                "Pattern Distribution",
                "Warning Signs",
                "Risk Factors",
                "Predicted Risk"
            ),
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # Add risk timeline
        self._add_risk_timeline(fig, intervention_history, 1, 1)
        
        # Add intervention effectiveness
        self._add_intervention_effectiveness(fig, pattern_analysis, 1, 2)
        
        # Add pattern distribution
        self._add_pattern_distribution(fig, pattern_analysis, 2, 1)
        
        # Add warning signs
        self._add_warning_signs(fig, risk_prediction, 2, 2)
        
        # Add risk factors
        self._add_risk_factors(fig, pattern_analysis, 3, 1)
        
        # Add predicted risk
        self._add_predicted_risk(fig, risk_prediction, 3, 2)
        
        # Update layout
        fig.update_layout(
            height=900,
            showlegend=True,
            template="plotly_white",
            title_text="Crisis Intervention Analytics Dashboard",
            title_x=0.5,
            paper_bgcolor=self.theme["background"],
            plot_bgcolor=self.theme["background"],
            font_color=self.theme["text"]
        )
        
        return fig
    
    def create_longitudinal_dashboard(
        self,
        trend_analysis: TrendAnalysis,
        pattern_recognition: PatternRecognitionResult,
        emotional_history: List[EmotionalState]
    ) -> go.Figure:
        """
        Create longitudinal analysis dashboard.
        
        Args:
            trend_analysis: Emotional trend analysis results
            pattern_recognition: Pattern recognition results
            emotional_history: Historical emotional states
            
        Returns:
            Plotly figure containing the dashboard
        """
        # Create subplot grid
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                "Emotional State Timeline",
                "Pattern Recognition",
                "Trend Analysis",
                "Stability Metrics",
                "Correlations",
                "Forecasting"
            ),
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # Add emotional timeline
        self._add_emotional_timeline(fig, emotional_history, 1, 1)
        
        # Add pattern recognition
        self._add_pattern_recognition(fig, pattern_recognition, 1, 2)
        
        # Add trend analysis
        self._add_trend_analysis(fig, trend_analysis, 2, 1)
        
        # Add stability metrics
        self._add_stability_metrics(fig, trend_analysis, 2, 2)
        
        # Add correlations
        self._add_correlations(fig, pattern_recognition, 3, 1)
        
        # Add forecasting
        self._add_forecasting(fig, trend_analysis, 3, 2)
        
        # Update layout
        fig.update_layout(
            height=900,
            showlegend=True,
            template="plotly_white",
            title_text="Longitudinal Analysis Dashboard",
            title_x=0.5,
            paper_bgcolor=self.theme["background"],
            plot_bgcolor=self.theme["background"],
            font_color=self.theme["text"]
        )
        
        return fig
    
    def _add_risk_timeline(
        self,
        fig: go.Figure,
        intervention_history: List[InterventionRecord],
        row: int,
        col: int
    ):
        """Add risk timeline plot"""
        if not intervention_history:
            return
        
        # Extract data
        timestamps = [record.timestamp for record in intervention_history]
        risk_scores = [record.risk_score for record in intervention_history]
        
        # Create line plot
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=risk_scores,
                mode="lines+markers",
                name="Risk Score",
                line=dict(color=self.color_scheme["primary"]),
                marker=dict(color=self.color_scheme["primary"])
            ),
            row=row, col=col
        )
        
        # Add intervention points
        for record in intervention_history:
            if record.level >= 2:  # Significant interventions
                fig.add_trace(
                    go.Scatter(
                        x=[record.timestamp],
                        y=[record.risk_score],
                        mode="markers",
                        name=f"Level {record.level} Intervention",
                        marker=dict(
                            color=self.color_scheme["warning"],
                            size=12,
                            symbol="star"
                        )
                    ),
                    row=row, col=col
                )
        
        # Update layout
        fig.update_xaxes(title_text="Time", row=row, col=col)
        fig.update_yaxes(title_text="Risk Score", row=row, col=col)
    
    def _add_intervention_effectiveness(
        self,
        fig: go.Figure,
        pattern_analysis: PatternAnalysis,
        row: int,
        col: int
    ):
        """Add intervention effectiveness plot"""
        if not pattern_analysis.intervention_effectiveness:
            return
        
        # Extract data
        interventions = list(pattern_analysis.intervention_effectiveness.keys())
        effectiveness = list(pattern_analysis.intervention_effectiveness.values())
        
        # Create bar plot
        fig.add_trace(
            go.Bar(
                x=interventions,
                y=effectiveness,
                marker_color=self.color_scheme["accent"]
            ),
            row=row, col=col
        )
        
        # Update layout
        fig.update_xaxes(title_text="Intervention Type", row=row, col=col)
        fig.update_yaxes(title_text="Effectiveness Score", row=row, col=col)
    
    def _add_pattern_distribution(
        self,
        fig: go.Figure,
        pattern_analysis: PatternAnalysis,
        row: int,
        col: int
    ):
        """Add pattern distribution plot"""
        if not pattern_analysis.detected_patterns:
            return
        
        # Count pattern types
        pattern_counts = {}
        for pattern in pattern_analysis.detected_patterns:
            pattern_type = pattern["type"]
            pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1
        
        # Create pie chart
        fig.add_trace(
            go.Pie(
                labels=list(pattern_counts.keys()),
                values=list(pattern_counts.values()),
                marker=dict(colors=[self.color_scheme["primary"],
                                  self.color_scheme["secondary"],
                                  self.color_scheme["accent"]])
            ),
            row=row, col=col
        )
    
    def _add_warning_signs(
        self,
        fig: go.Figure,
        risk_prediction: RiskPrediction,
        row: int,
        col: int
    ):
        """Add warning signs plot"""
        if not risk_prediction.warning_signs:
            return
        
        # Extract data
        warning_types = [w["type"] for w in risk_prediction.warning_signs]
        severities = [w["severity"] for w in risk_prediction.warning_signs]
        
        # Map severities to numeric values
        severity_map = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }
        severity_scores = [severity_map[s] for s in severities]
        
        # Create scatter plot
        fig.add_trace(
            go.Scatter(
                x=warning_types,
                y=severity_scores,
                mode="markers",
                marker=dict(
                    size=15,
                    color=severity_scores,
                    colorscale="RdYlBu_r",
                    showscale=True
                )
            ),
            row=row, col=col
        )
        
        # Update layout
        fig.update_xaxes(title_text="Warning Type", row=row, col=col)
        fig.update_yaxes(
            title_text="Severity",
            ticktext=["Low", "Medium", "High", "Critical"],
            tickvals=[1, 2, 3, 4],
            row=row, col=col
        )
    
    def _add_risk_factors(
        self,
        fig: go.Figure,
        pattern_analysis: PatternAnalysis,
        row: int,
        col: int
    ):
        """Add risk factors plot"""
        if not pattern_analysis.risk_factors:
            return
        
        # Extract data
        factors = [f["factor"] for f in pattern_analysis.risk_factors]
        importance = [f["importance"] for f in pattern_analysis.risk_factors]
        
        # Create horizontal bar plot
        fig.add_trace(
            go.Bar(
                x=importance,
                y=factors,
                orientation="h",
                marker_color=self.color_scheme["secondary"]
            ),
            row=row, col=col
        )
        
        # Update layout
        fig.update_xaxes(title_text="Importance Score", row=row, col=col)
        fig.update_yaxes(title_text="Risk Factor", row=row, col=col)
    
    def _add_predicted_risk(
        self,
        fig: go.Figure,
        risk_prediction: RiskPrediction,
        row: int,
        col: int
    ):
        """Add predicted risk plot"""
        # Create gauge chart
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=risk_prediction.risk_score,
                gauge={
                    "axis": {"range": [0, 1]},
                    "bar": {"color": self.color_scheme["primary"]},
                    "steps": [
                        {"range": [0, 0.3], "color": self.color_scheme["success"]},
                        {"range": [0.3, 0.7], "color": self.color_scheme["warning"]},
                        {"range": [0.7, 1], "color": self.color_scheme["danger"]}
                    ]
                },
                title={"text": f"Confidence: {risk_prediction.confidence:.2f}"}
            ),
            row=row, col=col
        )
    
    def _add_emotional_timeline(
        self,
        fig: go.Figure,
        emotional_history: List[EmotionalState],
        row: int,
        col: int
    ):
        """Add emotional state timeline"""
        if not emotional_history:
            return
        
        # Extract data
        timestamps = [state.timestamp for state in emotional_history]
        valences = [state.valence for state in emotional_history]
        arousals = [state.arousal for state in emotional_history]
        
        # Add valence line
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=valences,
                mode="lines",
                name="Valence",
                line=dict(color=self.color_scheme["primary"])
            ),
            row=row, col=col
        )
        
        # Add arousal line
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=arousals,
                mode="lines",
                name="Arousal",
                line=dict(color=self.color_scheme["secondary"])
            ),
            row=row, col=col
        )
        
        # Update layout
        fig.update_xaxes(title_text="Time", row=row, col=col)
        fig.update_yaxes(title_text="Emotional State", row=row, col=col)
    
    def _add_pattern_recognition(
        self,
        fig: go.Figure,
        pattern_recognition: PatternRecognitionResult,
        row: int,
        col: int
    ):
        """Add pattern recognition plot"""
        if not pattern_recognition.pattern_significance:
            return
        
        # Extract data
        patterns = list(pattern_recognition.pattern_significance.keys())
        significance = list(pattern_recognition.pattern_significance.values())
        
        # Create radar plot
        fig.add_trace(
            go.Scatterpolar(
                r=significance,
                theta=patterns,
                fill="toself",
                name="Pattern Significance"
            ),
            row=row, col=col
        )
    
    def _add_trend_analysis(
        self,
        fig: go.Figure,
        trend_analysis: TrendAnalysis,
        row: int,
        col: int
    ):
        """Add trend analysis plot"""
        if not trend_analysis.primary_trends:
            return
        
        # Extract data
        trend_types = [t["type"] for t in trend_analysis.primary_trends]
        magnitudes = [t["magnitude"] for t in trend_analysis.primary_trends]
        directions = [t["direction"] for t in trend_analysis.primary_trends]
        
        # Create scatter plot
        for i, trend_type in enumerate(trend_types):
            direction = directions[i]
            color = (self.color_scheme["success"] if direction == "increasing"
                    else self.color_scheme["danger"])
            
            fig.add_trace(
                go.Scatter(
                    x=[trend_type],
                    y=[magnitudes[i]],
                    mode="markers+text",
                    name=f"{trend_type} ({direction})",
                    marker=dict(size=20, color=color),
                    text=[direction],
                    textposition="top center"
                ),
                row=row, col=col
            )
        
        # Update layout
        fig.update_xaxes(title_text="Trend Type", row=row, col=col)
        fig.update_yaxes(title_text="Magnitude", row=row, col=col)
    
    def _add_stability_metrics(
        self,
        fig: go.Figure,
        trend_analysis: TrendAnalysis,
        row: int,
        col: int
    ):
        """Add stability metrics plot"""
        if not trend_analysis.stability_metrics:
            return
        
        # Extract data
        metrics = list(trend_analysis.stability_metrics.keys())
        values = list(trend_analysis.stability_metrics.values())
        
        # Create bar plot
        fig.add_trace(
            go.Bar(
                x=metrics,
                y=values,
                marker_color=self.color_scheme["accent"]
            ),
            row=row, col=col
        )
        
        # Update layout
        fig.update_xaxes(title_text="Metric", row=row, col=col)
        fig.update_yaxes(title_text="Stability Score", row=row, col=col)
    
    def _add_correlations(
        self,
        fig: go.Figure,
        pattern_recognition: PatternRecognitionResult,
        row: int,
        col: int
    ):
        """Add correlations plot"""
        if not pattern_recognition.correlations:
            return
        
        # Extract data
        variables = list(pattern_recognition.correlations.keys())
        correlations = list(pattern_recognition.correlations.values())
        
        # Create heatmap
        fig.add_trace(
            go.Heatmap(
                z=[correlations],
                x=variables,
                y=["Correlation"],
                colorscale="RdBu",
                zmin=-1,
                zmax=1
            ),
            row=row, col=col
        )
    
    def _add_forecasting(
        self,
        fig: go.Figure,
        trend_analysis: TrendAnalysis,
        row: int,
        col: int
    ):
        """Add forecasting plot"""
        if not trend_analysis.forecast:
            return
        
        # Extract data
        forecast_range = range(len(trend_analysis.forecast["valence"]))
        valence_forecast = trend_analysis.forecast["valence"]
        arousal_forecast = trend_analysis.forecast["arousal"]
        
        # Add valence forecast
        fig.add_trace(
            go.Scatter(
                x=forecast_range,
                y=valence_forecast,
                mode="lines",
                name="Valence Forecast",
                line=dict(
                    color=self.color_scheme["primary"],
                    dash="dash"
                )
            ),
            row=row, col=col
        )
        
        # Add arousal forecast
        fig.add_trace(
            go.Scatter(
                x=forecast_range,
                y=arousal_forecast,
                mode="lines",
                name="Arousal Forecast",
                line=dict(
                    color=self.color_scheme["secondary"],
                    dash="dash"
                )
            ),
            row=row, col=col
        )
        
        # Update layout
        fig.update_xaxes(title_text="Time Steps", row=row, col=col)
        fig.update_yaxes(title_text="Predicted Value", row=row, col=col) 