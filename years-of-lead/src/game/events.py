"""
Event management system for Years of Lead
Handles event dispatching, listeners, and event processing
"""

from typing import Dict, List, Any, Callable, Optional
import time
from loguru import logger


class EventManager:
    """
    Event manager for the game engine
    
    Provides a publish-subscribe pattern for game events,
    allowing components to listen for and react to events
    generated during gameplay.
    """
    
    def __init__(self):
        """Initialize event manager"""
        self.listeners = {}
        self.event_history = []
        self.max_history = 1000  # Maximum number of events to keep in history
    
    def register(self, event_type: str, listener: Callable) -> None:
        """
        Register a listener function for a specific event type
        
        Args:
            event_type: The type of event to listen for
            listener: Function to call when the event occurs
        """
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        
        self.listeners[event_type].append(listener)
        logger.debug(f"Registered listener for event type: {event_type}")
    
    def unregister(self, event_type: str, listener: Callable) -> bool:
        """
        Unregister a listener function for a specific event type
        
        Args:
            event_type: The event type to unregister from
            listener: The listener function to remove
            
        Returns:
            bool: True if listener was removed, False otherwise
        """
        if event_type in self.listeners and listener in self.listeners[event_type]:
            self.listeners[event_type].remove(listener)
            logger.debug(f"Unregistered listener for event type: {event_type}")
            return True
        return False
    
    def trigger(self, event_type: str, data: Dict[str, Any] = None) -> None:
        """
        Trigger an event, notifying all listeners
        
        Args:
            event_type: The type of event to trigger
            data: Event data to pass to listeners
        """
        event_data = data or {}
        event_time = time.time()
        
        # Create event record
        event = {
            "type": event_type,
            "timestamp": event_time,
            "data": event_data
        }
        
        # Add to history
        self.event_history.append(event)
        
        # Trim history if necessary
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # Notify listeners
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                try:
                    listener(event_data)
                except Exception as e:
                    logger.error(f"Error in event listener for {event_type}: {e}")
        
        # Special case for wildcard listeners
        if "*" in self.listeners:
            for listener in self.listeners["*"]:
                try:
                    listener({"type": event_type, **event_data})
                except Exception as e:
                    logger.error(f"Error in wildcard event listener for {event_type}: {e}")
        
        logger.debug(f"Triggered event: {event_type}")
    
    def get_events(self, event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get events from history, optionally filtered by type
        
        Args:
            event_type: Optional filter for event type
            limit: Maximum number of events to return
            
        Returns:
            List of event records
        """
        if event_type is None:
            return self.event_history[-limit:]
        
        filtered_events = [e for e in self.event_history if e["type"] == event_type]
        return filtered_events[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history"""
        self.event_history = []
        logger.debug("Event history cleared")


class GameEvent:
    """Base class for structured game events"""
    
    def __init__(self, event_type: str, data: Dict[str, Any] = None):
        """
        Initialize a game event
        
        Args:
            event_type: The type of event
            data: Event data
        """
        self.type = event_type
        self.data = data or {}
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation"""
        return {
            "type": self.type,
            "timestamp": self.timestamp,
            "data": self.data
        }


# Predefined event types
class EventTypes:
    """Constants for common event types"""
    
    # Game flow events
    GAME_STARTED = "game.started"
    GAME_ENDED = "game.ended"
    GAME_PAUSED = "game.paused"
    GAME_RESUMED = "game.resumed"
    GAME_SAVED = "game.saved"
    GAME_LOADED = "game.loaded"
    
    # Turn events
    TURN_START = "turn.start"
    TURN_END = "turn.end"
    
    # Action events
    PLAYER_ACTION = "player.action"
    FACTION_ACTION = "faction.action"
    
    # Resource events
    RESOURCE_CHANGED = "resource.changed"
    RESOURCE_DEPLETED = "resource.depleted"
    
    # Faction events
    FACTION_CREATED = "faction.created"
    FACTION_DESTROYED = "faction.destroyed"
    FACTION_RELATIONSHIP_CHANGED = "faction.relationship.changed"
    
    # District events
    DISTRICT_CONTROL_CHANGED = "district.control.changed"
    DISTRICT_HEAT_CHANGED = "district.heat.changed"
    
    # Cell events
    CELL_CREATED = "cell.created"
    CELL_COMPROMISED = "cell.compromised"
    CELL_DISBANDED = "cell.disbanded"
    
    # Operation events
    OPERATION_STARTED = "operation.started"
    OPERATION_COMPLETED = "operation.completed"
    OPERATION_FAILED = "operation.failed"
    
    # SYLVA/WREN integration events
    EMOTIONAL_STATE_CHANGED = "emotional.state.changed"
    NARRATIVE_BRANCH_CREATED = "narrative.branch.created"
    SYMBOLIC_PATTERN_DETECTED = "symbolic.pattern.detected"


class EventSystem:
    """
    Narrative event generation system for Years of Lead.
    
    Generates contextual events with descriptions and emotional impacts
    for the game world and agent interactions.
    """
    
    def __init__(self, game_state=None):
        """Initialize the event system"""
        self.game_state = game_state
        self.event_templates = self._initialize_event_templates()
        self.recent_events = []
    
    def _initialize_event_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize event templates for different contexts"""
        return {
            'daily_life': [
                {
                    'description': "You wake up to the sound of helicopters circling overhead",
                    'emotional_impact': {'fear': 0.2, 'anticipation': 0.1},
                    'consequences': {'time_of_day': 'morning', 'location': 'bedroom'}
                },
                {
                    'description': "The morning news reports another crackdown in the university district",
                    'emotional_impact': {'anger': 0.3, 'sadness': 0.2},
                    'consequences': {'unrest_level': 6}
                },
                {
                    'description': "You prepare a simple breakfast while checking for surveillance",
                    'emotional_impact': {'anticipation': 0.1},
                    'consequences': {'location': 'kitchen', 'time_of_day': 'morning'}
                },
                {
                    'description': "Neighbors whisper anxiously about the increased patrols",
                    'emotional_impact': {'fear': 0.2, 'trust': -0.1},
                    'consequences': {'social_tension': 'high'}
                },
                {
                    'description': "You receive a coded message from a fellow resistance member",
                    'emotional_impact': {'anticipation': 0.3, 'trust': 0.2},
                    'consequences': {'has_message': True}
                },
                {
                    'description': "The local market buzzes with rumors of government infiltrators",
                    'emotional_impact': {'fear': 0.3, 'anger': 0.1},
                    'consequences': {'location': 'market', 'paranoia_level': 'high'}
                },
                {
                    'description': "You notice unfamiliar faces watching from across the street",
                    'emotional_impact': {'fear': 0.4, 'surprise': 0.2},
                    'consequences': {'surveillance_risk': 'high'}
                },
                {
                    'description': "A childhood friend mentions seeing you in an old photograph",
                    'emotional_impact': {'joy': 0.3, 'sadness': 0.1},
                    'consequences': {'nostalgia_triggered': True}
                },
                {
                    'description': "The power cuts out suddenly, leaving the block in darkness",
                    'emotional_impact': {'surprise': 0.3, 'fear': 0.2},
                    'consequences': {'power_status': 'off', 'vulnerability': 'high'}
                },
                {
                    'description': "You discover a hidden cache of supplies in an abandoned building",
                    'emotional_impact': {'joy': 0.4, 'anticipation': 0.2},
                    'consequences': {'supplies_found': True, 'hope_level': 'increased'}
                }
            ],
            'resistance_operations': [
                {
                    'description': "Your cell successfully distributes propaganda leaflets across the district",
                    'emotional_impact': {'joy': 0.4, 'anticipation': 0.3},
                    'consequences': {'operation_success': True, 'influence': 5}
                },
                {
                    'description': "Government forces raid a safe house, but find it already evacuated",
                    'emotional_impact': {'relief': 0.3, 'fear': 0.2},
                    'consequences': {'safe_house_status': 'compromised'}
                },
                {
                    'description': "A new recruit shows promising skills in stealth operations",
                    'emotional_impact': {'hope': 0.3, 'trust': 0.2},
                    'consequences': {'recruitment_success': True}
                },
                {
                    'description': "Intelligence suggests government forces are planning a major sweep",
                    'emotional_impact': {'fear': 0.4, 'anticipation': 0.3},
                    'consequences': {'threat_level': 'high', 'planning_required': True}
                }
            ],
            'trauma_events': [
                {
                    'description': "You witness government forces brutally dispersing peaceful protesters",
                    'emotional_impact': {'fear': 0.7, 'anger': 0.6, 'sadness': 0.5},
                    'type': 'violence_witnessed',
                    'severity': 0.8,
                    'consequences': {'trauma_witnessed': True, 'trust_in_system': -0.8}
                },
                {
                    'description': "A trusted comrade is arrested and doesn't return from interrogation",
                    'emotional_impact': {'sadness': 0.8, 'fear': 0.6, 'anger': 0.7},
                    'type': 'loss_of_comrade',
                    'severity': 0.9,
                    'consequences': {'comrade_lost': True, 'operation_compromised': True}
                },
                {
                    'description': "You discover that someone you trusted has been informing the authorities",
                    'emotional_impact': {'anger': 0.8, 'trust': -0.9, 'sadness': 0.4},
                    'type': 'betrayal',
                    'severity': 0.8,
                    'consequences': {'trust_betrayed': True, 'network_compromised': True}
                }
            ]
        }
    
    def generate_event(self, event_category: str, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Generate a contextual event based on category and current context.
        
        Args:
            event_category: Category of event to generate ('daily_life', 'resistance_operations', etc.)
            context: Current game context to influence event selection
            
        Returns:
            Generated event with description, emotional impact, and consequences
        """
        if event_category not in self.event_templates:
            return None
        
        context = context or {}
        templates = self.event_templates[event_category]
        
        # Simple template selection - in a full implementation, this would be much more sophisticated
        import random
        template = random.choice(templates)
        
        # Create event from template
        event = {
            'category': event_category,
            'description': template['description'],
            'emotional_impact': template.get('emotional_impact', {}),
            'consequences': template.get('consequences', {}),
            'type': template.get('type', 'general'),
            'severity': template.get('severity', 0.3),
            'context': context
        }
        
        # Apply context-based modifications
        event = self._apply_context_modifications(event, context)
        
        # Store in recent events
        self.recent_events.append(event)
        if len(self.recent_events) > 50:  # Keep only recent events
            self.recent_events = self.recent_events[-50:]
        
        return event
    
    def _apply_context_modifications(self, event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply context-based modifications to generated events.
        This allows events to be influenced by current game state.
        """
        # Modify emotional impact based on context
        if context.get('time_of_day') == 'night':
            # Night events are more fearful
            if 'fear' in event['emotional_impact']:
                event['emotional_impact']['fear'] *= 1.2
        
        if context.get('location') == 'government_quarter':
            # Events in government quarter are more tense
            event['emotional_impact']['fear'] = event['emotional_impact'].get('fear', 0) + 0.1
            event['emotional_impact']['anticipation'] = event['emotional_impact'].get('anticipation', 0) + 0.1
        
        # Modify consequences based on context
        if context.get('recent_events'):
            # If recent events included violence, increase fear in current event
            recent_violence = any('violence' in str(recent_event).lower() 
                                for recent_event in context['recent_events'])
            if recent_violence:
                event['emotional_impact']['fear'] = event['emotional_impact'].get('fear', 0) + 0.2
        
        return event
    
    def get_recent_events(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent events for context"""
        return self.recent_events[-count:] if self.recent_events else []
