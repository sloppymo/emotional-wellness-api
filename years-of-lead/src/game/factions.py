"""
Faction management system for Years of Lead
Handles faction behaviors, relationships, and AI decision making
"""

from typing import Dict, List, Any, Optional
import random
from loguru import logger


class FactionManager:
    """
    Faction manager for Years of Lead
    
    Manages all factions in the game, their relationships,
    and their AI-driven decision making processes.
    """
    
    def __init__(self):
        """Initialize faction manager"""
        self.factions = {}
        self.relationships = {}
        
    async def initialize(self, game_state, scenario_config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize factions based on scenario configuration
        
        Args:
            game_state: Current game state
            scenario_config: Scenario configuration
        """
        # Default factions if no scenario provided
        default_factions = [
            {
                "id": "anarchists",
                "name": "Radical Anarchists",
                "description": "Decentralized cells focused on direct action and sabotage",
                "strength": 50,
                "ideology": "radical_left",
                "resources": {"money": 500, "influence": 200, "personnel": 30},
                "specialties": ["direct_action", "underground_networks", "sabotage"]
            },
            {
                "id": "thinktanks",
                "name": "Centrist Think Tanks",
                "description": "Policy influencers with media connections",
                "strength": 70,
                "ideology": "centrist",
                "resources": {"money": 2000, "influence": 1000, "personnel": 15},
                "specialties": ["media_influence", "policy_shaping", "research"]
            },
            {
                "id": "corporations",
                "name": "Corporate Lobbies",
                "description": "Financial power brokers with regulatory capture capabilities",
                "strength": 85,
                "ideology": "corporatist",
                "resources": {"money": 5000, "influence": 800, "personnel": 20},
                "specialties": ["financial_pressure", "regulatory_capture", "market_manipulation"]
            },
            {
                "id": "religious",
                "name": "Religious Militias",
                "description": "Ideologically motivated community organizers",
                "strength": 60,
                "ideology": "religious_right",
                "resources": {"money": 1200, "influence": 500, "personnel": 40},
                "specialties": ["recruitment", "community_organizing", "morality_policing"]
            },
            {
                "id": "separatists",
                "name": "Separatist Syndicates",
                "description": "Territorial control focused on independence movements",
                "strength": 65,
                "ideology": "regionalist",
                "resources": {"money": 1500, "influence": 400, "personnel": 35},
                "specialties": ["territorial_control", "resource_extraction", "autonomous_governance"]
            }
        ]
        
        factions_config = scenario_config.get("factions", default_factions) if scenario_config else default_factions
        
        # Initialize faction data
        for faction_data in factions_config:
            faction_id = faction_data["id"]
            self.factions[faction_id] = faction_data
            
        # Initialize relationships between factions
        await self._initialize_relationships()
        
        logger.info(f"Initialized {len(self.factions)} factions")
        
    async def _initialize_relationships(self) -> None:
        """Initialize relationships between factions"""
        faction_ids = list(self.factions.keys())
        
        # Create empty relationship matrix
        for faction_id in faction_ids:
            self.relationships[faction_id] = {}
            
        # Generate initial relationships
        for i, faction_id in enumerate(faction_ids):
            for other_id in faction_ids:
                if faction_id == other_id:
                    continue
                    
                # Skip if relationship is already defined in the opposite direction
                if other_id in self.relationships and faction_id in self.relationships[other_id]:
                    self.relationships[faction_id][other_id] = self.relationships[other_id][faction_id]
                    continue
                
                # Generate relationship value between -100 (enemies) to 100 (allies)
                # Based on ideological differences and other factors
                faction_ideology = self.factions[faction_id].get("ideology", "")
                other_ideology = self.factions[other_id].get("ideology", "")
                
                # Basic ideological compatibility
                base_value = self._calculate_ideological_compatibility(faction_ideology, other_ideology)
                
                # Add some randomness
                random_factor = random.randint(-20, 20)
                
                relationship_value = base_value + random_factor
                relationship_value = max(-100, min(100, relationship_value))  # Clamp to -100 to 100
                
                self.relationships[faction_id][other_id] = relationship_value
        
        logger.debug(f"Initialized faction relationships: {self.relationships}")
        
    def _calculate_ideological_compatibility(self, ideology1: str, ideology2: str) -> int:
        """
        Calculate base compatibility between two ideologies
        
        Returns value from -80 (opposed) to 80 (aligned)
        """
        # Ideology compatibility matrix (simplified)
        compatibility = {
            "radical_left": {
                "radical_left": 80,
                "centrist": -40,
                "corporatist": -80,
                "religious_right": -60,
                "regionalist": 20
            },
            "centrist": {
                "radical_left": -40,
                "centrist": 80,
                "corporatist": 40,
                "religious_right": 0,
                "regionalist": -20
            },
            "corporatist": {
                "radical_left": -80,
                "centrist": 40,
                "corporatist": 80,
                "religious_right": 20,
                "regionalist": -40
            },
            "religious_right": {
                "radical_left": -60,
                "centrist": 0,
                "corporatist": 20,
                "religious_right": 80,
                "regionalist": 0
            },
            "regionalist": {
                "radical_left": 20,
                "centrist": -20,
                "corporatist": -40,
                "religious_right": 0,
                "regionalist": 80
            }
        }
        
        # Default to neutral if ideologies aren't found
        if ideology1 not in compatibility or ideology2 not in compatibility.get(ideology1, {}):
            return 0
            
        return compatibility[ideology1][ideology2]
    
    async def process_turn(self, game_state, current_turn: int) -> Dict[str, Any]:
        """
        Process faction actions for the current turn
        
        Args:
            game_state: Current game state
            current_turn: Current turn number
            
        Returns:
            Dictionary of faction action results
        """
        results = {
            "turn": current_turn,
            "faction_actions": {},
        }
        
        # For each faction, determine and execute actions
        for faction_id, faction_data in self.factions.items():
            faction_results = await self._process_faction_turn(faction_id, faction_data, game_state, current_turn)
            results["faction_actions"][faction_id] = faction_results
            
        logger.info(f"Processed turn {current_turn} for {len(self.factions)} factions")
        return results
    
    async def _process_faction_turn(
        self, faction_id: str, faction_data: Dict[str, Any], 
        game_state, current_turn: int
    ) -> Dict[str, Any]:
        """
        Process a single faction's turn
        
        Args:
            faction_id: ID of the faction
            faction_data: Faction data
            game_state: Current game state
            current_turn: Current turn number
            
        Returns:
            Dictionary of action results
        """
        # Get faction AI strategy based on faction type
        strategy = self._get_faction_strategy(faction_id, faction_data)
        
        # Determine goals for this turn
        goals = strategy.determine_goals(game_state)
        
        # Generate possible actions
        possible_actions = strategy.generate_actions(goals, game_state)
        
        # Evaluate and select actions
        selected_actions = strategy.select_actions(possible_actions, game_state)
        
        # Execute actions and get results
        action_results = []
        for action in selected_actions:
            result = await self._execute_faction_action(faction_id, faction_data, action, game_state)
            action_results.append(result)
        
        logger.debug(f"Faction {faction_id} completed {len(action_results)} actions on turn {current_turn}")
        
        return {
            "faction_id": faction_id,
            "actions_taken": len(action_results),
            "results": action_results,
            # Include summaries of changes
            "faction_updates": {},  # Changes to faction data
            "district_changes": {},  # Changes to districts
            "heat_changes": {},      # Changes to heat levels
            "events": []            # Events generated
        }
    
    def _get_faction_strategy(self, faction_id: str, faction_data: Dict[str, Any]) -> Any:
        """
        Get the AI strategy object for a faction
        
        TODO: Implement actual strategies with different behaviors
        """
        # Placeholder implementation
        return FactionStrategy()
        
    async def _execute_faction_action(
        self, faction_id: str, faction_data: Dict[str, Any], 
        action: Dict[str, Any], game_state
    ) -> Dict[str, Any]:
        """
        Execute a faction action and determine results
        
        Args:
            faction_id: ID of the faction
            faction_data: Faction data
            action: Action to execute
            game_state: Current game state
            
        Returns:
            Action result
        """
        # TODO: Implement faction action execution
        # This is a placeholder implementation
        
        action_type = action.get("type", "unknown")
        target = action.get("target", {})
        
        # Placeholder result with no actual game impact
        return {
            "action_id": action.get("id"),
            "action_type": action_type,
            "target": target,
            "success": True,
            "effects": {
                "description": f"Faction {faction_id} performed {action_type}"
            }
        }
    
    def get_faction(self, faction_id: str) -> Optional[Dict[str, Any]]:
        """Get faction data by ID"""
        return self.factions.get(faction_id)
    
    def get_relationship(self, faction_id: str, other_id: str) -> int:
        """Get relationship value between two factions"""
        if faction_id not in self.relationships or other_id not in self.relationships[faction_id]:
            return 0
        return self.relationships[faction_id][other_id]
    
    def set_relationship(self, faction_id: str, other_id: str, value: int) -> None:
        """Set relationship value between two factions"""
        if faction_id not in self.relationships:
            self.relationships[faction_id] = {}
        
        # Clamp value between -100 and 100
        value = max(-100, min(100, value))
        self.relationships[faction_id][other_id] = value
        logger.debug(f"Updated relationship between {faction_id} and {other_id} to {value}")


class FactionStrategy:
    """
    Base class for faction AI strategies
    
    Each faction type can have specialized strategies
    derived from this base class.
    """
    
    def determine_goals(self, game_state):
        """Determine faction goals based on current state"""
        # Placeholder implementation
        return [
            {"type": "resource_acquisition", "priority": 1},
            {"type": "influence_expansion", "priority": 2},
            {"type": "threat_response", "priority": 3}
        ]
    
    def generate_actions(self, goals, game_state):
        """Generate possible actions to achieve goals"""
        # Placeholder implementation
        return [
            {"id": "action1", "type": "recruit", "target": {"type": "district", "id": "downtown"}},
            {"id": "action2", "type": "campaign", "target": {"type": "district", "id": "university"}},
            {"id": "action3", "type": "sabotage", "target": {"type": "faction", "id": "corporations"}}
        ]
    
    def select_actions(self, possible_actions, game_state):
        """Select best actions from possibilities"""
        # Placeholder: just return all actions for now
        # In a real implementation, this would evaluate and choose the best ones
        return possible_actions
