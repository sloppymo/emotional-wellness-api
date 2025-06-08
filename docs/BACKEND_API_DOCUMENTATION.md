# Shadowrun GM Dashboard - Backend API Documentation

## Overview

The Shadowrun GM Dashboard backend is a Flask-based REST API that provides comprehensive campaign management capabilities for Shadowrun 6th Edition tabletop RPG sessions. The system supports character management, combat tracking, Matrix operations, AI-powered narrative assistance, image generation, and Slack integration.

## Architecture

### Technology Stack
- **Framework**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **AI Integration**: OpenAI GPT models for narrative assistance
- **Image Generation**: DALL-E, Stable Diffusion, Midjourney
- **Real-time Communication**: Server-Sent Events (SSE)
- **External Integrations**: Slack API, Google Docs API
- **Security**: CORS, security headers, input validation

### Core Components
1. **Session Management**: Multi-user campaign sessions with role-based access
2. **Character System**: Complete SR6E character sheet storage and management
3. **Combat Manager**: Initiative tracking, damage calculation, action logging
4. **Matrix Dashboard**: Virtual reality hacking simulation
5. **DM Review System**: AI response moderation and approval workflow
6. **Image Generation**: AI-powered scene and character visualization
7. **Slack Integration**: Bot-based gameplay and notifications
8. **Character Sheet Integration**: Google Docs and Slack synchronization

## Database Models

### Core Session Models

#### Session
```python
class Session(db.Model):
    """
    Represents a Shadowrun campaign session with GM and player participants.
    Each session maintains its own isolated game state, characters, and narrative.
    """
    id = db.Column(db.String, primary_key=True)  # UUID
    name = db.Column(db.String, nullable=False)  # Campaign/session name
    gm_user_id = db.Column(db.String, nullable=False)  # Game Master's user ID
    created_at = db.Column(db.DateTime, server_default=db.func.now())
```

#### UserRole
```python
class UserRole(db.Model):
    """
    Defines user permissions and roles within each session.
    Supports multiple role types for flexible campaign management.
    """
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, db.ForeignKey('session.id'), nullable=False)
    user_id = db.Column(db.String, nullable=False)  # User identifier
    role = db.Column(db.String, nullable=False)  # 'player', 'gm', 'observer'
```

#### Scene
```python
class Scene(db.Model):
    """
    Stores the current narrative scene state for each session.
    Maintains scene descriptions and environmental context for AI responses.
    """
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, db.ForeignKey('session.id'), nullable=False, unique=True)
    summary = db.Column(db.Text, nullable=False, default="")  # Current scene description
```

### Character Management Models

#### Character
```python
class Character(db.Model):
    """
    Comprehensive character sheet storage for Shadowrun 6E characters.
    Supports all character creation methods (Priority, Karma, Narrative) and
    stores both mechanical stats and narrative elements for rich roleplay.
    """
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, db.ForeignKey('session.id'), nullable=False)
    user_id = db.Column(db.String, nullable=False)  # Player's user ID
    name = db.Column(db.String, nullable=False)  # Character's real name
    handle = db.Column(db.String, nullable=True)  # Street name/alias
    archetype = db.Column(db.String, nullable=True)  # Street Samurai, Decker, Mage, etc.
    
    # JSON Fields:
    attributes = db.Column(db.Text, nullable=True)  # {body, agility, reaction, logic, intuition, willpower, charisma, edge}
    skills = db.Column(db.Text, nullable=True)  # {skill_name: rating, specialization: bonus, ...}
    qualities = db.Column(db.Text, nullable=True)  # {positive: [...], negative: [...], symbolic: [...]}
    gear = db.Column(db.Text, nullable=True)  # [{name, category, rating, availability, cost, description}, ...]
    lifestyle = db.Column(db.Text, nullable=True)  # {type, cost, months_paid, location, contacts, description}
    contacts = db.Column(db.Text, nullable=True)  # [{name, connection, loyalty, archetype, description}, ...]
    narrative_hooks = db.Column(db.Text, nullable=True)  # [{type, description, mechanical_trigger}, ...]
    core_traumas = db.Column(db.Text, nullable=True)  # [{label, description, mechanical_effect}, ...]
    core_strengths = db.Column(db.Text, nullable=True)  # [{label, description, mechanical_effect}, ...]
```

