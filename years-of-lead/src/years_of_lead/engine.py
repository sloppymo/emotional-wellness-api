"""
Core game engine for Years of Lead
Implements the turn-based game loop and event system
"""

import uuid
import time
from typing import Dict, List, Any, Optional
from enum import Enum
from loguru import logger

from game.state import GameState
from game.events import EventManager
from game.factions import FactionManager


class GameStatus(Enum):
    """Game status enum"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class GameEngine:
    """
    Core game engine for Years of Lead
    Manages the turn-based loop, game state, and event processing
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize game engine with optional configuration"""
        self.game_id = str(uuid.uuid4())
        self.status = GameStatus.INITIALIZING
        self.current_turn = 0
        self.max_turns = config.get("max_turns", 100) if config else 100
        self.start_time = time.time()
        
        # Initialize core components
        self.state = GameState(game_id=self.game_id)
        self.event_manager = EventManager()
        self.faction_manager = FactionManager()
        
        logger.info(f"Game engine initialized with ID: {self.game_id}")
    
    async def initialize_game(self, scenario_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Initialize a new game with the given scenario configuration"""
        logger.info(f"Initializing new game with scenario: {scenario_config}")
        
        # Set up initial world state
        await self.state.initialize(scenario_config)
        
        # Initialize factions
        await self.faction_manager.initialize(self.state, scenario_config)
        
        # Register core event listeners
        self._register_event_listeners()
        
        # Set game to running state
        self.status = GameStatus.RUNNING
        
        # Trigger game start event
        self.event_manager.trigger("game.started", {
            "game_id": self.game_id,
            "start_time": self.start_time,
            "scenario": scenario_config
        })
        
        return self.get_game_info()
    
    def _register_event_listeners(self):
        """Register core event listeners"""
        # Register turn-related events
        self.event_manager.register("turn.start", self._on_turn_start)
        self.event_manager.register("turn.end", self._on_turn_end)
        
        # Register faction-related events
        self.event_manager.register("faction.action", self._on_faction_action)
        
        # Register game state events
        self.event_manager.register("game.paused", self._on_game_paused)
        self.event_manager.register("game.resumed", self._on_game_resumed)
    
    async def process_turn(self) -> Dict[str, Any]:
        """Process a single game turn"""
        if self.status != GameStatus.RUNNING:
            logger.warning(f"Cannot process turn, game is in {self.status} state")
            return {"error": f"Game is in {self.status} state"}
        
        # Increment turn counter
        self.current_turn += 1
        logger.info(f"Processing turn {self.current_turn}/{self.max_turns}")
        
        # Trigger turn start event
        turn_data = {
            "game_id": self.game_id,
            "turn": self.current_turn,
            "max_turns": self.max_turns
        }
        self.event_manager.trigger("turn.start", turn_data)
        
        # Process faction actions
        faction_results = await self.faction_manager.process_turn(self.state, self.current_turn)
        
        # Update game state based on actions
        await self.state.update(faction_results)
        
        # Trigger turn end event
        self.event_manager.trigger("turn.end", turn_data)
        
        # Check for game end conditions
        if self.current_turn >= self.max_turns:
            logger.info("Maximum turns reached, ending game")
            await self.end_game("maximum_turns_reached")
        elif await self.state.check_victory_conditions():
            logger.info("Victory conditions met, ending game")
            await self.end_game("victory_conditions_met")
        
        return {
            "turn": self.current_turn,
            "faction_results": faction_results,
            "state_summary": self.state.get_summary()
        }
    
    async def end_game(self, reason: str) -> Dict[str, Any]:
        """End the current game with the specified reason"""
        logger.info(f"Ending game {self.game_id}, reason: {reason}")
        
        # Set game status to completed
        self.status = GameStatus.COMPLETED
        
        # Calculate game duration
        duration = time.time() - self.start_time
        
        # Trigger game end event
        end_data = {
            "game_id": self.game_id,
            "reason": reason,
            "duration": duration,
            "turns": self.current_turn,
            "state_summary": self.state.get_summary()
        }
        self.event_manager.trigger("game.ended", end_data)
        
        return end_data
    
    async def pause_game(self) -> Dict[str, Any]:
        """Pause the current game"""
        if self.status == GameStatus.RUNNING:
            self.status = GameStatus.PAUSED
            logger.info(f"Game {self.game_id} paused")
            self.event_manager.trigger("game.paused", {"game_id": self.game_id})
        
        return self.get_game_info()
    
    async def resume_game(self) -> Dict[str, Any]:
        """Resume the current game"""
        if self.status == GameStatus.PAUSED:
            self.status = GameStatus.RUNNING
            logger.info(f"Game {self.game_id} resumed")
            self.event_manager.trigger("game.resumed", {"game_id": self.game_id})
        
        return self.get_game_info()
    
    async def perform_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a player action in the game"""
        # Validate action
        if not self._validate_action(action_data):
            return {"error": "Invalid action data"}
        
        # Process the action in the game state
        result = await self.state.process_action(action_data)
        
        # Trigger action event
        self.event_manager.trigger("player.action", {
            "game_id": self.game_id,
            "turn": self.current_turn,
            "action": action_data,
            "result": result
        })
        
        return result
    
    def _validate_action(self, action_data: Dict[str, Any]) -> bool:
        """Validate a player action"""
        # TODO: Implement proper action validation
        return True
    
    def get_game_info(self) -> Dict[str, Any]:
        """Get current game information"""
        return {
            "game_id": self.game_id,
            "status": self.status.value,
            "current_turn": self.current_turn,
            "max_turns": self.max_turns,
            "start_time": self.start_time,
            "state_summary": self.state.get_summary() if self.state else {}
        }
    
    async def save_game(self) -> Dict[str, Any]:
        """Save the current game state"""
        # TODO: Implement game saving to database
        logger.info(f"Saving game {self.game_id}")
        return {"message": "Game save functionality will be implemented"}
    
    async def load_game(self, game_id: str) -> Dict[str, Any]:
        """Load a saved game state"""
        # TODO: Implement game loading from database
        logger.info(f"Loading game {game_id}")
        return {"message": "Game load functionality will be implemented"}
    
    # Event handlers
    def _on_turn_start(self, data: Dict[str, Any]):
        """Handle turn start event"""
        logger.debug(f"Turn {data['turn']} started")
    
    def _on_turn_end(self, data: Dict[str, Any]):
        """Handle turn end event"""
        logger.debug(f"Turn {data['turn']} ended")
    
    def _on_faction_action(self, data: Dict[str, Any]):
        """Handle faction action event"""
        logger.debug(f"Faction {data.get('faction_id')} performed action: {data.get('action_type')}")
    
    def _on_game_paused(self, data: Dict[str, Any]):
        """Handle game paused event"""
        logger.debug(f"Game {data['game_id']} paused")
    
    def _on_game_resumed(self, data: Dict[str, Any]):
        """Handle game resumed event"""
        logger.debug(f"Game {data['game_id']} resumed")
