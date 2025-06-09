"""
District service for managing districts, territorial control, and regional dynamics
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.sql_models import GameDistrict, GameFaction, Cell, Operation, faction_district_control
from models.schemas import GameDistrictResponse, DistrictMetricsUpdate

from repositories.districts import game_district_repository
from repositories.factions import game_faction_repository
from repositories.operations import cell_repository, operation_repository


class DistrictService:
    """District service for managing district entities and territorial dynamics"""
    
    def __init__(self):
        pass
    
    async def get_districts_in_game(
        self, db: AsyncSession, game_id: str
    ) -> List[GameDistrictResponse]:
        """Get all districts in a game"""
        districts = await game_district_repository.get_by_game(db, game_id)
        
        result = []
        for district in districts:
            # Get faction control data for each district
            control_data = await game_district_repository.get_faction_control(db, district.id)
            
            result.append(GameDistrictResponse(
                id=district.id,
                game_id=district.game_id,
                district_template_id=district.district_template_id,
                name=district.name,
                description=district.description,
                district_type=district.district_type,
                population=district.population,
                security_level=district.security_level,
                unrest_level=district.unrest_level,
                prosperity_level=district.prosperity_level,
                heat=district.heat,
                faction_control=control_data
            ))
                
        return result
    
    async def get_district_details(
        self, db: AsyncSession, district_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed district information including cells and operations"""
        district = await game_district_repository.get(db, district_id)
        if not district:
            return None
            
        # Get basic district data
        control_data = await game_district_repository.get_faction_control(db, district.id)
        
        # Get cells in district
        cells = await cell_repository.get_by_district(db, district.id)
        cell_data = []
        for cell in cells:
            cell_data.append({
                "id": cell.id,
                "name": cell.name,
                "faction_id": cell.faction_id,
                "cell_type": cell.cell_type,
                "size": cell.size,
                "specialization": cell.specialization
            })
        
        # Get active operations in district
        operations = await operation_repository.get_by_district(db, district.id)
        operation_data = []
        for operation in operations:
            if operation.current_stage != "completed" and operation.current_stage != "failed":
                operation_data.append({
                    "id": operation.id,
                    "name": operation.name,
                    "operation_type": operation.operation_type,
                    "faction_id": operation.faction_id,
                    "current_stage": operation.current_stage,
                    "scheduled_for_turn": operation.scheduled_for_turn
                })
        
        # Compile comprehensive district details
        district_details = {
            "district": GameDistrictResponse(
                id=district.id,
                game_id=district.game_id,
                district_template_id=district.district_template_id,
                name=district.name,
                description=district.description,
                district_type=district.district_type,
                population=district.population,
                security_level=district.security_level,
                unrest_level=district.unrest_level,
                prosperity_level=district.prosperity_level,
                heat=district.heat,
                faction_control=control_data
            ),
            "cells": cell_data,
            "active_operations": operation_data
        }
        
        return district_details
    
    async def update_district_metrics(
        self, 
        db: AsyncSession, 
        district_id: str, 
        metrics: DistrictMetricsUpdate
    ) -> Optional[GameDistrictResponse]:
        """Update district metrics"""
        updated_district = await game_district_repository.update_metrics(
            db, 
            district_id, 
            metrics.security_level,
            metrics.unrest_level,
            metrics.prosperity_level,
            metrics.heat
        )
        
        if not updated_district:
            return None
            
        # Get faction control data
        control_data = await game_district_repository.get_faction_control(
            db, district_id
        )
            
        return GameDistrictResponse(
            id=updated_district.id,
            game_id=updated_district.game_id,
            district_template_id=updated_district.district_template_id,
            name=updated_district.name,
            description=updated_district.description,
            district_type=updated_district.district_type,
            population=updated_district.population,
            security_level=updated_district.security_level,
            unrest_level=updated_district.unrest_level,
            prosperity_level=updated_district.prosperity_level,
            heat=updated_district.heat,
            faction_control=control_data
        )
    
    async def update_faction_control(
        self, 
        db: AsyncSession, 
        district_id: str, 
        faction_id: str, 
        control_percentage: float,
        influence: Optional[float] = None,
        heat: Optional[float] = None
    ) -> bool:
        """Update faction control in a district"""
        # Validate entities exist
        district = await game_district_repository.get(db, district_id)
        faction = await game_faction_repository.get(db, faction_id)
        
        if not district or not faction:
            return False
            
        # Ensure faction belongs to the same game as district
        if district.game_id != faction.game_id:
            return False
            
        # Update control
        return await game_district_repository.update_faction_control(
            db, district_id, faction_id, control_percentage, influence, heat
        )
    
    async def calculate_unrest_factors(
        self, db: AsyncSession, district_id: str
    ) -> Dict[str, Any]:
        """Calculate factors affecting unrest in a district"""
        district = await game_district_repository.get(db, district_id)
        if not district:
            return {}
            
        # Get faction control data
        control_data = await game_district_repository.get_faction_control(db, district_id)
        
        # Get cells in district
        cells = await cell_repository.get_by_district(db, district_id)
        
        # Get operations in district
        operations = await operation_repository.get_by_district(db, district_id)
        active_operations = [op for op in operations 
                           if op.current_stage != "completed" and op.current_stage != "failed"]
        
        # Calculate factors
        factors = {
            "base_unrest": district.unrest_level,
            "prosperity_factor": -0.5 * (district.prosperity_level / 10),  # Higher prosperity reduces unrest
            "security_factor": -1 * (district.security_level / 2),  # Higher security reduces unrest
            "heat_factor": 0.2 * (district.heat / 10),  # Higher heat increases unrest
            "cell_presence": len(cells) * 2,  # Each cell adds some unrest
            "active_operations": len(active_operations) * 3,  # Active operations increase unrest
            "control_disparity": self._calculate_control_disparity(control_data)  # Contested districts have higher unrest
        }
        
        # Calculate total unrest change
        factors["total_change"] = sum([
            factors["prosperity_factor"],
            factors["security_factor"],
            factors["heat_factor"],
            factors["cell_presence"],
            factors["active_operations"],
            factors["control_disparity"]
        ])
        
        # Calculate projected unrest
        factors["projected_unrest"] = max(0, min(100, district.unrest_level + factors["total_change"]))
        
        return factors
    
    def _calculate_control_disparity(self, control_data: Dict[str, float]) -> float:
        """Calculate unrest factor from control disparity among factions"""
        if not control_data:
            return 0
            
        # If one faction has overwhelming control, unrest is lower
        # If control is split among factions, unrest is higher
        values = list(control_data.values())
        if len(values) <= 1:
            return 0
            
        max_control = max(values)
        second_highest = sorted(values, reverse=True)[1] if len(values) > 1 else 0
        
        # Calculate disparity - higher disparity (one dominant faction) means lower unrest
        disparity = max_control - second_highest
        
        # Map disparity to unrest factor: high disparity = low unrest, low disparity = high unrest
        return max(0, 20 - (disparity / 5))
    
    async def recalculate_district_metrics(
        self, db: AsyncSession, game_id: str
    ) -> bool:
        """Recalculate metrics for all districts in a game based on events"""
        districts = await game_district_repository.get_by_game(db, game_id)
        
        for district in districts:
            # Calculate new unrest
            unrest_factors = await self.calculate_unrest_factors(db, district.id)
            new_unrest = round(unrest_factors["projected_unrest"])
            
            # Adjust security based on state faction control
            control_data = await game_district_repository.get_faction_control(db, district.id)
            
            # Find state faction(s)
            game_factions = await game_faction_repository.get_by_game(db, game_id)
            state_factions = [f for f in game_factions if f.faction_type == "state"]
            
            # Calculate security adjustment
            security_adjustment = 0
            for faction in state_factions:
                faction_control = control_data.get(faction.id, 0)
                security_adjustment += (faction_control / 100) * 0.5  # State control increases security
            
            new_security = max(1, min(10, district.security_level + security_adjustment))
            
            # Adjust prosperity based on unrest and security
            prosperity_change = 0
            if new_unrest > 50:
                prosperity_change -= (new_unrest - 50) / 10  # High unrest decreases prosperity
            if new_security < 5:
                prosperity_change -= (5 - new_security) * 2  # Low security decreases prosperity
            
            new_prosperity = max(0, min(100, district.prosperity_level + prosperity_change))
            
            # Decay heat over time (heat naturally decreases)
            new_heat = max(0, district.heat - 5)
            
            # Update district
            await game_district_repository.update_metrics(
                db,
                district.id,
                security_level=round(new_security),
                unrest_level=new_unrest,
                prosperity_level=round(new_prosperity),
                heat=round(new_heat)
            )
            
        return True


# Create singleton instance for global use
district_service = DistrictService()
