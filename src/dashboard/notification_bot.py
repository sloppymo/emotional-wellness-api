"""
Notification Dashboard Bot for Emotional Wellness API

This module provides a customizable notification bot interface allowing
users to configure which notifications they receive and how they're delivered.
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import json

from ..utils.slack_utils import default_notifier
from ..structured_logging import get_logger
from ..observability import record_span, ComponentName

# Configure logger
logger = get_logger(__name__)

# Available notification categories
NOTIFICATION_CATEGORIES = {
    "symbolic_alerts": {
        "name": "Symbolic Emotional State Alerts",
        "description": "Notifications about symbolic emotional patterns",
        "default": True,
        "subcategories": {
            "rising_patterns": "Rising emotional patterns",
            "falling_patterns": "Falling emotional patterns",
            "stable_patterns": "Stable emotional patterns"
        }
    },
    "system_health": {
        "name": "Metaphorical DevOps Monitoring",
        "description": "System health updates using metaphorical language",
        "default": True,
        "subcategories": {
            "critical_alerts": "Critical system issues",
            "warning_alerts": "Warning-level system issues",
            "health_summaries": "Regular system health summaries"
        }
    },
    "archetype_analytics": {
        "name": "Archetype Distribution Reports",
        "description": "Heatmaps and analytics about emotional archetypes",
        "default": False,
        "subcategories": {
            "daily_heatmaps": "Daily archetype distribution heatmaps",
            "trend_reports": "Archetype trend analysis reports",
            "pattern_shifts": "Major archetype pattern shifts"
        }
    },
    "crisis_coordination": {
        "name": "Crisis Intervention Updates",
        "description": "Coordination updates for crisis intervention",
        "default": True,
        "subcategories": {
            "level1_crises": "Low-severity situations",
            "level2_crises": "Moderate-severity situations",
            "level3_crises": "High-severity situations"
        }
    },
    "weather_reports": {
        "name": "Emotional Weather Reports",
        "description": "Metaphorical weather reports of emotional trends",
        "default": False,
        "subcategories": {
            "daily_forecast": "Daily emotional weather forecasts",
            "weekly_forecast": "Weekly emotional trend projections",
            "weather_alerts": "Significant emotional weather shifts"
        }
    },
    "team_coordination": {
        "name": "Therapist Coordination",
        "description": "Team coordination and case management",
        "default": False,
        "subcategories": {
            "case_assignments": "New case assignments",
            "consultation_requests": "Requests for clinical consultation",
            "shift_reports": "End of shift summary reports"
        }
    },
    "compliance_reports": {
        "name": "HIPAA Compliance Reports",
        "description": "Audit logs and compliance monitoring",
        "default": False,
        "subcategories": {
            "audit_summaries": "Daily audit log summaries",
            "compliance_alerts": "Potential compliance issues",
            "security_updates": "Security and access control changes"
        }
    }
}


class NotificationPreferences:
    """Manages user notification preferences."""
    
    def __init__(self, user_id: str):
        """
        Initialize notification preferences.
        
        Args:
            user_id: Slack user ID
        """
        self.user_id = user_id
        self.preferences = self._load_preferences()
    
    def _load_preferences(self) -> Dict[str, Any]:
        """
        Load user preferences from storage.
        
        Returns:
            Dictionary of user preferences
        """
        # In a real implementation, this would load from a database
        # Here we'll create default preferences
        preferences = {}
        
        # Set up default preferences for each category
        for category_id, category in NOTIFICATION_CATEGORIES.items():
            preferences[category_id] = {
                "enabled": category["default"],
                "subcategories": {}
            }
            
            # Set up subcategories with defaults
            for sub_id, _ in category.get("subcategories", {}).items():
                preferences[category_id]["subcategories"][sub_id] = category["default"]
                
        return preferences
    
    def save_preferences(self) -> bool:
        """
        Save user preferences to storage.
        
        Returns:
            True if successful
        """
        # In a real implementation, this would save to a database
        logger.info(f"Saved notification preferences for user {self.user_id}")
        return True
    
    def update_category(self, category_id: str, enabled: bool) -> Dict[str, Any]:
        """
        Update a notification category.
        
        Args:
            category_id: Category to update
            enabled: Whether it should be enabled
        
        Returns:
            Updated preferences
        """
        if category_id in self.preferences:
            self.preferences[category_id]["enabled"] = enabled
            
            # Update all subcategories as well
            for sub_id in self.preferences[category_id]["subcategories"]:
                self.preferences[category_id]["subcategories"][sub_id] = enabled
                
            self.save_preferences()
            
        return self.preferences
    
    def update_subcategory(self, category_id: str, subcategory_id: str, enabled: bool) -> Dict[str, Any]:
        """
        Update a notification subcategory.
        
        Args:
            category_id: Parent category
            subcategory_id: Subcategory to update
            enabled: Whether it should be enabled
        
        Returns:
            Updated preferences
        """
        if (category_id in self.preferences and 
            subcategory_id in self.preferences[category_id]["subcategories"]):
            self.preferences[category_id]["subcategories"][subcategory_id] = enabled
            self.save_preferences()
            
        return self.preferences
    
    def should_notify(self, category_id: str, subcategory_id: Optional[str] = None) -> bool:
        """
        Check if a notification should be sent based on user preferences.
        
        Args:
            category_id: Category to check
            subcategory_id: Optional subcategory to check
            
        Returns:
            True if the notification should be sent
        """
        if category_id not in self.preferences:
            return False
            
        # Check if category is enabled
        if not self.preferences[category_id]["enabled"]:
            return False
            
        # If no subcategory specified, use category setting
        if not subcategory_id:
            return True
            
        # Check subcategory setting
        return self.preferences[category_id]["subcategories"].get(subcategory_id, False)


class NotificationDashboard:
    """Dashboard for managing notification preferences."""
    
    def __init__(self):
        """Initialize notification dashboard."""
        self._preferences = {}  # Dict of user_id -> NotificationPreferences
        self._logger = get_logger(f"{__name__}.NotificationDashboard")
    
    def get_user_preferences(self, user_id: str) -> NotificationPreferences:
        """
        Get preferences for a specific user.
        
        Args:
            user_id: Slack user ID
            
        Returns:
            User's notification preferences
        """
        if user_id not in self._preferences:
            self._preferences[user_id] = NotificationPreferences(user_id)
            
        return self._preferences[user_id]
    
    @record_span("dashboard.send_settings_message", ComponentName.NOTIFICATION)
    def send_settings_message(self, user_id: str) -> Dict[str, Any]:
        """
        Send notification settings message to a user.
        
        Args:
            user_id: Slack user ID
            
        Returns:
            Response from the Slack webhook
        """
        # Get user preferences
        prefs = self.get_user_preferences(user_id)
        
        # Create settings blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Notification Preferences"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Configure which notifications you receive from the Emotional Wellness API."
                }
            },
            {
                "type": "divider"
            }
        ]
        
        # Add settings for each category
        for category_id, category in NOTIFICATION_CATEGORIES.items():
            # Get current setting
            enabled = prefs.preferences[category_id]["enabled"]
            
            # Create category block
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{category['name']}*\n{category['description']}"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Enabled" if enabled else "Disabled"
                    },
                    "style": "primary" if enabled else "danger",
                    "value": f"toggle_{category_id}_{not enabled}"
                }
            })
            
            # Add subcategories in context block
            subcategory_text = ""
            for sub_id, sub_name in category.get("subcategories", {}).items():
                status = prefs.preferences[category_id]["subcategories"].get(sub_id, False)
                subcategory_text += f"• {sub_name}: {'✅' if status else '❌'}\n"
                
            if subcategory_text:
                blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": subcategory_text
                        }
                    ]
                })
                
        # Add manage subcategories button
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Manage Subcategories"
                    },
                    "value": "manage_subcategories"
                }
            ]
        })
        
        # Add footer
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        })
        
        # Send message to user
        return default_notifier.send_message(
            blocks=blocks,
            text="Notification Preferences",
            channel=user_id  # Direct message to user
        )
    
    @record_span("dashboard.send_subcategory_settings", ComponentName.NOTIFICATION)
    def send_subcategory_settings(self, user_id: str, category_id: str) -> Dict[str, Any]:
        """
        Send subcategory settings for a specific category.
        
        Args:
            user_id: Slack user ID
            category_id: Category to show settings for
            
        Returns:
            Response from the Slack webhook
        """
        # Get user preferences
        prefs = self.get_user_preferences(user_id)
        
        # Check if category exists
        if category_id not in NOTIFICATION_CATEGORIES:
            return {
                "error": f"Category {category_id} not found"
            }
            
        category = NOTIFICATION_CATEGORIES[category_id]
        user_prefs = prefs.preferences[category_id]
        
        # Create blocks for subcategory settings
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{category['name']} Settings"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Configure which types of *{category['name']}* you receive."
                }
            },
            {
                "type": "divider"
            }
        ]
        
        # Add toggle for each subcategory
        for sub_id, sub_name in category.get("subcategories", {}).items():
            enabled = user_prefs["subcategories"].get(sub_id, False)
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": sub_name
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Enabled" if enabled else "Disabled"
                    },
                    "style": "primary" if enabled else "danger",
                    "value": f"toggle_sub_{category_id}_{sub_id}_{not enabled}"
                }
            })
        
        # Add back button
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Back to Main Settings"
                    },
                    "value": "back_to_main"
                }
            ]
        })
        
        # Send message to user
        return default_notifier.send_message(
            blocks=blocks,
            text=f"{category['name']} Notification Settings",
            channel=user_id  # Direct message to user
        )
    
    @record_span("dashboard.handle_interaction", ComponentName.NOTIFICATION) 
    def handle_interaction(self, user_id: str, action_id: str) -> Dict[str, Any]:
        """
        Handle interaction with the dashboard.
        
        Args:
            user_id: Slack user ID
            action_id: Action identifier
            
        Returns:
            Response object
        """
        # Get user preferences
        prefs = self.get_user_preferences(user_id)
        
        # Handle toggle category
        if action_id.startswith("toggle_"):
            parts = action_id.split("_")
            
            if len(parts) == 3:
                # Toggle category
                category_id = parts[1]
                enabled = parts[2].lower() == "true"
                
                prefs.update_category(category_id, enabled)
                return self.send_settings_message(user_id)
                
            elif len(parts) == 4 and parts[1] == "sub":
                # Toggle subcategory
                category_id = parts[2]
                subcategory_id = parts[3]
                enabled = "true" in action_id.lower().split("_")[-1]
                
                prefs.update_subcategory(category_id, subcategory_id, enabled)
                return self.send_subcategory_settings(user_id, category_id)
        
        # Handle manage subcategories
        elif action_id == "manage_subcategories":
            # For now just show first category settings
            # In a real app, this would show category selection first
            first_category = next(iter(NOTIFICATION_CATEGORIES.keys()))
            return self.send_subcategory_settings(user_id, first_category)
        
        # Handle back to main
        elif action_id == "back_to_main":
            return self.send_settings_message(user_id)
            
        # Unknown action
        return {
            "error": f"Unknown action: {action_id}"
        }

# Create singleton instance for app-wide use
dashboard = NotificationDashboard()