#### Entity
```python
class Entity(db.Model):
    """
    Generic entity system for NPCs, spirits, drones, and other game objects.
    Provides flexible data storage through JSON extra_data field.
    """
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, db.ForeignKey('session.id'), nullable=False)
    name = db.Column(db.String, nullable=False)  # Entity display name
    type = db.Column(db.String, nullable=False)  # 'player', 'npc', 'spirit', 'drone'
    status = db.Column(db.String, nullable=True)  # 'active', 'marked', 'unconscious'
    extra_data = db.Column(db.Text, nullable=True)  # JSON-encoded string for extensibility
```

### Combat System Models

#### Combat
```python
class Combat(db.Model):
    """
    Manages Shadowrun 6E combat encounters with initiative tracking,
    round progression, and combatant management.
    """
    id = db.Column(db.String, primary_key=True)  # UUID
    session_id = db.Column(db.String, db.ForeignKey('session.id'), nullable=False)
    name = db.Column(db.String, nullable=False)  # Combat encounter name
    status = db.Column(db.String, nullable=False, default='setup')  # setup, active, paused, completed
    current_round = db.Column(db.Integer, nullable=False, default=1)
    active_combatant_index = db.Column(db.Integer, nullable=False, default=0)
```

#### Combatant
```python
class Combatant(db.Model):
    """
    Represents individual participants in combat encounters.
    Stores SR6E-specific attributes, condition monitors, and status effects.
    """
    id = db.Column(db.String, primary_key=True)  # UUID
    combat_id = db.Column(db.String, db.ForeignKey('combat.id'), nullable=False)
    name = db.Column(db.String, nullable=False)  # Combatant display name
    type = db.Column(db.String, nullable=False)  # player, npc, spirit, drone
    
    # SR6E Attributes
    initiative = db.Column(db.Integer, nullable=False, default=10)  # Initiative attribute
    initiative_score = db.Column(db.Integer, nullable=False, default=0)  # Current initiative score
    actions = db.Column(db.Integer, nullable=False, default=1)  # Available actions per turn
    reaction = db.Column(db.Integer, nullable=False, default=5)  # Reaction attribute
    intuition = db.Column(db.Integer, nullable=False, default=3)  # Intuition attribute
    edge = db.Column(db.Integer, nullable=False, default=2)  # Maximum Edge
    current_edge = db.Column(db.Integer, nullable=False, default=2)  # Current Edge points
    
    # Condition Monitors
    physical_damage = db.Column(db.Integer, nullable=False, default=0)  # Physical damage taken
    stun_damage = db.Column(db.Integer, nullable=False, default=0)  # Stun damage taken
    physical_monitor = db.Column(db.Integer, nullable=False, default=10)  # Physical condition monitor
    stun_monitor = db.Column(db.Integer, nullable=False, default=10)  # Stun condition monitor
    
    status = db.Column(db.String, nullable=False, default='active')  # active, delayed, unconscious, dead
    tags = db.Column(db.Text, nullable=True)  # JSON array of status effects
    position = db.Column(db.Text, nullable=True)  # JSON {x, y, z} coordinates
```

### Matrix System Models

#### MatrixGrid
```python
class MatrixGrid(db.Model):
    """
    Represents virtual Matrix environments where deckers operate.
    Each grid has security ratings, noise levels, and contains
    multiple interconnected nodes for hacking scenarios.
    """
    id = db.Column(db.String, primary_key=True)  # UUID
    session_id = db.Column(db.String, db.ForeignKey('session.id'), nullable=False)
    name = db.Column(db.String, nullable=False)  # Grid display name
    grid_type = db.Column(db.String, nullable=False)  # public, corporate, private
    security_rating = db.Column(db.Integer, nullable=False, default=3)  # Overall security level
    noise_level = db.Column(db.Integer, nullable=False, default=0)  # Matrix noise modifier
```

