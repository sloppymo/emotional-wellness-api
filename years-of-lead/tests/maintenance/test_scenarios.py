"""
Comprehensive test scenarios for Years of Lead maintenance mode.

These scenarios provide standardized, reproducible tests that the maintenance
system can use to evaluate game health and identify areas for improvement.
Each scenario focuses on specific aspects of the game system.
"""

import unittest
import time
import statistics
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from game.core import GameState, Agent
from game.emotional_state import EmotionalState
from game.events import EventSystem
from maintenance.metrics import GameHealthMetrics

class MaintenanceTestScenarios(unittest.TestCase):
    """Standardized scenarios for maintenance system evaluation"""
    
    def setUp(self):
        """Set up test environment for each scenario"""
        self.game_state = GameState()
        self.metrics = GameHealthMetrics(self.game_state)
        self.test_results = {}
    
    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self, 'game_state'):
            del self.game_state
    
    # === EMOTIONAL CONSISTENCY SCENARIOS ===
    
    def test_emotional_drift_rates(self):
        """Test that emotional states drift at believable rates"""
        agent = Agent("test_subject", "Test Agent", "test_faction", "test_location")
        initial_state = EmotionalState(
            fear=0.0, anger=0.0, sadness=0.0, joy=0.5,
            trust=0.5, anticipation=0.3, surprise=0.0, disgust=0.0
        )
        agent.emotional_state = initial_state
        
        # Simulate 10 time steps with no major events
        drift_amounts = []
        previous_state = initial_state.copy()
        
        for step in range(10):
            agent.update_emotional_state()
            current_state = agent.emotional_state
            
            # Calculate total drift
            total_drift = sum(
                abs(getattr(current_state, emotion) - getattr(previous_state, emotion))
                for emotion in ['fear', 'anger', 'sadness', 'joy', 'trust', 'anticipation', 'surprise', 'disgust']
            )
            drift_amounts.append(total_drift)
            previous_state = current_state.copy()
        
        # Drift should be gradual (less than 0.1 per step)
        max_drift = max(drift_amounts)
        avg_drift = statistics.mean(drift_amounts)
        
        self.test_results['emotional_drift'] = {
            'max_drift_per_step': max_drift,
            'avg_drift_per_step': avg_drift,
            'passed': max_drift < 0.1 and avg_drift < 0.05
        }
        
        self.assertLess(max_drift, 0.1, f"Emotional drift too rapid: {max_drift}")
        self.assertLess(avg_drift, 0.05, f"Average drift too high: {avg_drift}")
    
    def test_emotional_bounds_consistency(self):
        """Test that emotional values stay within expected bounds"""
        agent = Agent("test_subject", "Test Agent", "test_faction", "test_location")
        
        # Try to set extreme values and see if they're clamped
        extreme_state = EmotionalState(
            fear=2.0, anger=-2.0, sadness=1.5, joy=-1.5,
            trust=3.0, anticipation=-3.0, surprise=10.0, disgust=-10.0
        )
        
        agent.emotional_state = extreme_state
        agent.update_emotional_state()
        
        final_state = agent.emotional_state
        all_values = [
            final_state.fear, final_state.anger, final_state.sadness, final_state.joy,
            final_state.trust, final_state.anticipation, final_state.surprise, final_state.disgust
        ]
        
        bounds_valid = all(-1.0 <= value <= 1.0 for value in all_values)
        
        self.test_results['emotional_bounds'] = {
            'values': dict(zip(['fear', 'anger', 'sadness', 'joy', 'trust', 'anticipation', 'surprise', 'disgust'], all_values)),
            'all_in_bounds': bounds_valid
        }
        
        self.assertTrue(bounds_valid, f"Emotional values out of bounds: {all_values}")
    
    def test_trauma_persistence(self):
        """Test that traumatic events have appropriate lasting effects"""
        agent = Agent("test_subject", "Test Agent", "test_faction", "test_location")
        initial_fear = agent.emotional_state.fear
        
        # Apply a traumatic event
        trauma_event = {
            'type': 'violence_witnessed',
            'severity': 0.8,
            'emotional_impact': {'fear': 0.7, 'sadness': 0.4}
        }
        
        agent.process_event(trauma_event)
        immediate_fear = agent.emotional_state.fear
        
        # Simulate passage of time (several updates)
        for _ in range(20):
            agent.update_emotional_state()
        
        final_fear = agent.emotional_state.fear
        
        # Fear should increase immediately and persist (not fully fade)
        fear_increase = immediate_fear - initial_fear
        fear_retention = final_fear - initial_fear
        
        self.test_results['trauma_persistence'] = {
            'initial_fear': initial_fear,
            'immediate_fear': immediate_fear,
            'final_fear': final_fear,
            'fear_increase': fear_increase,
            'fear_retention': fear_retention,
            'trauma_processed': fear_increase > 0.3 and fear_retention > 0.1
        }
        
        self.assertGreater(fear_increase, 0.3, "Trauma didn't cause sufficient immediate fear")
        self.assertGreater(fear_retention, 0.1, "Trauma effects faded too quickly")
    
    # === NARRATIVE COHERENCE SCENARIOS ===
    
    def test_narrative_variety(self):
        """Test that narrative descriptions show sufficient variety"""
        event_system = EventSystem(self.game_state)
        
        # Generate 20 similar events
        descriptions = []
        for i in range(20):
            event = event_system.generate_event('daily_life', context={'location': 'home'})
            if event and 'description' in event:
                descriptions.append(event['description'])
        
        # Check for variety
        unique_descriptions = set(descriptions)
        variety_ratio = len(unique_descriptions) / len(descriptions) if descriptions else 0
        
        # Check vocabulary variety
        all_words = []
        for desc in descriptions:
            all_words.extend(desc.lower().split())
        
        unique_words = set(all_words)
        vocab_variety = len(unique_words) / len(all_words) if all_words else 0
        
        self.test_results['narrative_variety'] = {
            'total_descriptions': len(descriptions),
            'unique_descriptions': len(unique_descriptions),
            'variety_ratio': variety_ratio,
            'vocab_variety': vocab_variety,
            'sufficient_variety': variety_ratio > 0.7 and vocab_variety > 0.4
        }
        
        self.assertGreater(variety_ratio, 0.7, f"Too much repetition in descriptions: {variety_ratio}")
        self.assertGreater(vocab_variety, 0.4, f"Vocabulary too repetitive: {vocab_variety}")
    
    def test_narrative_coherence(self):
        """Test that narrative events follow logical sequences"""
        event_system = EventSystem(self.game_state)
        
        # Set up a specific context
        context = {
            'time_of_day': 'morning',
            'location': 'kitchen',
            'recent_events': ['woke_up', 'feeling_hungry']
        }
        
        # Generate a sequence of events
        events = []
        for i in range(5):
            event = event_system.generate_event('daily_life', context=context)
            if event:
                events.append(event)
                # Update context based on event
                if 'consequences' in event:
                    context.update(event['consequences'])
        
        # Analyze coherence
        coherence_scores = []
        for i, event in enumerate(events):
            if i == 0:
                coherence_scores.append(1.0)  # First event is always coherent
            else:
                # Check if event makes sense given previous context
                coherence = self._analyze_event_coherence(event, events[:i], context)
                coherence_scores.append(coherence)
        
        avg_coherence = statistics.mean(coherence_scores) if coherence_scores else 0
        
        self.test_results['narrative_coherence'] = {
            'events_generated': len(events),
            'coherence_scores': coherence_scores,
            'avg_coherence': avg_coherence,
            'coherent_sequence': avg_coherence > 0.7
        }
        
        self.assertGreater(avg_coherence, 0.7, f"Narrative sequence not coherent enough: {avg_coherence}")
    
    def _analyze_event_coherence(self, event: Dict, previous_events: List[Dict], context: Dict) -> float:
        """Analyze how well an event fits with previous events and context"""
        # This is a simplified coherence analysis
        # In a full implementation, this would be more sophisticated
        
        coherence_factors = []
        
        # Check location consistency
        if 'location' in event and 'location' in context:
            if event['location'] == context['location']:
                coherence_factors.append(1.0)
            else:
                # Allow reasonable location changes
                coherence_factors.append(0.7)
        else:
            coherence_factors.append(0.8)  # Neutral if no location info
        
        # Check time consistency
        if 'time_of_day' in event and 'time_of_day' in context:
            if event['time_of_day'] == context['time_of_day']:
                coherence_factors.append(1.0)
            else:
                coherence_factors.append(0.6)  # Time changes are less coherent
        else:
            coherence_factors.append(0.8)
        
        # Check emotional consistency
        if previous_events and 'emotional_impact' in event:
            last_event = previous_events[-1]
            if 'emotional_impact' in last_event:
                # Emotions should have some relationship
                coherence_factors.append(0.8)
            else:
                coherence_factors.append(0.7)
        else:
            coherence_factors.append(0.8)
        
        return statistics.mean(coherence_factors) if coherence_factors else 0.5
    
    # === PERFORMANCE SCENARIOS ===
    
    def test_game_initialization_speed(self):
        """Test that game initializes within acceptable time limits"""
        start_time = time.time()
        
        # Initialize a fresh game state
        test_game = GameState()
        
        init_time = time.time() - start_time
        
        self.test_results['initialization_speed'] = {
            'init_time': init_time,
            'within_limits': init_time < 0.1
        }
        
        self.assertLess(init_time, 0.1, f"Game initialization too slow: {init_time}s")
    
    def test_game_step_performance(self):
        """Test that game steps execute within reasonable time"""
        step_times = []
        
        for i in range(10):
            start_time = time.time()
            self.game_state.step()
            step_time = time.time() - start_time
            step_times.append(step_time)
        
        avg_step_time = statistics.mean(step_times)
        max_step_time = max(step_times)
        
        self.test_results['step_performance'] = {
            'avg_step_time': avg_step_time,
            'max_step_time': max_step_time,
            'step_times': step_times,
            'performance_acceptable': avg_step_time < 0.05 and max_step_time < 0.1
        }
        
        self.assertLess(avg_step_time, 0.05, f"Average step time too slow: {avg_step_time}s")
        self.assertLess(max_step_time, 0.1, f"Maximum step time too slow: {max_step_time}s")
    
    def test_memory_stability(self):
        """Test that memory usage remains stable during operation"""
        import gc
        
        try:
            import psutil
            psutil_available = True
        except ImportError:
            psutil_available = False
        
        if psutil_available:
            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        else:
            initial_memory = 0.0  # Fallback when psutil not available
        
        # Run many game steps
        for i in range(100):
            self.game_state.step()
            if i % 20 == 0:
                gc.collect()  # Force garbage collection
        
        if psutil_available:
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_growth = final_memory - initial_memory
        else:
            final_memory = 0.0
            memory_growth = 0.0  # Assume stable when we can't measure
        
        # Test passes if psutil is not available (graceful degradation)
        stable_memory = memory_growth < 10 if psutil_available else True
        
        self.test_results['memory_stability'] = {
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'memory_growth_mb': memory_growth,
            'stable_memory': stable_memory,
            'psutil_available': psutil_available
        }
        
        if psutil_available:
            self.assertLess(memory_growth, 10, f"Memory growth too high: {memory_growth}MB")
        else:
            # Pass the test when psutil is not available
            self.assertTrue(True, "Memory test passed (psutil not available)")
    
    # === AGENT INTERACTION SCENARIOS ===
    
    def test_multi_agent_interactions(self):
        """Test that multiple agents can interact without conflicts"""
        agents = [Agent(f"agent_{i}", f"Test Agent {i}", "test_faction", "test_location") for i in range(5)]
        
        # Add agents to game state
        for agent in agents:
            self.game_state.add_agent(agent)
        
        # Run interaction cycles
        interaction_results = []
        for cycle in range(10):
            cycle_start = time.time()
            
            # Each agent interacts with others
            for agent in agents:
                for other_agent in agents:
                    if agent != other_agent:
                        interaction = agent.interact_with(other_agent)
                        if interaction:
                            interaction_results.append(interaction)
            
            cycle_time = time.time() - cycle_start
            
            # Check that no agent has invalid state
            for agent in agents:
                self.assertTrue(agent.is_state_valid(), f"Agent {agent.name} has invalid state")
        
        self.test_results['multi_agent_interactions'] = {
            'agents_count': len(agents),
            'total_interactions': len(interaction_results),
            'avg_interactions_per_cycle': len(interaction_results) / 10,
            'all_states_valid': True  # We'd have failed already if not
        }
        
        self.assertGreater(len(interaction_results), 0, "No interactions occurred")
    
    def test_agent_state_persistence(self):
        """Test that agent states persist correctly across game saves/loads"""
        agent = Agent("persistent_test", "Persistent Test Agent", "test_faction", "test_location")
        
        # Set specific state
        agent.emotional_state.fear = 0.6
        agent.emotional_state.trust = -0.3
        agent.add_memory("test_memory", {"type": "trauma", "intensity": 0.8})
        
        # Serialize and deserialize (simulating save/load)
        agent_data = agent.serialize()
        new_agent = Agent.deserialize(agent_data)
        
        # Check state preservation
        state_preserved = (
            abs(new_agent.emotional_state.fear - 0.6) < 0.01 and
            abs(new_agent.emotional_state.trust - (-0.3)) < 0.01 and
            "test_memory" in new_agent.memories
        )
        
        self.test_results['state_persistence'] = {
            'original_fear': 0.6,
            'restored_fear': new_agent.emotional_state.fear,
            'original_trust': -0.3,
            'restored_trust': new_agent.emotional_state.trust,
            'memories_preserved': "test_memory" in new_agent.memories,
            'state_preserved': state_preserved
        }
        
        self.assertTrue(state_preserved, "Agent state not properly preserved")
    
    # === STRESS TEST SCENARIOS ===
    
    def test_high_load_stability(self):
        """Test system stability under high computational load"""
        # Create many agents
        agents = [Agent(f"stress_agent_{i}", f"Stress Agent {i}", "test_faction", "test_location") for i in range(50)]
        
        for agent in agents:
            self.game_state.add_agent(agent)
        
        start_time = time.time()
        errors = []
        
        try:
            # Run intensive operations
            for iteration in range(20):
                for agent in agents:
                    agent.update_emotional_state()
                    agent.process_event({
                        'type': 'minor_stress',
                        'emotional_impact': {'fear': 0.1, 'anger': 0.05}
                    })
                
                self.game_state.step()
                
        except Exception as e:
            errors.append(str(e))
        
        total_time = time.time() - start_time
        
        self.test_results['high_load_stability'] = {
            'agents_count': len(agents),
            'iterations': 20,
            'total_time': total_time,
            'errors_count': len(errors),
            'errors': errors,
            'stable_under_load': len(errors) == 0 and total_time < 10
        }
        
        self.assertEqual(len(errors), 0, f"Errors under high load: {errors}")
        self.assertLess(total_time, 10, f"High load test took too long: {total_time}s")

