"""
MongoDB schema validation utilities
Provides functions to create and update MongoDB collection validation schemas
"""

from typing import Dict, Any, List
import json
from pymongo import MongoClient
from pymongo.errors import OperationFailure

from models.nosql_models import (
    GameStateSnapshot,
    GameEventLog,
    PlayerJournal,
    FactionAnalytics,
    WorldState,
    AITrainingData,
    SylvaIntegrationData,
    WrenIntegrationData,
)


# Map Pydantic models to collection names
COLLECTION_MODELS = {
    "game_state_snapshots": GameStateSnapshot,
    "game_event_logs": GameEventLog,
    "player_journals": PlayerJournal,
    "faction_analytics": FactionAnalytics,
    "world_states": WorldState,
    "ai_training_data": AITrainingData,
    "sylva_integration_data": SylvaIntegrationData,
    "wren_integration_data": WrenIntegrationData,
}


def pydantic_to_mongodb_schema(model_class) -> Dict[str, Any]:
    """
    Convert a Pydantic model to a MongoDB JSON Schema
    """
    # Get the JSON schema from the model
    schema = model_class.schema()
    
    # Extract the properties and required fields
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    # MongoDB validation schema format
    mongodb_schema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": required,
            "properties": {}
        }
    }
    
    # Convert Pydantic types to MongoDB BSON types
    for field_name, field_schema in properties.items():
        mongodb_field = {"description": field_schema.get("description", "")}
        
        # Map Python types to BSON types
        field_type = field_schema.get("type")
        if field_type == "string":
            mongodb_field["bsonType"] = "string"
        elif field_type == "integer":
            mongodb_field["bsonType"] = "int"
        elif field_type == "number":
            mongodb_field["bsonType"] = "double"
        elif field_type == "boolean":
            mongodb_field["bsonType"] = "bool"
        elif field_type == "array":
            mongodb_field["bsonType"] = "array"
            items = field_schema.get("items", {})
            if items:
                mongodb_field["items"] = {"bsonType": "object"}
        elif field_type == "object":
            mongodb_field["bsonType"] = "object"
        
        mongodb_schema["$jsonSchema"]["properties"][field_name] = mongodb_field
    
    return mongodb_schema


def setup_collection_validations(mongo_client: MongoClient, db_name: str) -> None:
    """
    Set up MongoDB collection validations for all models
    """
    db = mongo_client[db_name]
    
    # Get existing collection names
    existing_collections = db.list_collection_names()
    
    for collection_name, model_class in COLLECTION_MODELS.items():
        # Create validation schema
        schema = pydantic_to_mongodb_schema(model_class)
        
        if collection_name in existing_collections:
            # Update existing collection with validation
            try:
                db.command({
                    "collMod": collection_name,
                    "validator": schema,
                    "validationLevel": "moderate",
                    "validationAction": "warn"
                })
                print(f"Updated validation for collection: {collection_name}")
            except OperationFailure as e:
                print(f"Failed to update validation for {collection_name}: {e}")
        else:
            # Create new collection with validation
            try:
                db.create_collection(
                    collection_name, 
                    validator=schema,
                    validationLevel="moderate",
                    validationAction="warn"
                )
                print(f"Created collection with validation: {collection_name}")
            except OperationFailure as e:
                print(f"Failed to create collection {collection_name}: {e}")


def get_mongodb_indexes() -> Dict[str, List[Dict[str, Any]]]:
    """
    Define indexes for MongoDB collections
    Returns a dict with collection names as keys and lists of index definitions
    """
    return {
        "game_state_snapshots": [
            {"keys": [("game_id", 1), ("turn", 1)], "unique": True},
            {"keys": [("game_id", 1), ("timestamp", -1)]}
        ],
        "game_event_logs": [
            {"keys": [("game_id", 1), ("event_id", 1)], "unique": True},
            {"keys": [("game_id", 1), ("turn", 1)]},
            {"keys": [("game_id", 1), ("event_type", 1)]}
        ],
        "player_journals": [
            {"keys": [("id", 1)], "unique": True},
            {"keys": [("game_id", 1), ("character_id", 1), ("turn", -1)]},
            {"keys": [("game_id", 1), ("timestamp", -1)]}
        ],
        "faction_analytics": [
            {"keys": [("game_id", 1), ("faction_id", 1), ("turn", 1)], "unique": True},
            {"keys": [("game_id", 1), ("faction_id", 1), ("timestamp", -1)]}
        ],
        "world_states": [
            {"keys": [("game_id", 1), ("turn", 1)], "unique": True}
        ],
        "ai_training_data": [
            {"keys": [("game_id", 1), ("data_type", 1), ("collection_time", -1)]}
        ],
        "sylva_integration_data": [
            {"keys": [("game_id", 1), ("character_id", 1), ("timestamp", -1)]}
        ],
        "wren_integration_data": [
            {"keys": [("game_id", 1), ("character_id", 1), ("timestamp", -1)]}
        ]
    }


def create_mongodb_indexes(mongo_client: MongoClient, db_name: str) -> None:
    """
    Create indexes for MongoDB collections
    """
    db = mongo_client[db_name]
    indexes = get_mongodb_indexes()
    
    for collection_name, collection_indexes in indexes.items():
        if collection_name not in db.list_collection_names():
            continue
            
        collection = db[collection_name]
        
        for index_def in collection_indexes:
            keys = index_def.pop("keys")
            try:
                collection.create_index(keys, **index_def)
                print(f"Created index on {collection_name}: {keys}")
            except Exception as e:
                print(f"Failed to create index on {collection_name}: {e}")


def initialize_mongodb(mongo_client: MongoClient, db_name: str) -> None:
    """
    Initialize MongoDB with collections, validations and indexes
    """
    setup_collection_validations(mongo_client, db_name)
    create_mongodb_indexes(mongo_client, db_name)