#### MatrixNode
```python
class MatrixNode(db.Model):
    """
    Individual nodes within Matrix grids representing hosts, files,
    devices, and data stores. Supports 3D positioning for visual
    Matrix representation and complex node relationships.
    """
    id = db.Column(db.String, primary_key=True)  # UUID
    grid_id = db.Column(db.String, db.ForeignKey('matrix_grid.id'), nullable=False)
    name = db.Column(db.String, nullable=False)  # Node display name
    node_type = db.Column(db.String, nullable=False)  # host, file, device, persona, ice, data
    security = db.Column(db.Integer, nullable=False, default=5)  # Node security rating
    encrypted = db.Column(db.Boolean, nullable=False, default=False)  # Encryption status
    
    # 3D Positioning
    position_x = db.Column(db.Float, nullable=False, default=0)
    position_y = db.Column(db.Float, nullable=False, default=0)
    position_z = db.Column(db.Float, nullable=False, default=0)
    
    discovered = db.Column(db.Boolean, nullable=False, default=False)  # Player discovery status
    compromised = db.Column(db.Boolean, nullable=False, default=False)  # Hack status
    data_payload = db.Column(db.Text, nullable=True)  # JSON data content
    connected_nodes = db.Column(db.Text, nullable=True)  # JSON array of node IDs
```

#### MatrixPersona
```python
class MatrixPersona(db.Model):
    """
    Represents a character's virtual presence in the Matrix.
    Tracks ASDF attributes (Attack, Sleaze, Data Processing, Firewall),
    overwatch scores, and Matrix positioning for hacking scenarios.
    """
    id = db.Column(db.String, primary_key=True)  # UUID
    character_id = db.Column(db.String, nullable=False)  # Associated character
    user_id = db.Column(db.String, nullable=False)  # Player user ID
    grid_id = db.Column(db.String, db.ForeignKey('matrix_grid.id'), nullable=True)  # Current grid
    
    # ASDF Attributes
    attack = db.Column(db.Integer, nullable=False, default=4)  # Attack attribute
    sleaze = db.Column(db.Integer, nullable=False, default=5)  # Sleaze attribute
    data_processing = db.Column(db.Integer, nullable=False, default=6)  # Data Processing attribute
    firewall = db.Column(db.Integer, nullable=False, default=4)  # Firewall attribute
    
    matrix_damage = db.Column(db.Integer, nullable=False, default=0)  # Matrix damage taken
    overwatch_score = db.Column(db.Integer, nullable=False, default=0)  # GOD attention level
    is_running_silent = db.Column(db.Boolean, nullable=False, default=False)  # Stealth mode
    is_hot_sim = db.Column(db.Boolean, nullable=False, default=False)  # Hot-sim VR mode
```

#### IceProgram
```python
class IceProgram(db.Model):
    """
    Represents Intrusion Countermeasures Electronics (ICE) programs
    that defend Matrix nodes from unauthorized access.
    
    ICE Types:
    - patrol: Roams and detects intruders
    - probe: Investigates suspicious activity
    - killer: Attacks detected intruders
    - track: Traces intruder locations
    - tar_baby: Traps and holds intruders
    """
    id = db.Column(db.String, primary_key=True)  # UUID
    grid_id = db.Column(db.String, db.ForeignKey('matrix_grid.id'), nullable=False)
    node_id = db.Column(db.String, db.ForeignKey('matrix_node.id'), nullable=True)  # Assigned node
    name = db.Column(db.String, nullable=False)  # ICE program name
    ice_type = db.Column(db.String, nullable=False)  # patrol, probe, killer, track, tar_baby
    rating = db.Column(db.Integer, nullable=False, default=6)  # ICE program rating
    status = db.Column(db.String, nullable=False, default='active')  # active, alerted, crashed
```

### DM Review System Models

#### PendingResponse
```python
class PendingResponse(db.Model):
    """
    Stores AI-generated responses that require Game Master review before
    being delivered to players. Supports priority-based review queues
    and comprehensive audit trails.
    
    Status Flow: pending -> approved/rejected/edited -> delivered
    Priority Levels: 1=low, 2=medium, 3=high (combat/critical situations)
    """
    id = db.Column(db.String, primary_key=True)  # UUID
    session_id = db.Column(db.String, db.ForeignKey('session.id'), nullable=False)
    user_id = db.Column(db.String, nullable=False)  # Player who triggered the AI response
    context = db.Column(db.Text, nullable=False)  # Original player input/context
    ai_response = db.Column(db.Text, nullable=False)  # Generated AI response
    response_type = db.Column(db.String, nullable=False)  # 'narrative', 'dice_roll', 'npc_action', etc.
    status = db.Column(db.String, nullable=False, default='pending')  # 'pending', 'approved', 'rejected', 'edited'
    dm_notes = db.Column(db.Text, nullable=True)  # DM's notes/comments
    final_response = db.Column(db.Text, nullable=True)  # Final approved/edited response
    priority = db.Column(db.Integer, nullable=False, default=1)  # 1=low, 2=medium, 3=high
```

