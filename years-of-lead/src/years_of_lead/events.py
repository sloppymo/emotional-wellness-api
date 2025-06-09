"""
Event management system for Years of Lead
Handles event dispatching, listeners, and event processing
"""

from typing import Dict, List, Any, Callable
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
