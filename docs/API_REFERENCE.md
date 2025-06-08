# Shadowrun 6E GM Dashboard - API Reference

## Table of Contents
1. [Authentication](#authentication)
2. [Session Management](#session-management)
3. [Character Management](#character-management)
4. [Combat System](#combat-system)
5. [Matrix Operations](#matrix-operations)
6. [AI Review System](#ai-review-system)
7. [Image Generation](#image-generation)
8. [Slack Integration](#slack-integration)
9. [Character Sheet Integration](#character-sheet-integration)
10. [Analytics & Monitoring](#analytics--monitoring)
11. [Error Handling](#error-handling)
12. [Rate Limiting](#rate-limiting)

---

## Authentication

All API endpoints require proper authentication through Clerk or session-based authentication.

### Headers
```http
Authorization: Bearer <token>
Content-Type: application/json
```

### User Roles
- **GM (Game Master)**: Full access to all endpoints
- **Player**: Limited access to character and session data
- **Observer**: Read-only access to session data

---

## Session Management

### Create Session
Creates a new game session with the specified GM.

```http
POST /api/session
```

**Request Body:**
```json
{
  "name": "Corporate Extraction Run",
  "gm_user_id": "user_123456"
}
```

**Response:**
```json
{
  "session_id": "sess_789abc",
  "name": "Corporate Extraction Run",
  "gm_user_id": "user_123456",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Status Codes:**
- `201 Created`: Session created successfully
- `400 Bad Request`: Missing required fields
- `401 Unauthorized`: Invalid authentication
- `500 Internal Server Error`: Server error

### Join Session
Adds a user to an existing session with specified role.

```http
POST /api/session/{session_id}/join
```

**Request Body:**
```json
{
  "user_id": "user_456789",
  "role": "player"
}
```

**Response:**
```json
{
  "session_id": "sess_789abc",
  "user_id": "user_456789",
  "role": "player",
  "joined_at": "2024-01-15T10:35:00Z"
}
```

### Get Session Users
Retrieves all users in a session with their roles.

```http
GET /api/session/{session_id}/users
```

**Response:**
```json
{
  "users": [
    {
      "user_id": "user_123456",
      "role": "gm",
      "joined_at": "2024-01-15T10:30:00Z"
    },
    {
      "user_id": "user_456789",
      "role": "player",
      "joined_at": "2024-01-15T10:35:00Z"
    }
  ]
}
```

---

## Character Management

### Get Characters
Retrieves all characters in a session.

```http
GET /api/session/{session_id}/characters
```

**Response:**
```json
{
  "characters": [
    {
      "id": 1,
      "user_id": "user_456789",
      "name": "Morgan Blackhawk",
      "handle": "Shadowstrike",
      "archetype": "Street Samurai",
      "attributes": {
        "body": 6,
        "agility": 8,
        "reaction": 7,
        "logic": 3,
        "intuition": 5,
        "willpower": 4,
        "charisma": 3,
        "edge": 4
      },
      "skills": {
        "firearms": 12,
        "melee_combat": 10,
        "stealth": 8,
        "athletics": 6
      },
      "created_at": "2024-01-15T10:40:00Z"
    }
  ]
}
```

### Create Character
Creates a new character in the session.

```http
POST /api/session/{session_id}/character
```

**Request Body:**
```json
{
  "user_id": "user_456789",
  "name": "Morgan Blackhawk",
  "handle": "Shadowstrike",
  "archetype": "Street Samurai",
  "background_seed": "Ex-corporate security",
  "gender": "Non-binary",
  "pronouns": "they/them",
  "essence_anchor": "Family photo",
  "build_method": "priority",
  "attributes": {
    "body": 6,
    "agility": 8,
    "reaction": 7,
    "logic": 3,
    "intuition": 5,
    "willpower": 4,
    "charisma": 3,
    "edge": 4
  },
  "skills": {
    "firearms": 12,
    "melee_combat": 10,
    "stealth": 8,
    "athletics": 6
  },
  "qualities": {
    "positive": ["Ambidextrous", "Combat Reflexes"],
    "negative": ["SINner (Corporate)", "Code of Honor"],
    "symbolic": ["Marked by Shadows"]
  },
  "gear": [
    {
      "name": "Ares Predator VI",
      "type": "weapon",
      "rating": 6,
      "condition": "good"
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "character_id": 1,
  "message": "Character created successfully"
}
```

### Update Character
Updates an existing character's data.

```http
PUT /api/session/{session_id}/character/{character_id}
```

**Request Body:** (Same as Create Character, with only fields to update)

### Delete Character
Removes a character from the session.

```http
DELETE /api/session/{session_id}/character/{character_id}
```

**Response:**
```json
{
  "status": "deleted",
  "message": "Character removed successfully"
}
```

---

## Combat System

### Get Combat Status
Retrieves current combat state for the session.

```http
GET /api/session/{session_id}/combat/status
```

**Response:**
```json
{
  "combat": {
    "id": "combat_123",
    "name": "Corporate Security Encounter",
    "status": "active",
    "current_round": 3,
    "active_combatant_index": 2
  },
  "combatants": [
    {
      "id": "combatant_1",
      "name": "Morgan Blackhawk",
      "type": "player",
      "initiative": 18,
      "actions": 2,
      "physical_damage": 2,
      "stun_damage": 0,
      "physical_monitor": 11,
      "stun_monitor": 10,
      "status": "active",
      "edge": 4,
      "current_edge": 3
    }
  ],
  "round": 3,
  "activeIndex": 2
}
```

### Start Combat
Initiates a new combat encounter.

```http
POST /api/session/{session_id}/combat/start
```

**Request Body:**
```json
{
  "name": "Corporate Security Encounter",
  "combatants": [
    {
      "name": "Morgan Blackhawk",
      "type": "player",
      "initiative": 18,
      "physical_monitor": 11,
      "stun_monitor": 10,
      "edge": 4
    },
    {
      "name": "Security Guard",
      "type": "npc",
      "initiative": 12,
      "physical_monitor": 10,
      "stun_monitor": 9,
      "edge": 2
    }
  ]
}
```

### Apply Damage
Applies damage to a combatant.

```http
POST /api/session/{session_id}/combat/damage
```

**Request Body:**
```json
{
  "combatant_id": "combatant_1",
  "damage_type": "physical",
  "damage_amount": 3,
  "source": "Ares Predator VI",
  "description": "Gunshot wound to the shoulder"
}
```

### Next Turn
Advances combat to the next combatant's turn.

```http
POST /api/session/{session_id}/combat/next-turn
```

**Response:**
```json
{
  "status": "success",
  "current_round": 3,
  "active_combatant_index": 3,
  "active_combatant": {
    "id": "combatant_3",
    "name": "Security Guard",
    "actions_remaining": 1
  }
}
```

---

## Matrix Operations

### Get Matrix Grid
Retrieves the current Matrix grid configuration.

```http
GET /api/session/{session_id}/matrix/grid
```

**Response:**
```json
{
  "grid": {
    "id": "grid_123",
    "name": "Ares Corporate Network",
    "grid_type": "corporate",
    "security_rating": 8,
    "noise_level": 2
  },
  "nodes": [
    {
      "id": "node_1",
      "name": "Payroll Database",
      "node_type": "host",
      "security": 8,
      "encrypted": true,
      "position_x": 0.3,
      "position_y": 0.7,
      "discovered": true,
      "compromised": false
    }
  ],
  "ice": [
    {
      "id": "ice_1",
      "name": "Killer ICE",
      "ice_type": "killer",
      "rating": 8,
      "status": "active",
      "position_x": 0.5,
      "position_y": 0.5
    }
  ],
  "overwatch": 15
}
```

### Create Matrix Node
Adds a new node to the Matrix grid.

```http
POST /api/session/{session_id}/matrix/node
```

**Request Body:**
```json
{
  "name": "Employee Records",
  "node_type": "file",
  "security": 6,
  "encrypted": true,
  "position_x": 0.4,
  "position_y": 0.6,
  "data_payload": {
    "file_type": "personnel_records",
    "size": "large",
    "value": "high"
  }
}
```

### Matrix Action
Performs a Matrix action (hack, search, etc.).

```http
POST /api/session/{session_id}/matrix/action
```

**Request Body:**
```json
{
  "persona_id": "persona_1",
  "action_type": "hack",
  "target_node_id": "node_1",
  "dice_pool": 14,
  "edge_used": false
}
```

**Response:**
```json
{
  "status": "success",
  "result": "success",
  "hits": 4,
  "overwatch_generated": 2,
  "consequences": [
    "Node access granted",
    "Overwatch Score increased by 2"
  ]
}
```

---

## AI Review System

### Get Pending Responses
Retrieves AI responses awaiting GM review.

```http
GET /api/session/{session_id}/pending-responses?user_id={gm_user_id}
```

**Response:**
```json
{
  "items": [
    {
      "id": "response_123",
      "user_id": "user_456789",
      "context": "I want to hack into the corporate database",
      "ai_response": "You jack into the Matrix and begin probing the corporate firewall...",
      "response_type": "matrix_action",
      "priority": 2,
      "created_at": "2024-01-15T11:15:00Z"
    }
  ]
}
```

### Review Response
GM reviews and approves/rejects/edits an AI response.

```http
POST /api/session/{session_id}/pending-response/{response_id}/review
```

**Request Body:**
```json
{
  "action": "edit",
  "final_response": "You carefully probe the corporate firewall, finding a vulnerability in the employee access portal...",
  "dm_notes": "Reduced difficulty to match player's skill level"
}
```

**Response:**
```json
{
  "status": "success",
  "action": "edit",
  "message": "Response reviewed and edited"
}
```

### Get DM Notifications
Retrieves unread notifications for the GM.

```http
GET /api/session/{session_id}/dm/notifications?user_id={gm_user_id}
```

**Response:**
```json
{
  "notifications": [
    {
      "id": 1,
      "pending_response_id": "response_123",
      "notification_type": "new_review",
      "message": "New AI response requires review",
      "created_at": "2024-01-15T11:15:00Z"
    }
  ]
}
```

---

## Image Generation

### Generate Image (Instant)
Generates an image immediately using AI.

```http
POST /api/session/{session_id}/generate-image-instant
```

**Request Body:**
```json
{
  "user_id": "user_123456",
  "prompt": "Neon-lit street market in downtown Seattle, cyberpunk style",
  "provider": "dalle",
  "style_preferences": {
    "style": "cyberpunk_noir",
    "quality": "standard",
    "size": "1024x1024"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "image_id": "img_789",
  "image_url": "https://example.com/generated/image_789.png",
  "generation_time": 8.5,
  "provider": "dalle",
  "revised_prompt": "A bustling neon-lit street market in downtown Seattle..."
}
```

### Get Session Images
Retrieves generated images for a session.

```http
GET /api/session/{session_id}/images?user_id={user_id}&limit=20
```

**Response:**
```json
{
  "status": "success",
  "images": [
    {
      "id": "img_789",
      "prompt": "Neon-lit street market",
      "image_url": "https://example.com/generated/image_789.png",
      "provider": "dalle",
      "status": "completed",
      "created_at": "2024-01-15T11:20:00Z",
      "is_favorite": false,
      "tags": ["street", "market", "cyberpunk"]
    }
  ],
  "count": 1
}
```

### Toggle Image Favorite
Marks an image as favorite or removes favorite status.

```http
POST /api/session/{session_id}/image/{image_id}/favorite
```

**Request Body:**
```json
{
  "user_id": "user_123456",
  "is_favorite": true
}
```

---

## Slack Integration

### Slack Command Handler
Handles Slack slash commands.

```http
POST /api/slack/command
```

**Request Body:** (Slack command payload)
```
command=/sr-session
text=create "Corporate Extraction"
user_id=U123456
channel_id=C789ABC
team_id=T456DEF
```

**Response:**
```json
{
  "response_type": "ephemeral",
  "text": "Session 'Corporate Extraction' created successfully!",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "✅ *Session Created*\nName: Corporate Extraction\nSession ID: sess_789abc"
      }
    }
  ]
}
```

### Slack Events Handler
Handles Slack events (mentions, messages, etc.).

```http
POST /api/slack/events
```

### Slack Interactive Handler
Handles Slack interactive components (buttons, modals).

```http
POST /api/slack/interactive
```

---

## Character Sheet Integration

### Discover Character Sheets
Scans connected platforms for character sheets.

```http
GET /api/session/{session_id}/character-sheets/discover?user_id={user_id}
```

**Response:**
```json
{
  "status": "success",
  "session_id": "sess_789abc",
  "discovered_sheets": {
    "google_docs": [
      {
        "document_id": "doc_123",
        "title": "Morgan Blackhawk - Character Sheet",
        "last_modified": "2024-01-15T10:00:00Z",
        "character_name": "Morgan Blackhawk",
        "confidence": 0.95
      }
    ],
    "slack": [
      {
        "message_id": "msg_456",
        "channel": "C789ABC",
        "timestamp": "2024-01-15T09:30:00Z",
        "character_name": "Alex Rivera",
        "confidence": 0.87
      }
    ]
  }
}
```

### Import Character Sheet
Imports a character sheet from external source.

```http
POST /api/session/{session_id}/character-sheets/import
```

**Request Body:**
```json
{
  "user_id": "user_456789",
  "source_type": "google_docs",
  "source_reference": {
    "document_id": "doc_123",
    "title": "Morgan Blackhawk - Character Sheet"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "character_id": 1,
  "message": "Character sheet imported successfully",
  "sync_enabled": true,
  "wren_copy_created": true
}
```

### Sync All Character Sheets
Synchronizes all character sheets in a session.

```http
POST /api/session/{session_id}/character-sheets/sync-all
```

**Request Body:**
```json
{
  "user_id": "user_123456"
}
```

**Response:**
```json
{
  "status": "success",
  "synced_characters": 3,
  "conflicts_resolved": 1,
  "errors": 0,
  "details": [
    {
      "character_id": 1,
      "status": "synced",
      "changes": ["attributes.edge", "skills.firearms"]
    }
  ]
}
```

---

## Analytics & Monitoring

### Get Session Analytics
Retrieves analytics data for a session.

```http
GET /api/session/{session_id}/analytics/summary
```

**Response:**
```json
{
  "stats": {
    "session_duration": 7200,
    "total_actions": 127,
    "combat_encounters": 3,
    "matrix_runs": 1,
    "npcs_encountered": 12
  },
  "engagement": [
    {
      "id": "user_456789",
      "name": "Morgan",
      "engagement": 85,
      "actions_taken": 42,
      "edge_used": 3
    }
  ],
  "combat": {
    "average_combat_length": 8,
    "hit_rate": 67,
    "edge_usage": 23,
    "total_damage": 156
  }
}
```

### Get Live Monitoring
Retrieves real-time player status.

```http
GET /api/session/{session_id}/monitoring/live
```

**Response:**
```json
{
  "players": [
    {
      "id": "user_456789",
      "name": "Morgan",
      "status": "online",
      "lastSeen": "2 minutes ago",
      "current_action": "Rolling dice",
      "health_status": "healthy",
      "edge_remaining": 3
    }
  ],
  "connections": 4
}
```

### Get Campaign Timeline
Retrieves campaign events and plot threads.

```http
GET /api/session/{session_id}/timeline/events
```

**Response:**
```json
{
  "events": [
    {
      "id": "event_1",
      "title": "Corporate Data Theft",
      "description": "Team successfully infiltrated Ares facility",
      "date": "2024-01-15T14:30:00Z",
      "tags": ["combat", "matrix", "success"]
    }
  ],
  "threads": [
    {
      "id": "thread_1",
      "name": "The Mysterious Mr. Johnson",
      "status": "active",
      "priority": "high"
    }
  ],
  "relationships": [
    {
      "npc_id": "npc_1",
      "player_id": "user_456789",
      "relationship_type": "trusted_contact",
      "strength": 8
    }
  ]
}
```

---

## Error Handling

All API endpoints return consistent error responses:

### Error Response Format
```json
{
  "error": "Error message description",
  "type": "error_type",
  "details": {
    "field": "specific_field_error",
    "code": "ERROR_CODE"
  },
  "timestamp": "2024-01-15T11:30:00Z",
  "request_id": "req_123456"
}
```

### Common Error Codes
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Validation Errors
```json
{
  "error": "Validation failed",
  "type": "validation_error",
  "details": {
    "name": "Name is required",
    "attributes.edge": "Edge must be between 1 and 7"
  }
}
```

---

## Rate Limiting

API endpoints are rate limited to prevent abuse:

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

### Rate Limits by Endpoint Type
- **General API**: 100 requests per minute
- **AI Generation**: 10 requests per minute
- **Image Generation**: 5 requests per minute
- **Slack Integration**: 50 requests per minute

### Rate Limit Exceeded Response
```json
{
  "error": "Rate limit exceeded",
  "type": "rate_limit_error",
  "details": {
    "limit": 100,
    "window": 60,
    "retry_after": 45
  }
}
```

---

## Webhooks

### Slack Webhook Events
The system can send webhook notifications to Slack channels:

```json
{
  "event_type": "combat_started",
  "session_id": "sess_789abc",
  "data": {
    "combat_name": "Corporate Security Encounter",
    "participants": 4,
    "timestamp": "2024-01-15T11:45:00Z"
  }
}
```

### Custom Webhook Configuration
Configure webhooks in your session settings to receive real-time updates about:
- Combat events
- Character updates
- AI response approvals
- Session milestones

---

## SDK and Client Libraries

### JavaScript/TypeScript
```javascript
import { ShadowrunAPI } from '@shadowrun/api-client';

const api = new ShadowrunAPI({
  baseURL: 'http://localhost:5000/api',
  apiKey: 'your-api-key'
});

// Create a session
const session = await api.sessions.create({
  name: 'Corporate Extraction',
  gm_user_id: 'user_123'
});

// Add a character
const character = await api.characters.create(session.session_id, {
  name: 'Morgan Blackhawk',
  archetype: 'Street Samurai'
});
```

### Python
```python
from shadowrun_api import ShadowrunClient

client = ShadowrunClient(
    base_url='http://localhost:5000/api',
    api_key='your-api-key'
)

# Create a session
session = client.sessions.create(
    name='Corporate Extraction',
    gm_user_id='user_123'
)

# Add a character
character = client.characters.create(
    session_id=session['session_id'],
    name='Morgan Blackhawk',
    archetype='Street Samurai'
)
```

---

## Testing

### Test Environment
Use the test environment for development:
```
Base URL: http://localhost:5000/api
Test API Key: test_key_123456
```

### Example Test Requests
```bash
# Create a test session
curl -X POST http://localhost:5000/api/session \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Session", "gm_user_id": "test_user"}'

# Get session info
curl -X GET http://localhost:5000/api/session/test_session/users

# Test AI response
curl -X POST http://localhost:5000/api/session/test_session/llm-with-review \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "context": "Test message", "response_type": "narrative"}'
```

---

For more information, see the [Comprehensive Guide](COMPREHENSIVE_GUIDE.md) or contact the development team. 