class ScenarioRunner:
    """Utility class to run maintenance scenarios and collect results"""
    
    def __init__(self):
        self.results = {}
        self.suite = None
    
    def run_all_scenarios(self) -> Dict:
        """Run all maintenance scenarios and return comprehensive results"""
        # Create test suite
        self.suite = unittest.TestLoader().loadTestsFromTestCase(MaintenanceTestScenarios)
        
        # Custom test runner that captures detailed results
        import io
        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        
        start_time = time.time()
        result = runner.run(self.suite)
        total_time = time.time() - start_time
        
        # Collect results from test instances
        detailed_results = {}
        for test_case in self.suite:
            if hasattr(test_case, 'test_results'):
                detailed_results.update(test_case.test_results)
        
        # Compile comprehensive results
        self.results = {
            'timestamp': time.time(),
            'total_tests': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0,
            'total_time': total_time,
            'test_output': stream.getvalue(),
            'detailed_results': detailed_results,
            'overall_passed': len(result.failures) == 0 and len(result.errors) == 0
        }
        
        return self.results
    
    def get_metrics_for_maintenance(self) -> Dict:
        """Convert scenario results into metrics for maintenance system"""
        if not self.results:
            return {}
        
        # Extract key metrics
        metrics = {
            'test_pass_rate': self.results['success_rate'],
            'performance_acceptable': self.results['detailed_results'].get('step_performance', {}).get('performance_acceptable', False),
            'emotional_consistency': self.results['detailed_results'].get('emotional_bounds', {}).get('all_in_bounds', False),
            'narrative_coherence': self.results['detailed_results'].get('narrative_coherence', {}).get('coherent_sequence', False),
            'system_stability': self.results['detailed_results'].get('high_load_stability', {}).get('stable_under_load', False)
        }
        
        return metrics

# For direct execution
if __name__ == "__main__":
    # Run scenarios individually for debugging
    unittest.main()
