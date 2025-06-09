"""
MongoDB repositories for Years of Lead NoSQL data models
"""

from typing import Dict, List, Optional, Any, Union, TypeVar, Generic
from datetime import datetime
import json
from pydantic import BaseModel
from pymongo.database import Database
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult
from bson import ObjectId
from bson.json_util import dumps, loads

from models.nosql_models import (
    GameStateSnapshot,
    GameEventLog,
    PlayerJournal,
    FactionAnalytics,
    WorldState,
    AITrainingData,
    SylvaIntegrationData,
    WrenIntegrationData
)

# Type variable for Pydantic models
ModelType = TypeVar("ModelType", bound=BaseModel)


class NoSQLBaseRepository(Generic[ModelType]):
    """Base repository for MongoDB operations"""
    
    def __init__(self, db: Database, collection_name: str, model_class: ModelType):
        self.db = db
        self.collection = db[collection_name]
        self.model_class = model_class
    
    async def get(self, id: str) -> Optional[ModelType]:
        """Get a document by ID"""
        result = await self.collection.find_one({"_id": id})
        if not result:
            return None
        return self.model_class(**self._process_mongodb_doc(result))
    
    async def get_by_filter(self, filter_dict: Dict[str, Any]) -> Optional[ModelType]:
        """Get a document by custom filter"""
        result = await self.collection.find_one(filter_dict)
        if not result:
            return None
        return self.model_class(**self._process_mongodb_doc(result))
    
    async def list(self, filter_dict: Dict[str, Any] = None, 
                  skip: int = 0, limit: int = 100,
                  sort_by: str = None, sort_desc: bool = False) -> List[ModelType]:
        """List documents with optional filtering and sorting"""
        filter_dict = filter_dict or {}
        cursor = self.collection.find(filter_dict).skip(skip).limit(limit)
        
        if sort_by:
            sort_direction = -1 if sort_desc else 1
            cursor = cursor.sort(sort_by, sort_direction)
            
        results = await cursor.to_list(length=limit)
        return [self.model_class(**self._process_mongodb_doc(doc)) for doc in results]
    
    async def create(self, obj_in: Union[ModelType, Dict[str, Any]]) -> str:
        """Create a new document"""
        if isinstance(obj_in, dict):
            data = obj_in
        else:
            data = obj_in.dict()
            
        result: InsertOneResult = await self.collection.insert_one(data)
        return str(result.inserted_id)
    
    async def update(self, id: str, obj_in: Union[ModelType, Dict[str, Any]]) -> bool:
        """Update a document by ID"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        result: UpdateResult = await self.collection.update_one(
            {"_id": id}, {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def delete(self, id: str) -> bool:
        """Delete a document by ID"""
        result: DeleteResult = await self.collection.delete_one({"_id": id})
        return result.deleted_count > 0
    
    def _process_mongodb_doc(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Process MongoDB document by converting ObjectId to string"""
        # Convert ObjectId to string
        if '_id' in doc and isinstance(doc['_id'], ObjectId):
            doc['_id'] = str(doc['_id'])
            
        # Handle ISODate and other BSON types with json serialization/deserialization
        return json.loads(dumps(doc))


