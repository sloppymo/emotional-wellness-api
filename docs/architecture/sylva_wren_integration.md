# SYLVA & WREN Integration Architecture

## System Integration Diagram

```mermaid
graph TD
    %% Client and API Layer
    Client[Client Application] --> API[API Gateway]
    API --> Router[FastAPI Router Layer]
    
    %% Middleware Layer
    Router --> Auth[Authentication Middleware]
    Router --> RateLimit[Rate Limiting Middleware]
    Router --> IPWhitelist[IP Whitelisting Middleware]
    Router --> Audit[Audit Logging Middleware]
    
    %% Integration Coordinator
    Auth & RateLimit & IPWhitelist & Audit --> SWCoord[SYLVA-WREN Coordinator]
    
    %% SYLVA Components
    subgraph SYLVA [SYLVA Symbolic Framework]
        CANOPY[CANOPY: Metaphor Extraction]
        ROOT[ROOT: Archetype Analysis]
        MOSS[MOSS: Crisis Detection]
        GROVE[GROVE: Cultural Adaptation]
        MARROW[MARROW: Safety Protocols]
        
        CANOPY --> ROOT
        ROOT --> MOSS
        MOSS --> MARROW
        GROVE --> CANOPY
        GROVE --> ROOT
    end
    
    %% WREN Components
    subgraph WREN [WREN Narrative Engine]
        SceneManager[Scene Lifecycle Manager]
        NarrativeTurn[Narrative Turn Processor]
        SpiritInt[Spirit Interaction Module]
        EmotionReg[Emotional Regulation]
        MemoryPersist[Narrative Memory]
        
        SceneManager --> NarrativeTurn
        NarrativeTurn --> EmotionReg
        EmotionReg --> SpiritInt
        SpiritInt --> MemoryPersist
        MemoryPersist --> SceneManager
    end
    
    %% Integration connections
    SWCoord --> CANOPY
    SWCoord --> ROOT
    SWCoord --> MOSS
    SWCoord --> SceneManager
    SWCoord --> EmotionReg
    
    %% Data Services
    subgraph DataServices [Data Services]
        Redis[Redis Cache]
        PostgreSQL[PostgreSQL Database]
        S3[S3 Storage]
        
        Redis --> PostgreSQL
    end
    
    %% External Services
    subgraph ExternalServices [External Services]
        LLM[Claude 3 Haiku LLM]
        Monitor[Prometheus/CloudWatch]
    end
    
    %% Data connections
    SWCoord <--> Redis
    ROOT <--> Redis
    SceneManager <--> Redis
    MOSS <--> PostgreSQL
    MemoryPersist <--> PostgreSQL
    GROVE <--> S3
    
    %% External service connections
    CANOPY <--> LLM
    SpiritInt <--> LLM
    SWCoord --> Monitor
    
    %% Return path
    SWCoord --> Router
    Router --> API
    API --> Client
```

## Data Flow Specifications

### 1. Emotional Input Processing Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Gateway
    participant SWC as SYLVA-WREN Coordinator
    participant CAN as CANOPY
    participant R as ROOT
    participant SM as Scene Manager
    participant LLM as Claude 3 Haiku
    participant Cache as Redis Cache

    C->>API: POST /emotional-state
    API->>SWC: Forward emotional input
    SWC->>Cache: Check for cached analysis
    
    alt Cache Miss
        SWC->>CAN: Extract metaphors
        CAN->>LLM: Prompt for metaphor extraction
        LLM-->>CAN: Return metaphors
        CAN-->>SWC: Return extracted metaphors
        
        SWC->>R: Map to archetypes
        R->>Cache: Check cached archetypes
        Cache-->>R: Return archetypes or null
        R-->>SWC: Return archetype analysis
        
        SWC->>Cache: Store analysis results
    else Cache Hit
        Cache-->>SWC: Return cached analysis
    end
    
    SWC->>SM: Update narrative scene
    SM-->>SWC: Return updated scene
    
    SWC-->>API: Return integrated response
    API-->>C: Deliver response
```

### 2. Crisis Detection Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Gateway
    participant SWC as SYLVA-WREN Coordinator
    participant CAN as CANOPY
    participant MOSS as MOSS Crisis Detection
    participant MAR as MARROW Safety Protocols
    participant ER as Emotional Regulation
    participant DB as PostgreSQL

    C->>API: POST /message with concerning content
    API->>SWC: Forward message content
    
    SWC->>CAN: Extract metaphors & themes
    CAN-->>SWC: Return extracted elements
    
    SWC->>MOSS: Evaluate crisis indicators
    MOSS->>DB: Log evaluation factors
    MOSS-->>SWC: Return crisis assessment
    
    alt Crisis Detected
        SWC->>MAR: Trigger safety protocol
        MAR-->>SWC: Return safety response
        
        SWC->>ER: Activate regulation workflow
        ER-->>SWC: Return regulation guidance
        
        SWC->>DB: Log crisis intervention
    end
    
    SWC-->>API: Return appropriate response
    API-->>C: Deliver response with appropriate support
```

