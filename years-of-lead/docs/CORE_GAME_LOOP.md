# Core Game Loop Specification

## Turn Structure
- 4 phases per day: Morning, Afternoon, Evening, Night
- Each phase: resolve agent tasks, update states, generate events

## Basic Entities
- Agents: id, name, faction, location, task
- Factions: id, name, resources
- Locations: id, name, security, unrest

## Task Resolution
1. Check agent skill vs task difficulty
2. Roll for success/failure
3. Apply outcomes
4. Generate narrative description