class GameStateSnapshotRepository(NoSQLBaseRepository[GameStateSnapshot]):
    """Repository for game state snapshots"""
    
    def __init__(self, db: Database):
        super().__init__(db, "game_state_snapshots", GameStateSnapshot)
    
    async def get_latest_snapshot(self, game_id: str) -> Optional[GameStateSnapshot]:
        """Get the latest game state snapshot for a game"""
        result = await self.collection.find_one(
            {"game_id": game_id},
            sort=[("timestamp", -1)]
        )
        if not result:
            return None
        return GameStateSnapshot(**self._process_mongodb_doc(result))
    
    async def get_snapshot_at_turn(self, game_id: str, turn: int) -> Optional[GameStateSnapshot]:
        """Get game state snapshot for a specific turn"""
        result = await self.collection.find_one({
            "game_id": game_id,
            "turn": turn
        })
        if not result:
            return None
        return GameStateSnapshot(**self._process_mongodb_doc(result))
    
    async def get_snapshots_for_game(
        self, game_id: str, limit: int = 10
    ) -> List[GameStateSnapshot]:
        """Get recent snapshots for a game"""
        cursor = self.collection.find(
            {"game_id": game_id}
        ).sort("timestamp", -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        return [GameStateSnapshot(**self._process_mongodb_doc(doc)) for doc in results]


class GameEventLogRepository(NoSQLBaseRepository[GameEventLog]):
    """Repository for game event logs"""
    
    def __init__(self, db: Database):
        super().__init__(db, "game_event_logs", GameEventLog)
    
    async def get_events_by_turn(
        self, game_id: str, turn: int
    ) -> List[GameEventLog]:
        """Get all events for a specific turn"""
        cursor = self.collection.find({
            "game_id": game_id,
            "turn": turn
        }).sort("timestamp", 1)
        
        results = await cursor.to_list(length=100)
        return [GameEventLog(**self._process_mongodb_doc(doc)) for doc in results]
    
    async def get_events_by_type(
        self, game_id: str, event_type: str, limit: int = 50
    ) -> List[GameEventLog]:
        """Get events of a specific type"""
        cursor = self.collection.find({
            "game_id": game_id,
            "event_type": event_type
        }).sort("timestamp", -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        return [GameEventLog(**self._process_mongodb_doc(doc)) for doc in results]
    
    async def get_events_affecting_entity(
        self, game_id: str, entity_type: str, entity_id: str, limit: int = 50
    ) -> List[GameEventLog]:
        """Get events affecting a specific entity"""
        cursor = self.collection.find({
            "game_id": game_id,
            f"affected_entities.{entity_type}": entity_id
        }).sort("timestamp", -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        return [GameEventLog(**self._process_mongodb_doc(doc)) for doc in results]


class PlayerJournalRepository(NoSQLBaseRepository[PlayerJournal]):
    """Repository for player journal entries"""
    
    def __init__(self, db: Database):
        super().__init__(db, "player_journals", PlayerJournal)
    
    async def get_entries_for_character(
        self, game_id: str, character_id: str, limit: int = 20
    ) -> List[PlayerJournal]:
        """Get journal entries for a specific character"""
        cursor = self.collection.find({
            "game_id": game_id,
            "character_id": character_id
        }).sort("timestamp", -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        return [PlayerJournal(**self._process_mongodb_doc(doc)) for doc in results]
    
    async def get_entries_with_emotional_tag(
        self, game_id: str, tag: str, limit: int = 20
    ) -> List[PlayerJournal]:
        """Get journal entries with a specific emotional tag"""
        cursor = self.collection.find({
            "game_id": game_id,
            "emotional_tags.name": tag
        }).sort("timestamp", -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        return [PlayerJournal(**self._process_mongodb_doc(doc)) for doc in results]


class FactionAnalyticsRepository(NoSQLBaseRepository[FactionAnalytics]):
    """Repository for faction analytics data"""
    
    def __init__(self, db: Database):
        super().__init__(db, "faction_analytics", FactionAnalytics)
    
    async def get_analytics_history(
        self, game_id: str, faction_id: str, limit: int = 10
    ) -> List[FactionAnalytics]:
        """Get historical analytics for a faction"""
        cursor = self.collection.find({
            "game_id": game_id,
            "faction_id": faction_id
        }).sort("turn", -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        return [FactionAnalytics(**self._process_mongodb_doc(doc)) for doc in results]


class WorldStateRepository(NoSQLBaseRepository[WorldState]):
    """Repository for world state data"""
    
    def __init__(self, db: Database):
        super().__init__(db, "world_states", WorldState)
    
    async def get_current_world_state(self, game_id: str) -> Optional[WorldState]:
        """Get the current world state for a game"""
        result = await self.collection.find_one({
            "game_id": game_id
        }, sort=[("turn", -1)])
        
        if not result:
            return None
        return WorldState(**self._process_mongodb_doc(result))


class AITrainingDataRepository(NoSQLBaseRepository[AITrainingData]):
    """Repository for AI training data"""
    
    def __init__(self, db: Database):
        super().__init__(db, "ai_training_data", AITrainingData)
    
    async def get_training_data_by_type(
        self, data_type: str, limit: int = 100
    ) -> List[AITrainingData]:
        """Get training data of a specific type"""
        cursor = self.collection.find({
            "data_type": data_type
        }).sort("collection_time", -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        return [AITrainingData(**self._process_mongodb_doc(doc)) for doc in results]


class SylvaIntegrationDataRepository(NoSQLBaseRepository[SylvaIntegrationData]):
    """Repository for SYLVA integration data"""
    
    def __init__(self, db: Database):
        super().__init__(db, "sylva_integration_data", SylvaIntegrationData)
    
    async def get_character_emotional_state(
        self, game_id: str, character_id: str
    ) -> Optional[SylvaIntegrationData]:
        """Get current emotional state for a character"""
        result = await self.collection.find_one({
            "game_id": game_id,
            "character_id": character_id
        }, sort=[("timestamp", -1)])
        
        if not result:
            return None
        return SylvaIntegrationData(**self._process_mongodb_doc(result))


class WrenIntegrationDataRepository(NoSQLBaseRepository[WrenIntegrationData]):
    """Repository for WREN integration data"""
    
    def __init__(self, db: Database):
        super().__init__(db, "wren_integration_data", WrenIntegrationData)
    
    async def get_character_narrative_context(
        self, game_id: str, character_id: str
    ) -> Optional[WrenIntegrationData]:
        """Get current narrative context for a character"""
        result = await self.collection.find_one({
            "game_id": game_id,
            "character_id": character_id
        }, sort=[("timestamp", -1)])
        
        if not result:
            return None
        return WrenIntegrationData(**self._process_mongodb_doc(result))
    
    async def get_game_narrative_context(self, game_id: str) -> Optional[WrenIntegrationData]:
        """Get current narrative context for a game (world-level narrative)"""
        result = await self.collection.find_one({
            "game_id": game_id,
            "character_id": None
        }, sort=[("timestamp", -1)])
        
        if not result:
            return None
        return WrenIntegrationData(**self._process_mongodb_doc(result))
