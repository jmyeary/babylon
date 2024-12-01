import unittest
from src.babylon.systems.contradiction_analysis import ContradictionAnalysis
from src.babylon.data.models.contradiction import Contradiction, Effect, Entity
from src.babylon.data.models.event import Event

class MockEntity:
    """Mock entity class for testing."""
    def __init__(self, entity_id, entity_type):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.freedom = 1.0
        self.wealth = 1.0
        self.stability = 1.0
        self.power = 1.0

class MockEntityRegistry:
    """Mock entity registry for testing."""
    def __init__(self):
        self.entities = {}
        
    def register_entity(self, entity):
        self.entities[entity.entity_id] = entity
        
    def get_entity(self, entity_id):
        return self.entities.get(entity_id)

class TestContradictionAnalysis(unittest.TestCase):
    """Test cases for the ContradictionAnalysis system."""

    def setUp(self):
        """Set up test fixtures."""
        self.entity_registry = MockEntityRegistry()
        self.game_state = {
            'economy': type('Economy', (), {'gini_coefficient': 0.4, 'unemployment_rate': 0.1})(),
            'politics': type('Politics', (), {'stability_index': 0.5})(),
            'entity_registry': self.entity_registry,
            'event_queue': [],
            'is_player_responsible': False
        }

        # Add mock entities
        upper_class = MockEntity('upper_class', 'Class')
        working_class = MockEntity('working_class', 'Class')
        self.entity_registry.register_entity(upper_class)
        self.entity_registry.register_entity(working_class)

        self.contradiction_analysis = ContradictionAnalysis(self.entity_registry)

    def _create_sample_contradiction(self):
        """Create a sample contradiction for testing."""
        upper_class = Entity('upper_class', 'Class', 'Oppressor')
        working_class = Entity('working_class', 'Class', 'Oppressed')
        entities = [upper_class, working_class]

        return Contradiction(
            id='economic_inequality',
            name='Economic Inequality',
            description='Testing contradiction.',
            entities=entities,
            universality='Universal',
            particularity='Economic',
            principal_contradiction=None,
            principal_aspect=upper_class,
            secondary_aspect=working_class,
            antagonism='Antagonistic',
            intensity='Low',
            state='Active',
            potential_for_transformation='High',
            conditions_for_transformation=['Revolutionary Movement'],
            resolution_methods=['Reform', 'Revolution'],
            resolution_conditions=['Reduce Inequality'],
            effects=[],
            attributes={}
        )

    def test_add_contradiction(self):
        """Test adding a contradiction to the system."""
        contradiction = self._create_sample_contradiction()
        self.contradiction_analysis.add_contradiction(contradiction)
        self.assertIn(contradiction, self.contradiction_analysis.contradictions)

    def test_detect_new_contradictions(self):
        """Test detection of new contradictions."""
        self.game_state['economy'].gini_coefficient = 0.6
        new_contradictions = self.contradiction_analysis.detect_new_contradictions(self.game_state)
        self.assertTrue(len(new_contradictions) > 0)
        self.assertEqual(new_contradictions[0].id, 'economic_inequality')

    def test_update_contradictions(self):
        """Test updating contradiction states."""
        contradiction = self._create_sample_contradiction()
        self.contradiction_analysis.add_contradiction(contradiction)
        self.game_state['economy'].gini_coefficient = 0.5
        
        self.contradiction_analysis.update_contradictions(self.game_state)
        self.assertTrue(len(contradiction.intensity_history) > 0)

    def test_generate_events(self):
        """Test event generation from contradictions."""
        contradiction = self._create_sample_contradiction()
        contradiction.state = 'Active'
        contradiction.intensity = 'High'
        self.contradiction_analysis.contradictions.append(contradiction)
        
        events = self.contradiction_analysis.generate_events(self.game_state)
        self.assertTrue(len(events) > 0)
        self.assertIsInstance(events[0], Event)

    def test_effect_application(self):
        """Test applying effects to entities."""
        effect = Effect(
            target='upper_class',
            attribute='wealth',
            modification_type='Decrease',
            value=0.5,
            description='Test effect'
        )
        
        upper_class = self.entity_registry.get_entity('upper_class')
        initial_wealth = upper_class.wealth
        effect.apply(self.game_state)
        self.assertEqual(upper_class.wealth, initial_wealth - 0.5)

if __name__ == '__main__':
    unittest.main()