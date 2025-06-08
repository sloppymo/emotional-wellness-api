# Shadowrun 6E GM Dashboard - Comprehensive Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Deep Dive](#architecture-deep-dive)
3. [GM Dashboard Features](#gm-dashboard-features)
4. [API Documentation](#api-documentation)
5. [Character Sheet Integration](#character-sheet-integration)
6. [Combat Management System](#combat-management-system)
7. [Matrix Dashboard](#matrix-dashboard)
8. [AI Review System](#ai-review-system)
9. [Slack Integration](#slack-integration)
10. [Database Schema](#database-schema)
11. [Configuration Guide](#configuration-guide)
12. [Development Workflow](#development-workflow)
13. [Troubleshooting](#troubleshooting)

---

## System Overview

The Shadowrun 6E GM Dashboard is a comprehensive campaign management system designed to help Game Masters run immersive Shadowrun 6th Edition campaigns. The system combines traditional tabletop RPG tools with modern technology, including AI assistance, real-time collaboration, and integrated character sheet management.

### Core Philosophy
- **GM-Centric Design**: Every feature is designed to reduce GM workload and enhance storytelling
- **Real-Time Collaboration**: Players and GMs share the same data space with live updates
- **AI-Assisted Gameplay**: AI helps generate content while maintaining GM control through review systems
- **Platform Integration**: Works with existing tools like Google Docs and Slack
- **Shadowrun Authenticity**: All features respect and enhance the cyberpunk atmosphere

### Key Components
1. **Frontend Dashboard** (`shadowrun-interface/components/GMDashboard.tsx`)
2. **Backend API** (`shadowrun-backend/app.py`)
3. **Character Sheet Integration System**
4. **AI Review and Response System**
5. **Combat and Matrix Management**
6. **Analytics and Monitoring Tools**

---

## Architecture Deep Dive

### Technology Stack

#### Frontend
- **React/Next.js**: Modern UI framework with SSR support
- **TypeScript**: Type safety and better developer experience
- **Tailwind CSS**: Utility-first styling with cyberpunk theme
- **Clerk**: Authentication and user management

#### Backend
- **Flask**: Lightweight Python web framework
- **SQLAlchemy**: ORM for database operations
- **SQLite**: Default database (configurable to PostgreSQL)
- **AsyncIO**: Asynchronous operations for AI and external APIs

#### External Integrations
- **OpenAI API**: AI response generation
- **DALL-E**: Image generation
- **Google Docs API**: Character sheet integration
- **Slack API**: Team communication integration

### Data Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GM Dashboard  │◄──►│   Flask API     │◄──►│   Database      │
│   (React)       │    │   (Python)      │    │   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Players       │    │   AI Services   │    │   External APIs │
│   (Browser)     │    │   (OpenAI)      │    │   (Docs/Slack)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## GM Dashboard Features

### 1. Review Queue Manager
**Purpose**: Control AI-generated responses before they reach players

**Key Functions**:
- Queue pending AI responses for review
- Approve, reject, or edit responses
- Priority-based sorting
- Bulk operations for efficiency
- Context preservation for informed decisions

**User Interface**:
- Tabbed interface with filtering by response type
- Real-time update notifications
- Edit-in-place functionality
- Bulk selection checkboxes

### 2. Scene Orchestration
**Purpose**: Manage narrative scenes and environmental conditions

**Key Functions**:
- Create and push scenes to players
- Set mood, time, and location
- Template library for common scenarios
- Environmental effects integration

**Templates Available**:
- Combat Setup
- Matrix Dive
- Social Encounter
- Investigation
- Chase Scene
- Infiltration

### 3. NPC & Faction Tracker
**Purpose**: Manage non-player characters and their relationships

**Key Functions**:
- Create and track NPCs
- Assign faction allegiances
- Monitor mood and status changes
- Relationship mapping
- Quick stat generation

**Status Types**:
- Allied: Helpful to players
- Neutral: No strong opinion
- Hostile: Actively opposing
- Active: Currently involved

### 4. Combat Manager
**Purpose**: Handle Shadowrun 6E combat mechanics

**Key Features**:
- Initiative tracking with drag-reorder
- Turn management and round progression
- Health/damage tracking (Physical/Stun)
- Status effects management
- Action recording and combat log
- Environmental hazard integration

**SR6E Mechanics Supported**:
- Initiative passes
- Edge point tracking
- Condition monitors
- Overflow damage
- Status effects (stunned, unconscious, etc.)

### 5. Character Viewer
**Purpose**: Monitor all player characters in real-time

**Key Features**:
- Grid layout of all player sheets
- Live attribute monitoring
- Edge tracking across characters
- Condition monitor overview
- Equipment status
- Detailed character sheet modal

### 6. Matrix Dashboard
**Purpose**: Visualize and manage Matrix operations

**Key Features**:
- Interactive Matrix grid visualization
- Node management (hosts, files, devices, ICE)
- Overwatch Score monitoring
- ICE program behavior tracking
- Real-time persona tracking

**Matrix Elements**:
- **Hosts**: Corporate systems
- **Files**: Data containers
- **Devices**: Connected hardware
- **ICE**: Intrusion Countermeasures
- **Personas**: User avatars

### 7. Session Analytics
**Purpose**: Track gameplay metrics and player engagement

**Metrics Tracked**:
- Player action frequency
- Combat encounter statistics
- Session duration and pacing
- Player engagement scores
- Success/failure rates
- Action distribution charts

### 8. Live Monitoring
**Purpose**: Real-time player status and activity tracking

**Features**:
- Connection status monitoring
- Current player actions
- Resource tracking (Edge, health, equipment)
- Communication channel monitoring
- Activity feed

### 9. Campaign Timeline
**Purpose**: Track campaign events and plot progression

**Features**:
- Interactive timeline with major events
- Plot thread status tracking
- NPC relationship network
- Session recap generation
- Player backstory integration

### 10. Random Generators
**Purpose**: Generate content on-the-fly for dynamic gameplay

**Generators Available**:
- NPC Generator (stats, backgrounds, motivations)
- Location Generator (with security ratings)
- Run Generator (objectives, complications, payouts)
- Weather/Environment Generator (with game effects)

### 11. GM Tools & Automation
**Purpose**: Quick actions and utilities for common GM tasks

**Tools Included**:
- Dice roller with modifiers
- Quick encounter generation
- Secret reveal system
- Matrix glitch triggers
- Session state management
- Image generation tools

### 12. Slack Broadcast Controls
**Purpose**: Integrate with team communication platforms

**Features**:
- Manual message broadcasting
- Auto-broadcast settings
- Scene change notifications
- Combat result sharing
- Image sharing to channels

---

## API Documentation

### Session Management Endpoints

#### Create Session
```http
POST /api/session
Content-Type: application/json

{
  "name": "Session Name",
  "gm_user_id": "user_123"
}
```

#### Join Session
```http
POST /api/session/{session_id}/join
Content-Type: application/json

{
  "user_id": "user_456",
  "role": "player"
}
```

### Character Management

#### Get Characters
```http
GET /api/session/{session_id}/characters
```

#### Create Character
```http
POST /api/session/{session_id}/character
Content-Type: application/json

{
  "user_id": "user_123",
  "name": "Character Name",
  "archetype": "Street Samurai",
  "attributes": "{\"body\": 6, \"agility\": 8}",
  "skills": "{\"firearms\": 12, \"melee\": 8}"
}
```

### Combat System

#### Get Combat Status
```http
GET /api/session/{session_id}/combat/status
```

#### Start Combat
```http
POST /api/session/{session_id}/combat/start
Content-Type: application/json

{
  "name": "Corporate Security Encounter",
  "combatants": [...]
}
```

### Matrix Operations

#### Get Matrix Grid
```http
GET /api/session/{session_id}/matrix/grid
```

#### Create Matrix Node
```http
POST /api/session/{session_id}/matrix/node
Content-Type: application/json

{
  "name": "Corporate Host",
  "node_type": "host",
  "security": 8,
  "position_x": 0.5,
  "position_y": 0.3
}
```

### AI Review System

#### Get Pending Responses
```http
GET /api/session/{session_id}/pending-responses?user_id={gm_user_id}
```

#### Review Response
```http
POST /api/session/{session_id}/pending-response/{response_id}/review
Content-Type: application/json

{
  "action": "approve|reject|edit",
  "final_response": "Edited response text",
  "dm_notes": "GM notes"
}
```

### Image Generation

#### Generate Image
```http
POST /api/session/{session_id}/generate-image-instant
Content-Type: application/json

{
  "user_id": "user_123",
  "prompt": "Neon-lit street market in downtown Seattle",
  "provider": "dalle",
  "style_preferences": {
    "style": "cyberpunk_noir"
  }
}
```

---

## Character Sheet Integration

### Supported Platforms
1. **Google Docs**: Full read/write integration with OAuth2
2. **Slack**: Message-based character sheets with parsing

### Integration Workflow

#### Discovery Phase
1. Scan connected Google Drive for character sheets
2. Monitor Slack channels for character sheet messages
3. Parse and validate character data
4. Present discovered sheets to GM for import approval

#### Import Process
1. **Google Docs**: 
   - OAuth2 authentication
   - Document parsing with regex patterns
   - Attribute extraction and validation
   - Bi-directional sync setup

2. **Slack**:
   - Message content parsing
   - Structured data extraction
   - Character template matching
   - Manual verification prompts

#### Synchronization
- **Real-time sync**: Updates from external sources reflected immediately
- **Conflict resolution**: GM approval for conflicting changes
- **Version history**: Track all changes with timestamps
- **Backup creation**: WREN-managed copies for reliability

### Character Sheet Schema
```typescript
interface Character {
  // Basic Information
  name: string;
  handle: string;
  archetype: string;
  background_seed: string;
  
  // Core Attributes
  attributes: {
    body: number;
    agility: number;
    reaction: number;
    logic: number;
    intuition: number;
    willpower: number;
    charisma: number;
    edge: number;
  };
  
  // Skills (SR6E skill list)
  skills: Record<string, number>;
  
  // Character Features
  qualities: {
    positive: string[];
    negative: string[];
    symbolic: string[];
  };
  
  // Equipment and Resources
  gear: EquipmentItem[];
  lifestyle: LifestyleData;
  contacts: Contact[];
  
  // Narrative Elements
  narrative_hooks: string[];
  core_traumas: TraumaData[];
  core_strengths: StrengthData[];
}
```

---

## Combat Management System

### Initiative System
Following Shadowrun 6E rules:
1. **Initiative Roll**: Reaction + Intuition + Initiative dice
2. **Initiative Passes**: Multiple actions based on Initiative Score
3. **Turn Order**: Descending Initiative Score order
4. **Edge Integration**: Edge points affect initiative and actions

### Condition Monitors
- **Physical Monitor**: (Body ÷ 2) + 8 boxes
- **Stun Monitor**: (Willpower ÷ 2) + 8 boxes
- **Overflow Damage**: Physical damage beyond Physical Monitor
- **Unconsciousness**: Stun damage exceeding Stun Monitor

### Action Types Supported
1. **Attack Actions**: Firearms, melee, spells
2. **Defense Actions**: Full defense, dodging, blocking
3. **Movement**: Walking, running, sprinting
4. **Matrix Actions**: Hacking, data searches, uploads
5. **Magic Actions**: Spellcasting, summoning, ritual magic
6. **Other Actions**: Equipment use, social interactions

### Status Effects
- **Stunned**: -2 to all actions
- **Unconscious**: Cannot act
- **Prone**: -2 to attacks, +2 to defend
- **Blinded**: -6 to sight-based actions
- **Deafened**: -4 to hearing-based actions

---

## Matrix Dashboard

### Virtual Reality Representation
The Matrix Dashboard provides a 3D-inspired view of the digital landscape:

#### Grid Elements
- **Nodes**: Represented as geometric shapes with security indicators
- **Connections**: Lines showing data pathways between nodes
- **ICE Patrols**: Animated indicators showing security programs
- **Data Streams**: Flowing particles representing information transfer

#### Node Types
1. **Host Nodes**: Corporate systems with high security
2. **File Nodes**: Data containers with access controls
3. **Device Nodes**: IoT and hardware connections
4. **Persona Nodes**: User avatars in the Matrix
5. **ICE Nodes**: Active security programs

#### Security Visualization
- **Color Coding**: Green (low), Yellow (medium), Red (high), Purple (military)
- **Encryption Indicators**: Lock icons for encrypted nodes
- **Compromised States**: Flashing or altered colors for hacked systems
- **Alert Levels**: Visual indicators for security response levels

### Overwatch Score Tracking
- **Real-time Monitoring**: Live updates of accumulating Overwatch
- **Threshold Warnings**: Alerts at 25, 30, and 35 points
- **Action Consequences**: Automatic Overwatch generation for illegal actions
- **Reset Mechanisms**: Admin tools for Overwatch reduction

---

## AI Review System

### Review Workflow
1. **Request Generation**: Player action triggers AI response generation
2. **Queue Placement**: Response placed in GM review queue with priority
3. **GM Review**: GM sees context, AI response, and can approve/reject/edit
4. **Response Delivery**: Approved responses sent to players
5. **History Tracking**: All review decisions logged for campaign continuity

### Priority System
- **Priority 1 (Low)**: General dialogue, description requests
- **Priority 2 (Medium)**: Combat actions, skill tests
- **Priority 3 (High)**: Critical story moments, major NPC interactions

### Review Interface Features
- **Context Preservation**: Full conversation history available
- **Edit-in-Place**: Modify AI responses without starting over
- **Bulk Operations**: Handle multiple reviews simultaneously
- **Response Templates**: Pre-written responses for common situations
- **Auto-Approval**: Optional auto-approval for trusted response types

### AI Provider Integration
- **OpenAI GPT-4**: Primary provider for narrative responses
- **Model Selection**: Choose specific models for different response types
- **Fallback Systems**: Secondary providers for redundancy
- **Custom Prompts**: Tailored prompts for Shadowrun-specific content

---

## Slack Integration

### Slash Commands
- `/sr-session create [name]`: Create new session
- `/sr-session join [session_id]`: Join existing session
- `/sr-ai [prompt]`: Request AI response (requires GM review)
- `/sr-image [description]`: Generate scene image
- `/sr-character [sheet_data]`: Submit character sheet
- `/sr-status`: Show session status and active players

### Bot Capabilities
1. **Session Management**: Create, join, and manage sessions
2. **AI Integration**: Route AI requests through review system
3. **Image Sharing**: Generate and share scene images
4. **Character Sheets**: Parse and import character data
5. **Notifications**: Alert players about session events

### Channel Integration
- **Dedicated Channels**: Each session can have its own Slack channel
- **Cross-Channel Support**: Bot works across multiple channels
- **Permission Management**: Role-based access to commands
- **Message Formatting**: Rich message formatting for game content

---

## Database Schema

### Core Tables

#### Sessions
```sql
CREATE TABLE session (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    gm_user_id TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Characters
```sql
CREATE TABLE character (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    handle TEXT,
    archetype TEXT,
    attributes TEXT, -- JSON
    skills TEXT,     -- JSON
    qualities TEXT,  -- JSON
    gear TEXT,       -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session (id)
);
```

#### Combat System
```sql
CREATE TABLE combat (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'setup',
    current_round INTEGER NOT NULL DEFAULT 1,
    active_combatant_index INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session (id)
);

CREATE TABLE combatant (
    id TEXT PRIMARY KEY,
    combat_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- player, npc, spirit, drone
    initiative INTEGER NOT NULL DEFAULT 10,
    physical_damage INTEGER NOT NULL DEFAULT 0,
    stun_damage INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    FOREIGN KEY (combat_id) REFERENCES combat (id)
);
```

#### Matrix System
```sql
CREATE TABLE matrix_grid (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    name TEXT NOT NULL,
    grid_type TEXT NOT NULL, -- public, corporate, private
    security_rating INTEGER NOT NULL DEFAULT 3,
    noise_level INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES session (id)
);

CREATE TABLE matrix_node (
    id TEXT PRIMARY KEY,
    grid_id TEXT NOT NULL,
    name TEXT NOT NULL,
    node_type TEXT NOT NULL, -- host, file, device, persona, ice
    security INTEGER NOT NULL DEFAULT 5,
    encrypted BOOLEAN NOT NULL DEFAULT FALSE,
    position_x REAL NOT NULL DEFAULT 0,
    position_y REAL NOT NULL DEFAULT 0,
    discovered BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (grid_id) REFERENCES matrix_grid (id)
);
```

#### AI Review System
```sql
CREATE TABLE pending_response (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    context TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    response_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    final_response TEXT,
    priority INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME,
    FOREIGN KEY (session_id) REFERENCES session (id)
);
```

---

## Configuration Guide

### Environment Variables

#### Required Variables
```bash
# AI Integration
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4

# Database
DATABASE_URL=sqlite:///shadowrun.db

# Security
SECRET_KEY=your-secret-key-here
CLERK_SECRET_KEY=your-clerk-secret-key
```

#### Optional Variables
```bash
# Image Generation
DALLE_ENABLED=true
DALLE_MODEL=dall-e-3
DALLE_QUALITY=standard
DALLE_SIZE=1024x1024

# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
SLACK_ENABLED=true

# Google Docs Integration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_DOCS_ENABLED=true

# Feature Flags
ENABLE_AI_REVIEW=true
ENABLE_COMBAT_MANAGER=true
ENABLE_MATRIX_DASHBOARD=true
ENABLE_CHARACTER_SHEETS=true

# Performance
MAX_CONCURRENT_AI_REQUESTS=5
AI_TIMEOUT_SECONDS=30
IMAGE_GENERATION_TIMEOUT=60
```

### Database Configuration
```python
# Default SQLite (development)
SQLALCHEMY_DATABASE_URI = 'sqlite:///shadowrun.db'

# PostgreSQL (production)
SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@localhost/shadowrun'

# MySQL (alternative)
SQLALCHEMY_DATABASE_URI = 'mysql://user:pass@localhost/shadowrun'
```

### Logging Configuration
```python
import logging

# Configure logging levels
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Specific logger configurations
logging.getLogger('shadowrun.ai').setLevel(logging.DEBUG)
logging.getLogger('shadowrun.combat').setLevel(logging.INFO)
logging.getLogger('shadowrun.matrix').setLevel(logging.WARNING)
```

---

## Development Workflow

### Setup Development Environment

1. **Clone Repository**
```bash
git clone <repository-url>
cd shadowrun-gm-dashboard
```

2. **Backend Setup**
```bash
cd shadowrun-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python app.py
```

3. **Frontend Setup**
```bash
cd shadowrun-interface
npm install
npm run dev
```

### Code Organization

#### Backend Structure
```
shadowrun-backend/
├── app.py                 # Main Flask application
├── llm_utils.py          # AI integration utilities
├── image_gen_utils.py    # Image generation utilities
├── slack_integration.py  # Slack bot and API integration
├── integrations/         # External service integrations
│   └── character_sheet_manager.py
├── routes/               # API route modules
├── models/               # Database models
├── utils/                # Utility functions
└── tests/                # Test suites
```

#### Frontend Structure
```
shadowrun-interface/
├── components/
│   ├── GMDashboard.tsx   # Main GM dashboard component
│   ├── character/        # Character creation components
│   └── common/           # Shared UI components
├── pages/                # Next.js pages
├── styles/               # Styling and themes
├── hooks/                # React hooks
├── utils/                # Utility functions
└── tests/                # Frontend tests
```

### Development Guidelines

#### Code Style
- **Python**: Follow PEP 8 with Black formatting
- **TypeScript**: ESLint with Prettier formatting
- **Comments**: Comprehensive JSDoc and Python docstrings
- **Naming**: Descriptive variable and function names

#### Testing Strategy
- **Unit Tests**: Test individual functions and components
- **Integration Tests**: Test API endpoints and data flow
- **E2E Tests**: Test complete user workflows
- **Manual Testing**: GM dashboard functionality testing

#### Git Workflow
1. **Feature Branches**: Create branches for new features
2. **Pull Requests**: Code review before merging
3. **Conventional Commits**: Use semantic commit messages
4. **Release Tags**: Version releases with semantic versioning

### Adding New Features

#### New Dashboard Tab
1. Add tab configuration to `tabs` array in GMDashboard.tsx
2. Create tab content in the main render switch statement
3. Add necessary state variables and data fetching functions
4. Implement corresponding backend API endpoints

#### New API Endpoint
1. Define route in `app.py` or appropriate route module
2. Create database models if needed
3. Implement business logic
4. Add input validation and error handling
5. Write tests for the new endpoint

#### New Integration
1. Create integration module in `integrations/` directory
2. Implement authentication and API communication
3. Add configuration variables to `.env`
4. Create management interface in GM dashboard
5. Add comprehensive error handling and logging

---

## Troubleshooting

### Common Issues

#### Database Connection Errors
```
Error: database is locked
```
**Solution**: Ensure only one instance of the app is running, or switch to PostgreSQL for multi-user access.

#### AI API Timeouts
```
Error: Request timeout after 30 seconds
```
**Solutions**:
- Check API key validity
- Verify internet connection
- Increase timeout in configuration
- Implement retry logic

#### Character Sheet Import Failures
```
Error: Failed to parse character sheet
```
**Solutions**:
- Verify document format matches expected template
- Check OAuth permissions for Google Docs
- Validate character data against schema
- Review parsing regex patterns

#### Slack Integration Issues
```
Error: Invalid request signature
```
**Solutions**:
- Verify Slack signing secret
- Check webhook URL configuration
- Ensure proper request header handling
- Validate timestamp tolerance

### Performance Issues

#### Slow Dashboard Loading
**Potential Causes**:
- Large number of characters or combat participants
- Unoptimized database queries
- Heavy image rendering

**Solutions**:
- Implement pagination for large datasets
- Add database indexes
- Optimize React rendering with useMemo
- Lazy load dashboard tabs

#### Memory Leaks
**Common Sources**:
- Unclosed database connections
- React useEffect without cleanup
- Event listeners not removed

**Prevention**:
- Use connection pooling
- Implement proper useEffect cleanup
- Remove event listeners in component unmount

### Debug Mode

#### Enable Debug Logging
```python
# In app.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Frontend Debug Console
```typescript
// Add to GMDashboard.tsx
console.log('Dashboard state:', {
  activeTab,
  combatants,
  matrixNodes,
  pendingResponses
});
```

#### Database Query Debugging
```python
# Enable SQLAlchemy query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Support and Maintenance

#### Regular Maintenance Tasks
1. **Database Cleanup**: Remove old sessions and temporary data
2. **Log Rotation**: Manage log file sizes
3. **API Key Rotation**: Regularly update API keys
4. **Dependency Updates**: Keep packages current
5. **Backup Creation**: Regular database backups

#### Monitoring
- **Error Tracking**: Implement error reporting service
- **Performance Monitoring**: Track response times and resource usage
- **User Analytics**: Monitor feature usage and adoption
- **Uptime Monitoring**: Ensure service availability

#### Documentation Updates
- Keep API documentation current with code changes
- Update configuration guides when adding new features
- Maintain troubleshooting guide with new issues
- Create video tutorials for complex workflows

---

## Conclusion

The Shadowrun 6E GM Dashboard represents a comprehensive solution for modern tabletop RPG management. By combining traditional GM tools with modern technology, it enables Game Masters to focus on storytelling while the system handles the mechanical complexity.

### Key Benefits
- **Reduced Preparation Time**: AI assistance and automation reduce session prep
- **Enhanced Player Experience**: Real-time updates and visual aids improve immersion
- **Consistent Rule Application**: Automated calculations ensure fair gameplay
- **Campaign Continuity**: Persistent data and analytics support long-term campaigns
- **Platform Integration**: Works with existing tools and workflows

### Future Development
The system is designed for extensibility, with planned features including:
- Advanced AI integration with custom models
- VR/AR support for immersive Matrix visualization
- Mobile companion apps for players
- Integration with additional platforms and tools
- Enhanced analytics and campaign insights

For technical support, feature requests, or contributions, please refer to the project repository and community guidelines. 