### 3. Narrative Scene Transition Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Gateway
    participant SWC as SYLVA-WREN Coordinator
    participant SM as Scene Manager
    participant NT as Narrative Turn Processor
    participant SI as Spirit Interaction
    participant R as ROOT
    participant MP as Memory Persistence
    participant Cache as Redis Cache
    participant DB as PostgreSQL

    C->>API: POST /narrative/progress
    API->>SWC: Forward progress request
    
    SWC->>SM: Request scene transition
    SM->>Cache: Get current scene state
    Cache-->>SM: Return scene state
    
    SM->>NT: Process narrative turn
    NT->>R: Get archetype context
    R-->>NT: Return archetype data
    
    NT->>SI: Generate spirit interactions
    SI-->>NT: Return spirit responses
    
    NT-->>SM: Return processed turn
    SM->>MP: Persist narrative changes
    MP->>DB: Store narrative data
    
    SM-->>SWC: Return updated scene
    SWC-->>API: Return narrative progress
    API-->>C: Deliver updated narrative
```

## Key System Interfaces

### 1. SYLVA-WREN Coordinator Interface

```python
class SylvaWrenCoordinator:
    """
    Core integration layer between SYLVA symbolic processing and WREN narrative engine.
    Manages state fusion, symbolic routing, and ensures unified response generation.
    """
    
    async def process_emotional_input(self, input_data: EmotionalInput) -> IntegratedResponse:
        """Process emotional input through both symbolic and narrative systems"""
        
    async def evaluate_crisis_indicators(self, message_content: str, user_context: UserContext) -> CrisisAssessment:
        """Evaluate potential crisis indicators in message content with user context"""
        
    async def progress_narrative(self, user_id: str, scene_id: str, actions: List[UserAction]) -> NarrativeScene:
        """Progress narrative scene based on user actions"""
        
    async def generate_symbolic_response(self, emotional_state: EmotionalState) -> SymbolicResponse:
        """Generate symbolically-informed response based on emotional state"""
        
    async def synchronize_states(self, symbolic_state: SymbolicState, narrative_state: NarrativeState) -> IntegratedState:
        """Synchronize symbolic and narrative states for consistent user experience"""
```

### 2. CANOPY Metaphor Extraction Interface

```python
class CANOPYMetaphorExtractor:
    """
    Extracts metaphors, themes, and symbolic elements from user input.
    """
    
    async def extract_metaphors(self, text: str, user_context: Dict) -> List[Metaphor]:
        """Extract metaphors from text with user context"""
        
    async def classify_themes(self, metaphors: List[Metaphor]) -> List[Theme]:
        """Classify metaphors into thematic groupings"""
        
    async def extract_color_symbolism(self, text: str) -> List[ColorSymbol]:
        """Extract color symbolism from text"""
        
    async def extract_nature_elements(self, text: str) -> List[NatureElement]:
        """Extract nature elements symbolism from text"""
```

### 3. ROOT Archetype Analysis Interface

```python
class ROOTArchetypeAnalyzer:
    """
    Analyzes emotional states and transforms them into archetypal patterns.
    """
    
    async def map_emotions_to_archetypes(self, emotional_state: EmotionalState) -> List[ArchetypeMapping]:
        """Map emotional state to archetypal patterns"""
        
    async def analyze_archetype_transitions(self, timeline: List[ArchetypeMapping]) -> ArchetypeTransitionAnalysis:
        """Analyze transitions between dominant archetypes over time"""
        
    async def get_dominant_archetypes(self, mapping: List[ArchetypeMapping], limit: int = 3) -> List[DominantArchetype]:
        """Get dominant archetypes from mapping with limit"""
        
    async def cached_analyze_with_context(self, emotional_state: EmotionalState, context: UserContext) -> ArchetypeAnalysis:
        """Perform cached, context-aware analysis of emotional state"""
```

### 4. Scene Lifecycle Manager Interface

```python
class SceneLifecycleManager:
    """
    Manages narrative scene creation, transitions, and lifecycle events.
    """
    
    async def create_scene(self, scene_type: SceneType, context: Dict) -> NarrativeScene:
        """Create a new narrative scene with context"""
        
    async def transition_to_next_scene(self, current_scene: NarrativeScene, transition_trigger: TransitionTrigger) -> NarrativeScene:
        """Transition to next scene based on current scene and trigger"""
        
    async def get_available_actions(self, scene: NarrativeScene, user_context: UserContext) -> List[AvailableAction]:
        """Get available actions for the current scene"""
        
    async def resolve_scene_outcome(self, scene: NarrativeScene, actions: List[UserAction]) -> SceneOutcome:
        """Resolve scene outcome based on user actions"""
```

### 5. Emotional Regulation Interface

```python
class EmotionalRegulator:
    """
    Manages emotional regulation workflows and interventions.
    """
    
    async def suggest_regulation_technique(self, emotional_state: EmotionalState, user_preferences: Dict) -> RegulationTechnique:
        """Suggest appropriate regulation technique based on emotional state"""
        
    async def track_regulation_effectiveness(self, technique: RegulationTechnique, before: EmotionalState, after: EmotionalState) -> EffectivenessReport:
        """Track effectiveness of applied regulation technique"""
        
    async def generate_grounding_exercise(self, intensity_level: int, focus_area: str) -> GroundingExercise:
        """Generate grounding exercise based on intensity level and focus area"""
        
    async def create_regulation_narrative(self, emotional_state: EmotionalState, preferred_modality: str) -> RegulationNarrative:
        """Create narrative designed to support emotional regulation"""
```
