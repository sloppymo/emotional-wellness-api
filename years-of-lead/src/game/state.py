"""
Game state management for Years of Lead
Handles the core state of the game world, districts, and factions
"""

from typing import Dict, List, Any, Optional
import json
from loguru import logger


class GameState:
    """
    Game state manager for Years of Lead
    Maintains the current state of the game world, including
    districts, factions, resources, and other game elements
    """
    
    def __init__(self, game_id: str):
        """Initialize game state with game ID"""
        self.game_id = game_id
        self.world_data = {}
        self.factions = {}
        self.districts = {}
        self.players = {}
        self.resources = {}
        self.heat_levels = {}
        self.turn_history = []
        self.events = []
        
        logger.info(f"Game state initialized for game {game_id}")
    
    async def initialize(self, scenario_config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize game state with scenario configuration"""
        scenario_name = scenario_config.get("name", "default") if scenario_config else "default"
        logger.info(f"Initializing game state with scenario: {scenario_name}")
        
        # Initialize districts
        await self._initialize_districts(scenario_config)
        
        # Initialize resources
        await self._initialize_resources(scenario_config)
        
        # Initialize heat levels
        await self._initialize_heat_levels()
        
        # Save initial state to history
        self._save_state_to_history(0, "game_initialized")
    
    async def _initialize_districts(self, scenario_config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize game districts"""
        # Default districts if no scenario provided
        default_districts = [
            {"id": "downtown", "name": "Downtown", "population": 250000, "security_level": 8},
            {"id": "industrial", "name": "Industrial Zone", "population": 120000, "security_level": 5},
            {"id": "suburbs", "name": "Suburbs", "population": 350000, "security_level": 6},
            {"id": "university", "name": "University District", "population": 80000, "security_level": 4},
            {"id": "government", "name": "Government Quarter", "population": 40000, "security_level": 10}
        ]
        
        districts_config = scenario_config.get("districts", default_districts) if scenario_config else default_districts
        
        for district in districts_config:
            district_id = district["id"]
            self.districts[district_id] = {
                "id": district_id,
                "name": district.get("name", district_id),
                "population": district.get("population", 100000),
                "security_level": district.get("security_level", 5),
                "control": {},  # Faction control percentages
                "facilities": district.get("facilities", []),
                "events": []
            }
        
        logger.info(f"Initialized {len(self.districts)} districts")
    
    async def _initialize_resources(self, scenario_config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize game resources"""
        default_resources = {
            "money": 1000,
            "influence": 500,
            "personnel": 10
        }
        
        resources_config = scenario_config.get("initial_resources", default_resources) if scenario_config else default_resources
        self.resources = resources_config
        
        logger.info(f"Initialized resources: {self.resources}")
    
    async def _initialize_heat_levels(self) -> None:
        """Initialize heat levels for districts and factions"""
        # Initialize district heat levels
        for district_id in self.districts:
            self.heat_levels[district_id] = 0
        
        logger.info(f"Initialized heat levels for {len(self.heat_levels)} districts")
    
    async def update(self, faction_results: Dict[str, Any]) -> None:
        """Update game state based on faction action results"""
        # Process faction results and update state
        for faction_id, results in faction_results.items():
            if faction_id in self.factions:
                # Update faction state
                for key, value in results.get("faction_updates", {}).items():
                    self.factions[faction_id][key] = value
                
                # Process district changes
                for district_id, changes in results.get("district_changes", {}).items():
                    if district_id in self.districts:
                        for key, value in changes.items():
                            self.districts[district_id][key] = value
                
                # Update heat levels
                for district_id, heat_change in results.get("heat_changes", {}).items():
                    if district_id in self.heat_levels:
                        self.heat_levels[district_id] += heat_change
                
                # Add events
                for event in results.get("events", []):
                    self.events.append(event)
        
        # Save updated state to history
        turn = faction_results.get("turn", len(self.turn_history))
        self._save_state_to_history(turn, "turn_processed")
    
    async def process_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a player action and update state accordingly"""
        # TODO: Implement action processing
        action_type = action_data.get("type", "unknown")
        logger.info(f"Processing action of type: {action_type}")
        
        # Add action to events
        self.events.append({
            "type": "player_action",
            "action_type": action_type,
            "data": action_data,
            "timestamp": self._get_timestamp()
        })
        
        # Return placeholder result
        return {
            "success": True,
            "action_type": action_type,
            "message": f"Action {action_type} processed successfully"
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current game state"""
        return {
            "game_id": self.game_id,
            "districts_count": len(self.districts),
            "factions_count": len(self.factions),
            "players_count": len(self.players),
            "event_count": len(self.events),
            "resources": self.resources,
            "latest_events": self.events[-5:] if self.events else []
        }
    
    def _save_state_to_history(self, turn: int, reason: str) -> None:
        """Save current state snapshot to history"""
        # Create a deep copy of essential state data
        state_snapshot = {
            "turn": turn,
            "reason": reason,
            "timestamp": self._get_timestamp(),
            "resources": dict(self.resources),
            "heat_levels": dict(self.heat_levels),
            # Only save summaries of large data structures
            "districts_summary": {d_id: {"name": d["name"], "control": d.get("control", {})} 
                               for d_id, d in self.districts.items()},
            "factions_summary": {f_id: {"name": f.get("name", f_id), "strength": f.get("strength", 0)} 
                              for f_id, f in self.factions.items()}
        }
        
        self.turn_history.append(state_snapshot)
        logger.debug(f"Saved state snapshot for turn {turn}, reason: {reason}")
    
    async def check_victory_conditions(self) -> bool:
        """Check if any victory conditions have been met"""
        # TODO: Implement victory condition checks
        return False
    
    def _get_timestamp(self) -> int:
        """Get current timestamp"""
        import time
        return int(time.time())
