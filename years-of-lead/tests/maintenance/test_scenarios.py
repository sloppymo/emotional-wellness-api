"""
Comprehensive test scenarios for Years of Lead game system.
These scenarios test narrative coherence, emotional consistency, and game mechanics.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum
import json


class ScenarioType(Enum):
    CHARACTER_CREATION = "character_creation"
    MISSION_EXECUTION = "mission_execution"
    EMOTIONAL_STATE = "emotional_state"
    NARRATIVE_FLOW = "narrative_flow"
    LEGAL_SYSTEM = "legal_system"
    BASE_MANAGEMENT = "base_management"
    RECRUITMENT = "recruitment"
    ECONOMIC_SYSTEM = "economic_system"


@dataclass
class TestScenario:
    """Standardized test scenario structure"""
    id: str
    name: str
    scenario_type: ScenarioType
    description: str
    preconditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    expected_outcomes: Dict[str, Any]
    metrics_to_measure: List[str]
    complexity_score: int  # 1-10 scale
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "scenario_type": self.scenario_type.value,
            "description": self.description,
            "preconditions": self.preconditions,
            "actions": self.actions,
            "expected_outcomes": self.expected_outcomes,
            "metrics_to_measure": self.metrics_to_measure,
            "complexity_score": self.complexity_score
        }


# Comprehensive test scenarios
TEST_SCENARIOS = [
    # Character Creation Scenarios
    TestScenario(
        id="CC001",
        name="Revolutionary Leader Creation",
        scenario_type=ScenarioType.CHARACTER_CREATION,
        description="Test creation of a charismatic revolutionary leader character",
        preconditions={
            "game_state": "new_game",
            "available_backgrounds": ["student_activist", "factory_worker", "intellectual"]
        },
        actions=[
            {"action": "select_background", "value": "student_activist"},
            {"action": "assign_traits", "values": ["charismatic", "idealistic", "hot_headed"]},
            {"action": "distribute_skill_points", "values": {
                "leadership": 8, "rhetoric": 7, "combat": 3, "stealth": 2
            }},
            {"action": "set_emotional_baseline", "values": {
                "hope": 80, "anger": 60, "fear": 20, "guilt": 10
            }}
        ],
        expected_outcomes={
            "character_valid": True,
            "trait_synergy_score": {"min": 0.7},
            "emotional_coherence": {"min": 0.8},
            "skill_distribution_valid": True
        },
        metrics_to_measure=["trait_synergy", "emotional_coherence", "skill_balance"],
        complexity_score=6
    ),
    
    TestScenario(
        id="CC002",
        name="Underground Operative Creation",
        scenario_type=ScenarioType.CHARACTER_CREATION,
        description="Test creation of a stealthy underground operative",
        preconditions={
            "game_state": "new_game",
            "available_backgrounds": ["criminal", "police_informant", "military_deserter"]
        },
        actions=[
            {"action": "select_background", "value": "criminal"},
            {"action": "assign_traits", "values": ["cautious", "pragmatic", "cynical"]},
            {"action": "distribute_skill_points", "values": {
                "stealth": 9, "combat": 5, "forgery": 6, "leadership": 0
            }},
            {"action": "set_emotional_baseline", "values": {
                "hope": 30, "anger": 40, "fear": 60, "guilt": 50
            }}
        ],
        expected_outcomes={
            "character_valid": True,
            "trait_synergy_score": {"min": 0.8},
            "emotional_coherence": {"min": 0.75},
            "skill_specialization_score": {"min": 0.8}
        },
        metrics_to_measure=["trait_synergy", "emotional_coherence", "skill_specialization"],
        complexity_score=7
    ),
    
    # Mission Execution Scenarios
    TestScenario(
        id="ME001",
        name="Propaganda Distribution Mission",
        scenario_type=ScenarioType.MISSION_EXECUTION,
        description="Test low-risk propaganda distribution mission",
        preconditions={
            "character": {"skills": {"stealth": 5, "rhetoric": 7}},
            "mission_type": "propaganda",
            "heat_level": 2,
            "resources": {"pamphlets": 100, "safe_houses": 2}
        },
        actions=[
            {"action": "select_mission", "value": "distribute_pamphlets"},
            {"action": "choose_approach", "value": "stealthy"},
            {"action": "handle_event", "value": "police_patrol", "response": "hide"},
            {"action": "complete_objective", "value": "pamphlets_distributed"}
        ],
        expected_outcomes={
            "mission_success": True,
            "heat_increase": {"max": 2},
            "character_stress": {"max": 30},
            "narrative_events_triggered": {"min": 1}
        },
        metrics_to_measure=["mission_coherence", "risk_reward_balance", "narrative_flow"],
        complexity_score=4
    ),
    
    TestScenario(
        id="ME002",
        name="High-Risk Assassination",
        scenario_type=ScenarioType.MISSION_EXECUTION,
        description="Test high-stakes assassination mission with multiple complications",
        preconditions={
            "character": {"skills": {"combat": 8, "stealth": 6, "planning": 7}},
            "mission_type": "assassination",
            "heat_level": 8,
            "target": {"security_level": "high", "public_figure": True}
        },
        actions=[
            {"action": "select_mission", "value": "assassinate_official"},
            {"action": "planning_phase", "values": ["scout_location", "acquire_weapon", "plan_escape"]},
            {"action": "handle_event", "value": "security_increased", "response": "abort_wait"},
            {"action": "execute_mission", "value": "sniper_approach"},
            {"action": "handle_complication", "value": "witness_spotted", "response": "intimidate"}
        ],
        expected_outcomes={
            "mission_outcomes": ["success", "partial_success", "failure"],
            "heat_increase": {"min": 5},
            "legal_consequences": {"possible": ["murder", "conspiracy"]},
            "emotional_impact": {"guilt": {"min": 20}, "fear": {"min": 30}}
        },
        metrics_to_measure=["mission_coherence", "consequence_severity", "emotional_consistency"],
        complexity_score=9
    ),
    
    # Emotional State Scenarios
    TestScenario(
        id="ES001",
        name="Betrayal Emotional Response",
        scenario_type=ScenarioType.EMOTIONAL_STATE,
        description="Test emotional system response to ally betrayal",
        preconditions={
            "character_emotions": {"hope": 70, "trust": 80, "anger": 30},
            "relationship": {"ally_name": "Marcus", "trust_level": 90}
        },
        actions=[
            {"action": "trigger_event", "value": "ally_betrayal"},
            {"action": "reveal_information", "value": "ally_was_informant"},
            {"action": "player_response", "value": "confront_ally"}
        ],
        expected_outcomes={
            "emotional_changes": {
                "trust": {"decrease": {"min": 40}},
                "anger": {"increase": {"min": 30}},
                "hope": {"decrease": {"min": 20}}
            },
            "relationship_status": "broken",
            "narrative_consequences": ["trust_issues", "paranoia_increase"]
        },
        metrics_to_measure=["emotional_coherence", "relationship_impact", "narrative_consistency"],
        complexity_score=8
    ),
    
    # Legal System Scenarios
    TestScenario(
        id="LS001",
        name="Arrest and Trial Process",
        scenario_type=ScenarioType.LEGAL_SYSTEM,
        description="Test complete arrest, imprisonment, and trial flow",
        preconditions={
            "character_crimes": ["sedition", "assault", "propaganda"],
            "evidence_level": 7,
            "legal_heat": 9
        },
        actions=[
            {"action": "trigger_arrest", "value": "raid_hideout"},
            {"action": "interrogation_response", "values": ["remain_silent", "deny_charges"]},
            {"action": "trial_strategy", "value": "political_defense"},
            {"action": "verdict_received", "value": "guilty_lesser_charges"}
        ],
        expected_outcomes={
            "legal_outcome": ["imprisonment", "execution", "escape"],
            "sentence_length": {"months": {"range": [6, 60]}},
            "organization_impact": {"heat_increase": True, "morale_decrease": True},
            "character_reputation": {"martyr_points": {"min": 20}}
        },
        metrics_to_measure=["legal_coherence", "consequence_proportionality", "narrative_impact"],
        complexity_score=10
    ),
    
    # Base Management Scenarios
    TestScenario(
        id="BM001",
        name="Safe House Network Management",
        scenario_type=ScenarioType.BASE_MANAGEMENT,
        description="Test management of multiple safe houses under pressure",
        preconditions={
            "safe_houses": 3,
            "resources": {"food": 100, "weapons": 20, "money": 5000},
            "heat_levels": {"house_1": 3, "house_2": 7, "house_3": 2}
        },
        actions=[
            {"action": "relocate_resources", "from": "house_2", "to": "house_3"},
            {"action": "upgrade_security", "target": "house_1", "improvement": "hidden_exits"},
            {"action": "handle_raid_warning", "house": "house_2", "response": "evacuate"},
            {"action": "establish_new_base", "location": "abandoned_factory"}
        ],
        expected_outcomes={
            "bases_operational": {"min": 2},
            "resource_preservation": {"min": 0.6},
            "heat_management_score": {"min": 0.7},
            "network_resilience": True
        },
        metrics_to_measure=["resource_efficiency", "risk_management", "strategic_planning"],
        complexity_score=7
    ),
    
    # Recruitment Scenarios
    TestScenario(
        id="RC001",
        name="Mass Recruitment Campaign",
        scenario_type=ScenarioType.RECRUITMENT,
        description="Test recruitment of multiple character types",
        preconditions={
            "organization_reputation": 60,
            "available_resources": {"propaganda": 50, "money": 3000},
            "target_demographics": ["students", "workers", "intellectuals"]
        },
        actions=[
            {"action": "plan_recruitment_campaign", "targets": ["university", "factory"]},
            {"action": "allocate_resources", "distribution": {"propaganda": 30, "money": 2000}},
            {"action": "handle_recruit_vetting", "candidate": "suspicious_volunteer", "decision": "reject"},
            {"action": "integrate_new_members", "count": 12, "training": "basic_ideology"}
        ],
        expected_outcomes={
            "recruitment_success": {"min": 8, "max": 20},
            "infiltrator_risk": {"probability": 0.15},
            "organization_growth": {"min": 0.2},
            "resource_cost_efficiency": {"min": 0.6}
        },
        metrics_to_measure=["recruitment_efficiency", "security_effectiveness", "growth_sustainability"],
        complexity_score=6
    ),
    
    # Economic System Scenarios
    TestScenario(
        id="EC001",
        name="Underground Economy Management",
        scenario_type=ScenarioType.ECONOMIC_SYSTEM,
        description="Test management of illegal funding sources",
        preconditions={
            "funding_sources": ["donations", "robbery", "forgery", "smuggling"],
            "monthly_expenses": 8000,
            "current_funds": 12000
        },
        actions=[
            {"action": "plan_bank_heist", "risk_level": "medium", "expected_take": 50000},
            {"action": "establish_forgery_operation", "investment": 5000},
            {"action": "handle_police_investigation", "response": "suspend_operations"},
            {"action": "diversify_income", "new_source": "protection_racket"}
        ],
        expected_outcomes={
            "financial_stability": {"months_runway": {"min": 3}},
            "income_diversity_score": {"min": 0.6},
            "legal_risk_level": {"max": 8},
            "operation_sustainability": True
        },
        metrics_to_measure=["economic_viability", "risk_reward_ratio", "operational_security"],
        complexity_score=8
    ),
    
    # Narrative Flow Scenarios
    TestScenario(
        id="NF001",
        name="Multi-Chapter Story Arc",
        scenario_type=ScenarioType.NARRATIVE_FLOW,
        description="Test coherent narrative progression across multiple game chapters",
        preconditions={
            "chapter": 3,
            "previous_choices": ["peaceful_protest", "violent_escalation", "underground_focus"],
            "faction_relations": {"moderates": -20, "radicals": +40, "government": -80}
        },
        actions=[
            {"action": "trigger_chapter_event", "value": "government_crackdown"},
            {"action": "player_decision", "value": "go_fully_underground"},
            {"action": "develop_subplot", "value": "internal_faction_conflict"},
            {"action": "resolve_arc", "value": "unite_against_common_enemy"}
        ],
        expected_outcomes={
            "narrative_coherence_score": {"min": 0.8},
            "choice_consequence_alignment": True,
            "subplot_resolution_quality": {"min": 0.7},
            "player_agency_preserved": True
        },
        metrics_to_measure=["narrative_coherence", "choice_impact", "story_satisfaction"],
        complexity_score=10
    )
]


def get_scenarios_by_type(scenario_type: ScenarioType) -> List[TestScenario]:
    """Get all scenarios of a specific type"""
    return [s for s in TEST_SCENARIOS if s.scenario_type == scenario_type]


def get_scenarios_by_complexity(min_complexity: int, max_complexity: int) -> List[TestScenario]:
    """Get scenarios within a complexity range"""
    return [s for s in TEST_SCENARIOS if min_complexity <= s.complexity_score <= max_complexity]


def export_scenarios_json(filename: str = "test_scenarios.json"):
    """Export all scenarios to JSON format"""
    scenarios_dict = {
        "scenarios": [scenario.to_dict() for scenario in TEST_SCENARIOS],
        "total_scenarios": len(TEST_SCENARIOS),
        "scenario_types": [t.value for t in ScenarioType]
    }
    
    with open(filename, 'w') as f:
        json.dump(scenarios_dict, f, indent=2)
    
    return scenarios_dict


if __name__ == "__main__":
    # Display scenario statistics
    print(f"Total test scenarios: {len(TEST_SCENARIOS)}")
    print("\nScenarios by type:")
    for scenario_type in ScenarioType:
        count = len(get_scenarios_by_type(scenario_type))
        print(f"  {scenario_type.value}: {count}")
    
    print("\nComplexity distribution:")
    for i in range(1, 11):
        count = len([s for s in TEST_SCENARIOS if s.complexity_score == i])
        if count > 0:
            print(f"  Level {i}: {count} scenarios")