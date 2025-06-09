# Years of Lead - Turn-based Insurgency Simulator

A text-based strategy game inspired by Liberal Crime Squad and Dwarf Fortress, set during a period of political upheaval. Players manage multiple resistance factions, coordinate agents, and navigate the complex dynamics of insurgency warfare.

## Overview

Years of Lead simulates the "Years of Lead" period of political violence and terrorism in 1970s-1980s Europe. Players control resistance movements fighting against an authoritarian government through:

- **Turn-based Strategy**: Plan operations across multiple phases
- **Faction Coordination**: Manage multiple resistance groups with different goals and resources
- **Agent Management**: Direct individual operatives with unique skills and loyalties
- **Dynamic Events**: Respond to changing political and security situations
- **Narrative Focus**: Rich text-based storytelling with meaningful choices

## Installation

### Prerequisites
- Python 3.8+
- Terminal with 80+ column width

### Setup
```bash
cd /path/to/years-of-lead
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Game
```bash
python3 play_years_of_lead.py
```

## Gameplay

- **Phase-based Turns**: Each turn consists of planning, action, and resolution phases
- **Agent Actions**: Agents automatically perform tasks based on faction goals
- **Event Response**: React to random events that affect the political landscape
- **Resource Management**: Balance money, influence, and personnel across factions

### Factions & Agents
- **The Resistance**: Military-focused insurgency group
- **Urban Liberation**: Student/worker movement with popular support
- **Underground Network**: Information and supply specialists

Each faction has unique strengths, resources, and victory conditions.

### Locations
- **Safe Houses**: Low security, good for planning and recruitment
- **Public Spaces**: Moderate security, opportunities for influence operations
- **Government Districts**: High security, high-value targets

### Actions
- **Propaganda**: Increase faction influence
- **Recruitment**: Expand faction membership
- **Intelligence**: Gather information on government activities
- **Sabotage**: Disrupt government operations
- **Financing**: Secure funding for operations

## Controls

- `status` - View current game state, factions, and agent locations
- `advance` - Progress to next turn phase
- `help` - Show available commands
- `quit` - Exit the game

## Strategy Tips

- **Diversify Operations**: Different factions excel at different mission types
- **Manage Heat**: High-profile operations increase government attention
- **Build Networks**: Coordinate between factions for maximum impact
- **Adapt to Events**: Random events can create opportunities or threaten operations

## Project Structure

```
years-of-lead/
├── src/
│   ├── game/              # Core game engine
│   ├── maintenance/       # Automated maintenance system
│   └── years_of_lead/     # Game-specific logic
├── tests/                 # Test suites
├── config/                # Configuration files
├── play_years_of_lead.py  # Main game launcher
└── requirements.txt       # Python dependencies
```

## Game Systems

- **Faction**: Organizations with resources, goals, and agents
- **Agent**: Individual operatives with skills, equipment, and loyalty
- **Location**: Areas with security levels and ongoing events
- **Mission**: Planned operations requiring multiple agents
- **Equipment**: Weapons, tools, and resources for operations
- **Event System**: Random events that affect locations and factions

## Victory Conditions

Different factions have different paths to victory:

- **Military Victory**: Reduce government control through force
- **Popular Support**: Win hearts and minds of the population
- **Infiltration**: Compromise government institutions from within
- **Economic Disruption**: Undermine the state through targeted strikes

The game ends when:
- A faction achieves its victory condition
- Government successfully suppresses all resistance
- All faction leaders are captured or killed

## Advanced Features

- **Multi-faction Coordination**: Alliance and betrayal mechanics
- **Dynamic Narrative**: Events and outcomes shaped by player choices
- **Faction resource changes and goal updates
- **Agent skill development and loyalty shifts
- **Government counter-intelligence operations

## Future Development

- **Historical Scenarios**: Play through real resistance movements
- **Multiplayer**: Competing resistance factions
- **Extended Campaigns**: Multi-year struggle simulations
- **Mod Support**: Custom factions and scenarios

---

*"In the years of lead, every choice echoes through history..."*