### Image Generation Models

#### GeneratedImage
```python
class GeneratedImage(db.Model):
    """
    Stores AI-generated scene images with metadata and status tracking.
    Supports multiple image generation providers and comprehensive tagging
    for campaign asset management.
    """
    id = db.Column(db.String, primary_key=True)  # UUID
    session_id = db.Column(db.String, db.ForeignKey('session.id'), nullable=False)
    user_id = db.Column(db.String, nullable=False)  # User who requested the image
    prompt = db.Column(db.Text, nullable=False)  # Original description/prompt
    enhanced_prompt = db.Column(db.Text, nullable=True)  # AI-enhanced prompt for image generation
    image_url = db.Column(db.String, nullable=True)  # URL to generated image
    thumbnail_url = db.Column(db.String, nullable=True)  # URL to thumbnail
    provider = db.Column(db.String, nullable=False)  # 'dalle', 'stable_diffusion', 'midjourney'
    status = db.Column(db.String, nullable=False, default='pending')  # 'pending', 'generating', 'completed', 'failed'
    generation_time = db.Column(db.Float, nullable=True)  # Time taken to generate (seconds)
    tags = db.Column(db.Text, nullable=True)  # JSON: scene tags for categorization
    is_favorite = db.Column(db.Boolean, nullable=False, default=False)
```

## API Endpoints

### Character Management

#### GET /api/session/{session_id}/characters
**Get All Characters in Session**

Retrieves all character sheets for a specific session with comprehensive character data.

**Parameters:**
- `session_id` (path): Session identifier

