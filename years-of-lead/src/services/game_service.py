"""
Game service for managing game sessions and state
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.sql_models import Game, GameEvent, Scenario, Faction, GameFaction, District, GameDistrict
from models.nosql_models import GameStateSnapshot, GameEventLog
from models.schemas import (
    GameCreate, GameResponse, ScenarioResponse, 
    GameFactionCreate, GameDistrictCreate
)

from repositories.games import game_repository
from repositories.factions import faction_repository, game_faction_repository
from repositories.districts import district_repository, game_district_repository
from repositories.operations import operation_repository, cell_repository
from repositories.nosql_repositories import GameStateSnapshotRepository, GameEventLogRepository


class GameService:
    """Game service for managing game sessions and state"""
    
    def __init__(self, mongo_db: Optional[AsyncIOMotorDatabase] = None):
        self.mongo_db = mongo_db
        
        # Initialize NoSQL repositories if mongodb is provided
        if mongo_db:
            self.snapshot_repository = GameStateSnapshotRepository(mongo_db)
            self.event_repository = GameEventLogRepository(mongo_db)
        else:
            self.snapshot_repository = None
            self.event_repository = None
    
    async def create_game(
        self, 
        db: AsyncSession, 
        game_data: GameCreate,
        user_id: str
    ) -> GameResponse:
        """Create a new game session"""
        # Validate scenario existence
        scenario = await db.get(Scenario, game_data.scenario_id)
        if not scenario:
            raise ValueError(f"Scenario with ID {game_data.scenario_id} not found")
            
        # Create game record
        game_dict = game_data.dict()
        game_dict["id"] = str(uuid.uuid4())
        game_dict["created_by"] = user_id
        game_dict["current_turn"] = 1
        game_dict["is_completed"] = False
        game_dict["created_at"] = datetime.utcnow()
        game_dict["last_played_at"] = datetime.utcnow()
        
        game = await game_repository.create(db, obj_in=game_dict)
        
        # Initialize game entities based on scenario
        await self._initialize_game_factions(db, game.id, game_data.scenario_id)
        await self._initialize_game_districts(db, game.id, game_data.scenario_id)
        
        # Create initial game state snapshot
        if self.snapshot_repository:
            await self._create_initial_snapshot(db, game.id)
        
        # Return created game
        return GameResponse(
            id=game.id,
            name=game.name,
            description=game.description,
            scenario_id=game.scenario_id,
            current_turn=game.current_turn,
            is_completed=game.is_completed,
            created_by=game.created_by,
            created_at=game.created_at,
            last_played_at=game.last_played_at
        )
    
    async def get_game(
        self, 
        db: AsyncSession, 
        game_id: str
    ) -> Optional[GameResponse]:
        """Get game by ID"""
        game = await game_repository.get(db, game_id)
        if not game:
            return None
            
        return GameResponse(
            id=game.id,
            name=game.name,
            description=game.description,
            scenario_id=game.scenario_id,
            current_turn=game.current_turn,
            is_completed=game.is_completed,
            created_by=game.created_by,
            created_at=game.created_at,
            last_played_at=game.last_played_at
        )
    
    async def get_user_games(
        self, 
        db: AsyncSession, 
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[GameResponse]:
        """Get all games created by user"""
        games = await game_repository.get_by_user(db, user_id, skip, limit)
        
        return [
            GameResponse(
                id=game.id,
                name=game.name,
                description=game.description,
                scenario_id=game.scenario_id,
                current_turn=game.current_turn,
                is_completed=game.is_completed,
                created_by=game.created_by,
                created_at=game.created_at,
                last_played_at=game.last_played_at
            )
            for game in games
        ]
    
    async def advance_turn(self, db: AsyncSession, game_id: str) -> Optional[GameResponse]:
        """Advance game to next turn"""
        # Get current game
        game = await game_repository.get(db, game_id)
        if not game:
            return None
            
        if game.is_completed:
            return GameResponse.from_orm(game)
            
        # Save current game state snapshot before advancing
        if self.snapshot_repository:
            await self._create_snapshot(db, game_id, game.current_turn)
            
        # Process end of turn events
        await self._process_end_of_turn(db, game)
        
        # Advance turn
        await game_repository.increment_turn(db, game_id)
        await game_repository.update_last_played(db, game_id)
        
        # Get updated game
        updated_game = await game_repository.get(db, game_id)
        
        # Process beginning of turn events
        await self._process_beginning_of_turn(db, updated_game)
        
        return GameResponse.from_orm(updated_game)
    
    async def _initialize_game_factions(
        self, 
        db: AsyncSession, 
        game_id: str, 
        scenario_id: str
    ) -> List[str]:
        """Initialize factions for a new game based on scenario"""
        # Get factions from scenario
        scenario_factions = await faction_repository.list(
            db, 
            filter_dict={"scenario_id": scenario_id}
        )
        
        created_faction_ids = []
        
        # Create game faction instances for each faction template
        for template in scenario_factions:
            # Default starting values
            starting_resources = {
                "money": 1000,
                "weapons": 10,
                "intel": 5,
                "support": 50  # Base public support level
            }
            
            # Adjust based on faction type
            if template.faction_type == "state":
                starting_resources = {
                    "money": 5000,
                    "weapons": 50,
                    "intel": 20,
                    "support": 40
                }
            elif template.faction_type == "insurgent":
                starting_resources = {
                    "money": 500,
                    "weapons": 5,
                    "intel": 10,
                    "support": 30
                }
            
            # Create game faction
            game_faction = GameFactionCreate(
                id=str(uuid.uuid4()),
                game_id=game_id,
                faction_template_id=template.id,
                name=template.name,
                faction_type=template.faction_type,
                ideology=template.ideology,
                description=template.description,
                resources=starting_resources,
                is_player_faction=False,  # Default to AI-controlled
                is_active=True,
                popularity=50,  # Default to neutral popularity
                heat=0        # Start with no heat/suspicion
            )
            
            created_faction = await game_faction_repository.create(
                db, 
                obj_in=game_faction.dict()
            )
            created_faction_ids.append(created_faction.id)
            
        return created_faction_ids
    
    async def _initialize_game_districts(
        self, 
        db: AsyncSession, 
        game_id: str, 
        scenario_id: str
    ) -> List[str]:
        """Initialize districts for a new game based on scenario"""
        # Get districts from scenario
        scenario_districts = await district_repository.list(
            db, 
            filter_dict={"scenario_id": scenario_id}
        )
        
        created_district_ids = []
        
        # Create game district instances for each district template
        for template in scenario_districts:
            # Create game district
            game_district = GameDistrictCreate(
                id=str(uuid.uuid4()),
                game_id=game_id,
                district_template_id=template.id,
                name=template.name,
                description=template.description,
                district_type=template.district_type,
                population=template.population,
                security_level=5,  # Default mid-level security
                unrest_level=0,    # Start with no unrest
                prosperity_level=50,  # Default average prosperity
                heat=0              # Start with no heat/attention
            )
            
            created_district = await game_district_repository.create(
                db, 
                obj_in=game_district.dict()
            )
            created_district_ids.append(created_district.id)
            
            # Set up initial faction control for this district
            # By default, state faction controls most districts
            state_factions = await game_faction_repository.list(
                db,
                filter_dict={"game_id": game_id, "faction_type": "state"}
            )
            
            if state_factions:
                main_state_faction = state_factions[0]
                # Set default 80% control for state faction
                await game_district_repository.update_faction_control(
                    db,
                    created_district.id,
                    main_state_faction.id,
                    80.0,  # 80% control
                    70.0,  # 70% influence
                    10.0   # 10% heat
                )
            
        return created_district_ids
    
    async def _create_initial_snapshot(
        self,
        db: AsyncSession,
        game_id: str
    ) -> None:
        """Create initial game state snapshot"""
        if not self.snapshot_repository:
            return
            
        game = await game_repository.get(db, game_id)
        
        # Get game factions
        factions = await game_faction_repository.get_by_game(db, game_id)
        faction_data = []
        for faction in factions:
            faction_data.append({
                "id": faction.id,
                "name": faction.name,
                "resources": faction.resources,
                "popularity": faction.popularity
            })
            
        # Get game districts
        districts = await game_district_repository.get_by_game(db, game_id)
        district_data = []
        for district in districts:
            # Get faction control data for district
            control_data = await game_district_repository.get_faction_control(
                db, district.id
            )
            
            district_data.append({
                "id": district.id,
                "name": district.name,
                "security_level": district.security_level,
                "unrest_level": district.unrest_level,
                "faction_control": control_data
            })
        
        # Create snapshot
        snapshot = GameStateSnapshot(
            game_id=game_id,
            turn=game.current_turn,
            timestamp=datetime.utcnow(),
            factions=faction_data,
            districts=district_data,
            events=[],
            player_status={
                "resources": {},
                "influence": 0,
                "heat": 0
            }
        )
        
        await self.snapshot_repository.create(snapshot.dict())
    
    async def _create_snapshot(
        self,
        db: AsyncSession,
        game_id: str,
        turn: int
    ) -> None:
        """Create game state snapshot for current turn"""
        if not self.snapshot_repository:
            return
            
        # Similar to _create_initial_snapshot but for regular turns
        # Implementation would be similar but with current game state data
        pass
    
    async def _process_end_of_turn(
        self,
        db: AsyncSession,
        game: Game
    ) -> None:
        """Process end of turn events and calculations"""
        # Process operations
        # Update faction resources
        # Calculate faction relationships
        # Apply district effects
        # Generate end-of-turn events
        pass
    
    async def _process_beginning_of_turn(
        self,
        db: AsyncSession,
        game: Game
    ) -> None:
        """Process beginning of turn events and calculations"""
        # Set up new operations
        # Apply passive effects
        # Generate beginning-of-turn events
        pass
    
    async def _log_game_event(
        self,
        event_type: str,
        game_id: str,
        turn: int,
        title: str,
        description: str,
        affected_entities: Dict[str, List[str]],
        outcome: Dict[str, Any]
    ) -> None:
        """Log a game event"""
        if not self.event_repository:
            return
            
        event = GameEventLog(
            game_id=game_id,
            turn=turn,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            title=title,
            description=description,
            affected_entities=affected_entities,
            outcome=outcome
        )
        
        await self.event_repository.create(event.dict())


# To be instantiated with dependency injection for MongoDB connection
# game_service = GameService(mongo_db)
