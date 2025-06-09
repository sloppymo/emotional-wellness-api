#!/usr/bin/env python3
"""
Test script for the integrated Years of Lead mission system.

Demonstrates:
- Comprehensive mission types
- Random events during missions  
- Legal tracking system
- Narrative generation
- Mission outcomes and consequences
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from game.core import GameState, Agent, Location, Faction
from game.mission_system import MissionType, MissionComplexity
from game.legal_system import LegalSystem


def test_mission_system():
    """Test the complete mission system integration"""
    
    print("🎮 YEARS OF LEAD - INTEGRATED MISSION SYSTEM TEST")
    print("=" * 60)
    
    # Initialize game state
    print("\n1️⃣ Initializing game state...")
    game_state = GameState()
    game_state.initialize_game()
    
    # Create additional test location with varying security
    print("\n2️⃣ Creating test locations...")
    test_locations = [
        Location("bank_district", "Bank District", security_level=8, unrest_level=3),
        Location("prison_complex", "Federal Prison", security_level=10, unrest_level=1),
        Location("media_center", "Media Broadcasting Center", security_level=6, unrest_level=4)
    ]
    
    for location in test_locations:
        game_state.add_location(location)
    
    # Test different mission types
    print("\n3️⃣ Testing different mission types...")
    
    mission_tests = [
        {
            'type': MissionType.PROPAGANDA_CAMPAIGN,
            'location': 'university_district',
            'faction': 'urban_liberation',
            'agents': ['agent_maria', 'agent_sofia']
        },
        {
            'type': MissionType.INTELLIGENCE_GATHERING,
            'location': 'government_quarter',
            'faction': 'underground',
            'agents': ['agent_ana', 'agent_miguel']
        },
        {
            'type': MissionType.SABOTAGE,
            'location': 'industrial_zone',
            'faction': 'resistance',
            'agents': ['agent_carlos', 'agent_luis']
        },
        {
            'type': MissionType.BANK_ROBBERY,
            'location': 'bank_district',
            'faction': 'resistance',
            'agents': ['agent_carlos', 'agent_luis']
        },
        {
            'type': MissionType.ASSASSINATION,
            'location': 'government_quarter',
            'faction': 'resistance',
            'agents': ['agent_carlos']
        }
    ]
    
    for i, test in enumerate(mission_tests, 1):
        print(f"\n{'='*60}")
        print(f"Mission Test {i}: {test['type'].value}")
        print(f"{'='*60}")
        
        # Create mission
        mission = game_state.create_mission(
            mission_type=test['type'],
            target_location_id=test['location'],
            faction_id=test['faction'],
            difficulty=7,
            description=f"Test {test['type'].value} mission"
        )
        
        # Assign agents
        mission.participants = test['agents']
        
        print(f"📋 Mission created: {mission.id}")
        print(f"   Type: {mission.mission_type.value}")
        print(f"   Location: {game_state.locations[mission.target_location_id].name}")
        print(f"   Faction: {game_state.factions[mission.faction_id].name}")
        print(f"   Agents: {', '.join(game_state.agents[aid].name for aid in mission.participants)}")
        print(f"   Difficulty: {mission.complexity.calculate_difficulty():.2f}")
        
        # Execute mission
        print(f"\n🎯 Executing mission...")
        report = game_state.execute_mission(mission.id)
        
        if report:
            print(f"\n📊 Mission Report:")
            print(f"   Outcome: {report['outcome']}")
            print(f"   Political Impact: {report['political_impact']:.2f}")
            print(f"   Reputation Change: {report['faction_reputation_change']:.2f}")
            
            # Show narrative
            print(f"\n📖 Mission Narrative:")
            for event in report['narrative_summary'][:5]:  # Show first 5 events
                print(f"   - {event}")
            
            # Show crimes committed
            if report['crimes_committed']:
                print(f"\n⚖️  Legal Consequences:")
                print(f"   Crimes recorded: {len(report['crimes_committed'])}")
                
                # Check legal profiles
                legal_system = game_state.legal_system
                for agent_id in test['agents']:
                    if agent_id in legal_system.legal_profiles:
                        profile = legal_system.legal_profiles[agent_id]
                        print(f"   {game_state.agents[agent_id].name}: {profile.legal_status.value}")
            
            # Show casualties/captures
            if report['casualties'] or report['captured_agents']:
                print(f"\n🚨 Agent Losses:")
                if report['casualties']:
                    print(f"   Casualties: {len(report['casualties'])}")
                if report['captured_agents']:
                    print(f"   Captured: {len(report['captured_agents'])}")
            
            # Show resources
            if report['resources_gained']:
                print(f"\n💰 Resources Gained:")
                for resource, amount in report['resources_gained'].items():
                    print(f"   {resource}: {amount}")
    
    # Test legal system interactions
    print(f"\n\n{'='*60}")
    print("4️⃣ Testing Legal System")
    print(f"{'='*60}")
    
    # Check for wanted agents
    wanted_agents = []
    for agent_id, profile in game_state.legal_system.legal_profiles.items():
        if profile.is_wanted():
            agent = game_state.agents[agent_id]
            wanted_agents.append((agent, profile))
    
    if wanted_agents:
        print(f"\n🚔 Wanted Agents:")
        for agent, profile in wanted_agents:
            print(f"   {agent.name}: {profile.legal_status.value}")
            print(f"      Total crimes: {profile.get_total_crimes()}")
            print(f"      Surveillance level: {profile.surveillance_level}/10")
            
            # Attempt arrest on one wanted agent
            if profile.legal_status.value == "wanted":
                print(f"\n   Attempting arrest of {agent.name}...")
                location = game_state.locations[agent.location_id]
                arrested, arrest_record = game_state.legal_system.attempt_arrest(
                    agent, location, force_level="normal"
                )
                
                if arrested:
                    print(f"   ✅ {agent.name} arrested!")
                    
                    # Conduct trial
                    crimes = profile.crime_records[-3:]  # Last 3 crimes
                    trial = game_state.legal_system.conduct_trial(agent, crimes)
                    print(f"\n   ⚖️  Trial Result: {trial.verdict}")
                    
                    if trial.verdict == "guilty":
                        print(f"      Sentence: {trial.sentence_years} turns")
                        
                        # Imprison if convicted
                        prison = game_state.legal_system.imprison_agent(
                            agent, trial.sentence_years
                        )
                        print(f"      Imprisoned at: {prison.facility_name}")
                        print(f"      Security level: {prison.security_level.value}")
                else:
                    print(f"   ❌ {agent.name} escaped arrest!")
                
                break  # Only test one arrest
    
    # Final game state summary
    print(f"\n\n{'='*60}")
    print("5️⃣ Final Game State Summary")
    print(f"{'='*60}")
    
    summary = game_state.get_status_summary()
    print(f"\n📊 Game Status:")
    print(f"   Turn: {summary['turn']}")
    print(f"   Phase: {summary['phase']}")
    print(f"   Active Agents: {summary['active_agents']}/{summary['total_agents']}")
    print(f"   Active Missions: {summary['active_missions']}")
    
    print(f"\n💼 Faction Resources:")
    for faction_id, resources in summary['factions'].items():
        faction_name = game_state.factions[faction_id].name
        print(f"   {faction_name}:")
        for resource, amount in resources.items():
            print(f"      {resource}: {amount}")
    
    print(f"\n📰 Recent Events:")
    for event in summary['recent_narrative'][-5:]:
        print(f"   - {event}")
    
    print(f"\n\n✅ Mission system test complete!")
    

def test_mission_events():
    """Test the mission event generation system"""
    
    print("\n\n🎲 TESTING MISSION EVENT SYSTEM")
    print("=" * 60)
    
    game_state = GameState()
    game_state.initialize_game()
    
    # Create a high-risk mission
    print("\n Creating high-risk assassination mission...")
    mission = game_state.create_mission(
        mission_type=MissionType.ASSASSINATION,
        target_location_id='government_quarter',
        faction_id='resistance',
        difficulty=9
    )
    
    mission.participants = ['agent_carlos', 'agent_luis']
    
    # Execute and watch for events
    print("\n Executing mission with event tracking...")
    report = game_state.execute_mission(mission.id)
    
    if report and report['events_encountered']:
        print(f"\n🎯 Random Events Encountered: {len(report['events_encountered'])}")
        
        # Note: Event details would be in the actual event objects
        # For now we can see them in the narrative
        print("\nEvent narratives:")
        for narrative in report['narrative_summary']:
            if "EVENT:" in narrative:
                print(f"   {narrative}")


if __name__ == "__main__":
    try:
        test_mission_system()
        test_mission_events()
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n" + "="*60)
    print("Test suite complete!")
    print("="*60) 