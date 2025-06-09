"""
Faction service for managing factions, relationships, and faction-specific operations
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.sql_models import Game, GameFaction, Cell, Operation, faction_relationships
from models.nosql_models import FactionAnalytics
from models.schemas import (
    GameFactionResponse, FactionResourcesUpdate,
    CellCreate, CellResponse, OperationCreate, OperationResponse
)

from repositories.factions import faction_repository, game_faction_repository
from repositories.operations import cell_repository, operation_repository
from repositories.districts import game_district_repository
from repositories.nosql_repositories import FactionAnalyticsRepository


class FactionService:
    """Faction service for managing faction entities and interactions"""
    
    def __init__(self, mongo_db: Optional[AsyncIOMotorDatabase] = None):
        self.mongo_db = mongo_db
        
        # Initialize NoSQL repositories if mongodb is provided
        if mongo_db:
            self.analytics_repository = FactionAnalyticsRepository(mongo_db)
        else:
            self.analytics_repository = None
    
    async def get_factions_in_game(
        self, db: AsyncSession, game_id: str
    ) -> List[GameFactionResponse]:
        """Get all factions in a game"""
        factions = await game_faction_repository.get_by_game(db, game_id)
        
        return [
            GameFactionResponse(
                id=faction.id,
                game_id=faction.game_id,
                faction_template_id=faction.faction_template_id,
                name=faction.name,
                faction_type=faction.faction_type,
                ideology=faction.ideology,
                description=faction.description,
                resources=faction.resources,
                is_player_faction=faction.is_player_faction,
                is_active=faction.is_active,
                popularity=faction.popularity,
                heat=faction.heat
            )
            for faction in factions
        ]
    
    async def set_player_faction(
        self, db: AsyncSession, game_id: str, faction_id: str
    ) -> Optional[GameFactionResponse]:
        """Set a faction as the player-controlled faction"""
        # Reset any existing player factions
        current_factions = await game_faction_repository.get_by_game(db, game_id)
        for faction in current_factions:
            if faction.is_player_faction:
                faction.is_player_faction = False
                db.add(faction)
                
        # Set new player faction
        faction = await game_faction_repository.get(db, faction_id)
        if not faction or faction.game_id != game_id:
            return None
            
        faction.is_player_faction = True
        db.add(faction)
        await db.commit()
        await db.refresh(faction)
        
        return GameFactionResponse(
            id=faction.id,
            game_id=faction.game_id,
            faction_template_id=faction.faction_template_id,
            name=faction.name,
            faction_type=faction.faction_type,
            ideology=faction.ideology,
            description=faction.description,
            resources=faction.resources,
            is_player_faction=faction.is_player_faction,
            is_active=faction.is_active,
            popularity=faction.popularity,
            heat=faction.heat
        )
    
    async def update_faction_resources(
        self, db: AsyncSession, faction_id: str, resources_update: FactionResourcesUpdate
    ) -> Optional[GameFactionResponse]:
        """Update faction resources"""
        updated_faction = await game_faction_repository.update_resources(
            db, faction_id, resources_update.resources
        )
        
        if not updated_faction:
            return None
            
        return GameFactionResponse(
            id=updated_faction.id,
            game_id=updated_faction.game_id,
            faction_template_id=updated_faction.faction_template_id,
            name=updated_faction.name,
            faction_type=updated_faction.faction_type,
            ideology=updated_faction.ideology,
            description=updated_faction.description,
            resources=updated_faction.resources,
            is_player_faction=updated_faction.is_player_faction,
            is_active=updated_faction.is_active,
            popularity=updated_faction.popularity,
            heat=updated_faction.heat
        )
    
    async def get_faction_relationships(
        self, db: AsyncSession, faction_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """Get all relationships for a faction with faction details"""
        # Get basic relationship values
        relationships = await game_faction_repository.get_relationships(db, faction_id)
        
        # Expand with faction details
        result = {}
        for other_faction_id, value in relationships.items():
            other_faction = await game_faction_repository.get(db, other_faction_id)
            if other_faction:
                result[other_faction_id] = {
                    "name": other_faction.name,
                    "faction_type": other_faction.faction_type,
                    "ideology": other_faction.ideology,
                    "value": value
                }
                
        return result
    
    async def update_relationship(
        self, 
        db: AsyncSession, 
        faction_id: str, 
        other_faction_id: str, 
        value: int
    ) -> bool:
        """Update relationship between two factions"""
        # Validate factions exist
        faction = await game_faction_repository.get(db, faction_id)
        other_faction = await game_faction_repository.get(db, other_faction_id)
        
        if not faction or not other_faction:
            return False
            
        # Ensure both factions are part of the same game
        if faction.game_id != other_faction.game_id:
            return False
            
        # Update relationship
        return await game_faction_repository.update_relationship(
            db, faction_id, other_faction_id, value
        )
    
    async def create_cell(
        self, db: AsyncSession, cell_data: CellCreate
    ) -> CellResponse:
        """Create a new cell for a faction"""
        # Validate faction exists
        faction = await game_faction_repository.get(db, cell_data.faction_id)
        if not faction:
            raise ValueError(f"Faction with ID {cell_data.faction_id} not found")
            
        # Set default values
        cell_dict = cell_data.dict()
        cell_dict["id"] = str(uuid.uuid4())
        if "morale" not in cell_dict or cell_dict["morale"] is None:
            cell_dict["morale"] = 50
        if "cover_strength" not in cell_dict or cell_dict["cover_strength"] is None:
            cell_dict["cover_strength"] = 100  # Start with full cover
        if "heat" not in cell_dict or cell_dict["heat"] is None:
            cell_dict["heat"] = 0
        if "size" not in cell_dict or cell_dict["size"] is None:
            cell_dict["size"] = 3  # Default cell size
        
        # Create cell
        cell = await cell_repository.create(db, obj_in=cell_dict)
        
        return CellResponse(
            id=cell.id,
            name=cell.name,
            faction_id=cell.faction_id,
            district_id=cell.district_id,
            leader_id=cell.leader_id,
            cell_type=cell.cell_type,
            morale=cell.morale,
            cover_strength=cell.cover_strength,
            heat=cell.heat,
            size=cell.size,
            specialization=cell.specialization,
            equipment=cell.equipment
        )
    
    async def create_operation(
        self, db: AsyncSession, operation_data: OperationCreate
    ) -> OperationResponse:
        """Create a new operation for a faction"""
        # Validate faction exists
        faction = await game_faction_repository.get(db, operation_data.faction_id)
        if not faction:
            raise ValueError(f"Faction with ID {operation_data.faction_id} not found")
            
        # Set default values
        operation_dict = operation_data.dict()
        operation_dict["id"] = str(uuid.uuid4())
        if "current_stage" not in operation_dict or operation_dict["current_stage"] is None:
            operation_dict["current_stage"] = "planning"
        if "success_probability" not in operation_dict or operation_dict["success_probability"] is None:
            operation_dict["success_probability"] = 0.5  # 50% default probability
            
        # Create operation
        operation = await operation_repository.create(db, obj_in=operation_dict)
        
        # Assign cells if provided
        if operation_data.cell_ids:
            await operation_repository.assign_cells(db, operation.id, operation_data.cell_ids)
        
        return OperationResponse(
            id=operation.id,
            name=operation.name,
            operation_type=operation.operation_type,
            description=operation.description,
            faction_id=operation.faction_id,
            district_id=operation.district_id,
            target_faction_id=operation.target_faction_id,
            scheduled_for_turn=operation.scheduled_for_turn,
            current_stage=operation.current_stage,
            success_probability=operation.success_probability,
            cell_ids=await operation_repository.get_assigned_cells(db, operation.id),
            resource_cost=operation.resource_cost,
            expected_outcomes=operation.expected_outcomes,
            actual_outcomes=operation.actual_outcomes
        )
    
    async def calculate_support_in_district(
        self, db: AsyncSession, faction_id: str, district_id: str
    ) -> Dict[str, float]:
        """Calculate a faction's support level in a district"""
        # Get basic control percentage
        control_data = await game_district_repository.get_faction_control(
            db, district_id
        )
        
        faction_control = control_data.get(faction_id, 0.0)
        
        # Consider cells in the district
        cells = await cell_repository.get_by_district(db, district_id)
        faction_cells = [cell for cell in cells if cell.faction_id == faction_id]
        
        # Calculate support based on cells' influence
        cell_influence = sum(
            [
                (cell.size / 10) * (cell.morale / 100)  # Size and morale affect influence
                for cell in faction_cells
            ]
        )
        
        # Calculate influence from operations
        operations = await operation_repository.get_by_district(db, district_id)
        faction_operations = [op for op in operations if op.faction_id == faction_id]
        completed_ops = [op for op in faction_operations if op.current_stage == "completed"]
        
        operation_influence = len(completed_ops) * 5  # Each successful operation adds influence
        
        # Combined support calculation
        combined_support = {
            "control_percentage": faction_control,
            "cell_influence": min(30.0, cell_influence),  # Cap cell influence
            "operation_influence": min(20.0, operation_influence),  # Cap operation influence
            "total_support": min(100.0, faction_control + cell_influence/3 + operation_influence/5)
        }
        
        return combined_support
    
    async def record_faction_analytics(
        self, db: AsyncSession, game_id: str, turn: int
    ) -> bool:
        """Record analytics data for all factions in a game"""
        if not self.analytics_repository:
            return False
            
        # Get all factions in game
        factions = await game_faction_repository.get_by_game(db, game_id)
        
        for faction in factions:
            # Calculate total control across all districts
            game_districts = await game_district_repository.get_by_game(db, game_id)
            total_control = 0.0
            district_control = {}
            
            for district in game_districts:
                control_data = await game_district_repository.get_faction_control(
                    db, district.id
                )
                district_control[district.id] = control_data.get(faction.id, 0.0)
                total_control += control_data.get(faction.id, 0.0)
                
            # Calculate average control
            avg_control = total_control / len(game_districts) if game_districts else 0
            
            # Get all cells for this faction
            cells = await cell_repository.get_by_faction(db, faction.id)
            cell_count = len(cells)
            
            # Get all operations for this faction
            operations = await operation_repository.get_by_faction(db, faction.id)
            active_operations = len([op for op in operations if op.current_stage != "completed" and op.current_stage != "failed"])
            completed_operations = len([op for op in operations if op.current_stage == "completed"])
            failed_operations = len([op for op in operations if op.current_stage == "failed"])
            
            # Create analytics entry
            analytics = FactionAnalytics(
                game_id=game_id,
                faction_id=faction.id,
                faction_name=faction.name,
                turn=turn,
                timestamp=datetime.utcnow(),
                popularity=faction.popularity,
                resources=faction.resources,
                heat=faction.heat,
                territory_control={
                    "average_control": avg_control,
                    "district_breakdown": district_control
                },
                assets={
                    "cell_count": cell_count,
                    "active_operations": active_operations,
                    "completed_operations": completed_operations,
                    "failed_operations": failed_operations
                }
            )
            
            # Save analytics
            await self.analytics_repository.create(analytics.dict())
            
        return True


# To be instantiated with dependency injection for MongoDB connection
# faction_service = FactionService(mongo_db)
