"""
Operations and cells repository for database operations
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, text, desc

from models.sql_models import Operation, Cell, cell_operations
from models.schemas import OperationCreate, OperationBase, CellCreate, CellBase
from repositories.base import BaseRepository


class OperationRepository(BaseRepository[Operation, OperationCreate, OperationBase]):
    """Operation repository for database operations"""
    
    def __init__(self):
        super().__init__(Operation)
    
    async def get_by_faction(self, db: AsyncSession, faction_id: str) -> List[Operation]:
        """Get operations by faction ID"""
        query = select(Operation).where(Operation.faction_id == faction_id)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_district(self, db: AsyncSession, district_id: str) -> List[Operation]:
        """Get operations in a district"""
        query = select(Operation).where(Operation.district_id == district_id)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_active_operations(self, db: AsyncSession, faction_id: str) -> List[Operation]:
        """Get active (non-completed) operations for a faction"""
        query = select(Operation).where(
            and_(
                Operation.faction_id == faction_id,
                Operation.current_stage != "completed",
                Operation.current_stage != "failed"
            )
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_stage(
        self, db: AsyncSession, operation_id: str, stage: str
    ) -> Optional[Operation]:
        """Update operation stage"""
        operation = await self.get(db, operation_id)
        if not operation:
            return None
        
        valid_stages = ["planning", "executing", "completed", "failed"]
        if stage not in valid_stages:
            raise ValueError(f"Invalid stage: {stage}. Must be one of: {', '.join(valid_stages)}")
            
        operation.current_stage = stage
        db.add(operation)
        await db.commit()
        await db.refresh(operation)
        return operation
    
    async def update_success_probability(
        self, db: AsyncSession, operation_id: str, probability: float
    ) -> Optional[Operation]:
        """Update operation success probability"""
        operation = await self.get(db, operation_id)
        if not operation:
            return None
            
        # Ensure probability is between 0 and 1
        probability = max(0.0, min(1.0, probability))
        operation.success_probability = probability
        
        db.add(operation)
        await db.commit()
        await db.refresh(operation)
        return operation
    
    async def assign_cells(
        self, db: AsyncSession, operation_id: str, cell_ids: List[str]
    ) -> bool:
        """Assign cells to an operation"""
        # Delete existing cell assignments
        delete_stmt = cell_operations.delete().where(
            cell_operations.c.operation_id == operation_id
        )
        await db.execute(delete_stmt)
        
        # Add new cell assignments
        for cell_id in cell_ids:
            insert_stmt = cell_operations.insert().values(
                operation_id=operation_id,
                cell_id=cell_id
            )
            await db.execute(insert_stmt)
            
        await db.commit()
        return True
    
    async def get_assigned_cells(
        self, db: AsyncSession, operation_id: str
    ) -> List[str]:
        """Get IDs of cells assigned to an operation"""
        query = select(cell_operations.c.cell_id).where(
            cell_operations.c.operation_id == operation_id
        )
        result = await db.execute(query)
        return [row[0] for row in result.all()]


class CellRepository(BaseRepository[Cell, CellCreate, CellBase]):
    """Cell repository for database operations"""
    
    def __init__(self):
        super().__init__(Cell)
    
    async def get_by_faction(self, db: AsyncSession, faction_id: str) -> List[Cell]:
        """Get cells by faction ID"""
        query = select(Cell).where(Cell.faction_id == faction_id)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_district(self, db: AsyncSession, district_id: str) -> List[Cell]:
        """Get cells in a district"""
        query = select(Cell).where(Cell.district_id == district_id)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_leader(self, db: AsyncSession, leader_id: str) -> List[Cell]:
        """Get cells led by a specific character"""
        query = select(Cell).where(Cell.leader_id == leader_id)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_operations(
        self, db: AsyncSession, cell_id: str
    ) -> List[str]:
        """Get operation IDs that a cell is assigned to"""
        query = select(cell_operations.c.operation_id).where(
            cell_operations.c.cell_id == cell_id
        )
        result = await db.execute(query)
        return [row[0] for row in result.all()]
    
    async def update_morale(
        self, db: AsyncSession, cell_id: str, morale_change: int
    ) -> Optional[Cell]:
        """Update cell morale"""
        cell = await self.get(db, cell_id)
        if not cell:
            return None
            
        cell.morale = max(0, min(100, cell.morale + morale_change))
        db.add(cell)
        await db.commit()
        await db.refresh(cell)
        return cell
    
    async def update_cover(
        self, db: AsyncSession, cell_id: str, cover_change: int
    ) -> Optional[Cell]:
        """Update cell cover strength"""
        cell = await self.get(db, cell_id)
        if not cell:
            return None
            
        cell.cover_strength = max(0, min(100, cell.cover_strength + cover_change))
        db.add(cell)
        await db.commit()
        await db.refresh(cell)
        return cell
    
    async def update_heat(
        self, db: AsyncSession, cell_id: str, heat_change: int
    ) -> Optional[Cell]:
        """Update cell heat level"""
        cell = await self.get(db, cell_id)
        if not cell:
            return None
            
        cell.heat = max(0, min(100, cell.heat + heat_change))
        db.add(cell)
        await db.commit()
        await db.refresh(cell)
        return cell
    
    async def update_size(
        self, db: AsyncSession, cell_id: str, size_change: int
    ) -> Optional[Cell]:
        """Update cell size (number of members)"""
        cell = await self.get(db, cell_id)
        if not cell:
            return None
            
        cell.size = max(1, cell.size + size_change)  # Minimum size is 1
        db.add(cell)
        await db.commit()
        await db.refresh(cell)
        return cell


# Create singleton instances for global use
operation_repository = OperationRepository()
cell_repository = CellRepository()