**Response:**
```json
[
  {
    "id": 1,
    "user_id": "user123",
    "name": "Alex Chen",
    "handle": "Neon",
    "archetype": "Decker",
    "attributes": "{\"body\": 3, \"agility\": 4, \"reaction\": 5, \"logic\": 6, \"intuition\": 4, \"willpower\": 3, \"charisma\": 2, \"edge\": 3}",
    "skills": "{\"hacking\": 6, \"electronics\": 5, \"cybercombat\": 4}",
    "gear": "[{\"name\": \"Cyberdeck\", \"rating\": 6}]",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

#### POST /api/session/{session_id}/character
**Create New Character**

Creates a new character sheet in the specified session.

**Parameters:**
- `session_id` (path): Session identifier

**Request Body:**
```json
{
  "user_id": "user123",
  "name": "Alex Chen",
  "handle": "Neon",
  "archetype": "Decker",
  "attributes": "{\"body\": 3, \"agility\": 4, \"reaction\": 5, \"logic\": 6}",
  "skills": "{\"hacking\": 6, \"electronics\": 5}",
  "gear": "[{\"name\": \"Cyberdeck\", \"rating\": 6}]"
}
```

**Response:**
```json
{
  "status": "success",
  "character_id": 1
}
```

#### GET /api/session/{session_id}/character/{char_id}
**Get Individual Character**

Retrieves detailed character sheet data for a specific character.

**Parameters:**
- `session_id` (path): Session identifier
- `char_id` (path): Character identifier

**Response:**
```json
{
  "id": 1,
  "user_id": "user123",
  "name": "Alex Chen",
  "handle": "Neon",
  "archetype": "Decker",
  "attributes": "{\"body\": 3, \"agility\": 4, \"reaction\": 5}",
  "skills": "{\"hacking\": 6, \"electronics\": 5}",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### PUT /api/session/{session_id}/character/{char_id}
**Update Character Sheet**

Updates an existing character sheet with new data. Supports partial updates.

**Parameters:**
- `session_id` (path): Session identifier
- `char_id` (path): Character identifier

**Request Body:**
```json
{
  "attributes": "{\"body\": 4, \"agility\": 4, \"reaction\": 5}",
  "skills": "{\"hacking\": 7, \"electronics\": 5}"
}
```

**Response:**
```json
{
  "status": "success"
}
```

#### DELETE /api/session/{session_id}/character/{char_id}
**Delete Character**

Permanently removes a character from the session.

**Parameters:**
- `session_id` (path): Session identifier
- `char_id` (path): Character identifier

**Response:**
```json
{
  "status": "deleted"
}
```

### Scene Management

#### GET /api/session/{session_id}/scene
**Get Current Scene**

Retrieves the current narrative scene description for the session.

**Parameters:**
- `session_id` (path): Session identifier

**Response:**
```json
{
  "session_id": "session123",
  "summary": "The team stands in the neon-lit alley behind the Stuffer Shack, rain pattering on the concrete. Corporate security drones circle overhead."
}
```

#### POST /api/session/{session_id}/scene
**Update Scene Description**

Updates the current narrative scene for the session. Only Game Masters can modify scenes.

**Parameters:**
- `session_id` (path): Session identifier

**Request Body:**
```json
{
  "user_id": "gm_user123",
  "summary": "The team enters the abandoned warehouse. Dust motes dance in shafts of light filtering through broken windows."
}
```

**Response:**
```json
{
  "session_id": "session123",
  "summary": "The team enters the abandoned warehouse. Dust motes dance in shafts of light filtering through broken windows."
}
```

### Entity Management

#### GET /api/session/{session_id}/entities
**Get All Entities**

Retrieves all entities (NPCs, spirits, drones, etc.) in the session.

**Parameters:**
- `session_id` (path): Session identifier

**Response:**
```json
[
  {
    "id": 1,
    "name": "Mr. Johnson",
    "type": "npc",
    "status": "active",
    "extra_data": "{\"archetype\": \"Corporate Fixer\", \"connection\": 4, \"loyalty\": 2}"
  },
  {
    "id": 2,
    "name": "Security Drone Alpha",
    "type": "drone",
    "status": "patrolling",
    "extra_data": "{\"pilot\": 3, \"armor\": 6, \"weapons\": [\"SMG\"]}"
  }
]
```

#### POST /api/session/{session_id}/entities
**Create or Update Entity**

Creates a new entity or updates an existing one. Only Game Masters can modify entities.

**Parameters:**
- `session_id` (path): Session identifier

**Request Body (Create):**
```json
{
  "user_id": "gm_user123",
  "name": "Street Samurai",
  "type": "npc",
  "status": "hostile",
  "extra_data": "{\"body\": 6, \"agility\": 5, \"weapons\": [\"Katana\", \"Ares Predator\"]}"
}
```

**Request Body (Update):**
```json
{
  "user_id": "gm_user123",
  "id": 1,
  "name": "Mr. Johnson",
  "status": "suspicious"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Mr. Johnson",
  "type": "npc",
  "status": "suspicious",
  "extra_data": "{\"archetype\": \"Corporate Fixer\"}"
}
```

### DM Review System

#### GET /api/session/{session_id}/pending-responses
**Get Pending AI Responses**

Retrieves all AI-generated responses awaiting Game Master review, sorted by priority.

**Parameters:**
- `session_id` (path): Session identifier
- `user_id` (query): Game Master's user ID for authentication

**Response:**
```json
[
  {
    "id": "response123",
    "user_id": "player456",
    "context": "Player attempts to hack the corporate mainframe",
    "ai_response": "The ICE detects your intrusion attempt. Roll Hacking + Logic [6] vs. Firewall 8.",
    "response_type": "dice_roll",
    "priority": 3,
    "created_at": "2024-01-15T14:30:00Z"
  }
]
```

#### POST /api/session/{session_id}/pending-response/{response_id}/review
**Review AI Response**

Allows Game Masters to approve, reject, or edit AI-generated responses.

**Parameters:**
- `session_id` (path): Session identifier
- `response_id` (path): Response identifier

**Request Body:**
```json
{
  "user_id": "gm_user123",
  "action": "approved",
  "dm_notes": "Good response, approved as-is",
  "final_response": null
}
```

**Request Body (Edit):**
```json
{
  "user_id": "gm_user123",
  "action": "edited",
  "dm_notes": "Modified to increase difficulty",
  "final_response": "The military-grade ICE detects your intrusion. Roll Hacking + Logic [6] vs. Firewall 10 with +2 dice penalty."
}
```

**Response:**
```json
{
  "status": "success",
  "action": "approved"
}
```

### Session Management

#### POST /api/session
**Create New Session**

Creates a new campaign session with the requesting user as Game Master.

**Request Body:**
```json
{
  "name": "Shadows of Neo-Tokyo",
  "gm_user_id": "gm_user123"
}
```

**Response:**
```json
{
  "status": "success",
  "session_id": "session123",
  "name": "Shadows of Neo-Tokyo",
  "gm_user_id": "gm_user123"
}
```

#### POST /api/session/{session_id}/join
**Join Session**

Allows a user to join an existing session as a player.

**Parameters:**
- `session_id` (path): Session identifier

**Request Body:**
```json
{
  "user_id": "player456",
  "role": "player"
}
```

**Response:**
```json
{
  "status": "joined",
  "session_id": "session123",
  "role": "player"
}
```

### Image Generation

#### POST /api/session/{session_id}/generate-image
**Generate Scene Image**

Requests AI generation of a scene image with queuing and status tracking.

**Parameters:**
- `session_id` (path): Session identifier

**Request Body:**
```json
{
  "user_id": "gm_user123",
  "description": "A neon-lit cyberpunk alley with rain-slicked streets and holographic advertisements",
  "style": "cyberpunk",
  "provider": "dalle"
}
```

**Response:**
```json
{
  "status": "queued",
  "image_id": "img123",
  "estimated_time": 30
}
```

#### POST /api/session/{session_id}/generate-image-instant
**Generate Image Instantly**

Generates an image immediately without queuing (for urgent requests).

**Parameters:**
- `session_id` (path): Session identifier

**Request Body:**
```json
{
  "user_id": "gm_user123",
  "description": "Combat scene in a corporate boardroom",
  "style": "realistic"
}
```

**Response:**
```json
{
  "status": "completed",
  "image_id": "img124",
  "image_url": "https://example.com/images/img124.jpg",
  "thumbnail_url": "https://example.com/images/img124_thumb.jpg",
  "generation_time": 25.3
}
```

#### GET /api/session/{session_id}/images
**Get Session Images**

Retrieves all generated images for a session with filtering options.

**Parameters:**
- `session_id` (path): Session identifier
- `status` (query, optional): Filter by status (completed, pending, failed)
- `favorites_only` (query, optional): Show only favorited images

**Response:**
```json
{
  "images": [
    {
      "id": "img123",
      "prompt": "Cyberpunk alley scene",
      "image_url": "https://example.com/images/img123.jpg",
      "thumbnail_url": "https://example.com/images/img123_thumb.jpg",
      "status": "completed",
      "is_favorite": true,
      "created_at": "2024-01-15T16:00:00Z"
    }
  ],
  "total": 1
}
```

### AI and LLM Integration

#### POST /api/llm
**Stream AI Response**

Generates streaming AI responses for narrative assistance.

**Request Body:**
```json
{
  "input": "The player wants to negotiate with the gang leader",
  "session_id": "session123",
  "user_id": "gm_user123",
  "context": "Previous scene context here"
}
```

**Response:** Server-Sent Events stream
```
data: {"type": "token", "content": "The gang leader"}
data: {"type": "token", "content": " leans back"}
data: {"type": "complete", "full_response": "The gang leader leans back in his chair, cybernetic eyes glowing as he considers your offer."}
```

#### POST /api/session/{session_id}/llm-with-review
**AI Response with Review Queue**

Generates AI responses that are queued for Game Master review before delivery.

**Parameters:**
- `session_id` (path): Session identifier

**Request Body:**
```json
{
  "user_id": "player456",
  "input": "I want to hack into the corporate database",
  "context": "Player is in the Matrix, connected to corporate host",
  "response_type": "dice_roll",
  "priority": 2
}
```

**Response:**
```json
{
  "status": "queued_for_review",
  "response_id": "response123",
  "estimated_review_time": "2-5 minutes"
}
```

### Slack Integration

#### POST /api/slack/command
**Handle Slack Slash Commands**

Processes Slack slash commands for bot interactions.

**Request Body:** (Slack webhook format)
```json
{
  "token": "slack_token",
  "team_id": "T123456",
  "channel_id": "C123456",
  "user_id": "U123456",
  "command": "/shadowrun",
  "text": "roll 6d6",
  "response_url": "https://hooks.slack.com/commands/..."
}
```

**Response:**
```json
{
  "response_type": "in_channel",
  "text": "Rolling 6d6: [5, 3, 6, 2, 4, 6] = 3 hits"
}
```

#### POST /api/slack/events
**Handle Slack Events**

Processes Slack events like app mentions and direct messages.

**Request Body:** (Slack Events API format)
```json
{
  "type": "event_callback",
  "event": {
    "type": "app_mention",
    "user": "U123456",
    "text": "<@BOT_ID> generate scene image: corporate office",
    "channel": "C123456"
  }
}
```

### Character Sheet Integration

#### GET /api/session/{session_id}/character-sheets/discover
**Discover Character Sheets**

Scans for available character sheets in connected Google Docs or Slack.

**Parameters:**
- `session_id` (path): Session identifier

**Response:**
```json
{
  "discovered_sheets": [
    {
      "source": "google_docs",
      "document_id": "doc123",
      "title": "Alex Chen - Decker Character Sheet",
      "last_modified": "2024-01-15T12:00:00Z"
    },
    {
      "source": "slack",
      "channel_id": "C123456",
      "message_id": "msg123",
      "character_name": "Neon"
    }
  ]
}
```

#### POST /api/session/{session_id}/character-sheets/import
**Import Character Sheet**

Imports character data from external sources (Google Docs, Slack).

**Parameters:**
- `session_id` (path): Session identifier

**Request Body:**
```json
{
  "source": "google_docs",
  "document_id": "doc123",
  "user_id": "player456"
}
```

**Response:**
```json
{
  "status": "imported",
  "character_id": 1,
  "imported_fields": ["name", "attributes", "skills", "gear"]
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "status": "error",
  "error": "Descriptive error message",
  "error_code": "SPECIFIC_ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

### Common HTTP Status Codes
- **200 OK**: Successful request
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### Error Categories

#### Authentication Errors
- `AUTH_REQUIRED`: Authentication token required
- `INVALID_TOKEN`: Invalid or expired token
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions

#### Validation Errors
- `MISSING_FIELD`: Required field not provided
- `INVALID_FORMAT`: Data format validation failed
- `CONSTRAINT_VIOLATION`: Database constraint violated

#### Resource Errors
- `SESSION_NOT_FOUND`: Session does not exist
- `CHARACTER_NOT_FOUND`: Character does not exist
- `ENTITY_NOT_FOUND`: Entity does not exist

#### System Errors
- `AI_SERVICE_UNAVAILABLE`: AI service temporarily unavailable
- `IMAGE_GENERATION_FAILED`: Image generation service failed
- `DATABASE_ERROR`: Database operation failed

## Rate Limiting

### Limits by Endpoint Category
- **Character Operations**: 100 requests/minute
- **AI/LLM Requests**: 20 requests/minute
- **Image Generation**: 5 requests/minute
- **General API**: 200 requests/minute

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642262400
```

## Security Features

### Security Headers
- **HSTS**: Enforces HTTPS connections
- **Content Security Policy**: Prevents XSS attacks
- **X-Frame-Options**: Prevents clickjacking
- **X-Content-Type-Options**: Prevents MIME sniffing

### Input Validation
- JSON schema validation for all endpoints
- SQL injection prevention through parameterized queries
- XSS prevention through output encoding
- File upload restrictions and scanning

### Authentication & Authorization
- Session-based authentication
- Role-based access control (GM, Player, Observer)
- Permission checks on all sensitive operations
- Audit logging for administrative actions

## Performance Considerations

### Database Optimization
- Indexed foreign keys and frequently queried fields
- Connection pooling for concurrent requests
- Query optimization for complex joins
- Pagination for large result sets

### Caching Strategy
- Session data caching for frequently accessed information
- Image URL caching to reduce generation requests
- AI response caching for common queries

### Monitoring & Logging
- Request/response timing metrics
- Error rate monitoring
- Resource usage tracking
- Structured logging for debugging

## Development and Testing

### Environment Configuration
```bash
# Required Environment Variables
FLASK_ENV=development
DATABASE_URL=sqlite:///shadowrun.db
OPENAI_API_KEY=your_openai_key
SLACK_BOT_TOKEN=your_slack_token
GOOGLE_DOCS_API_KEY=your_google_key

# Optional Configuration
IMAGE_GENERATION_PROVIDER=dalle
MAX_CONCURRENT_REQUESTS=50
RATE_LIMIT_ENABLED=true
```

### Testing
- Unit tests for all database models
- Integration tests for API endpoints
- Mock services for external dependencies
- Load testing for performance validation

### Deployment
- Docker containerization
- Health check endpoints
- Graceful shutdown handling
- Database migration scripts 