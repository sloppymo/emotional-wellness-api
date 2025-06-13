"""
Unit tests for CANOPY Archetype Mapping System

Tests the archetype identification, mapping, and transformation capabilities of the CANOPY system:
- Basic archetype identification in text
- Context-sensitive archetype mapping
- Multi-archetype interactions and relationships
- Edge cases and malformed inputs
- Caching behavior
- Custom archetype mapping
"""

import pytest
import json
from unittest.mock import patch, MagicMock, call
from datetime import datetime

from src.symbolic.canopy.archetype_mapper import (
    ArchetypeManager,
    ArchetypeMapping,
    ArchetypeProfile,
    ArchetypeIdentifier,
    ArchetypeRelationship,
    RelationshipType,
    SymbolicArchetype
)


class TestArchetypeManager:
    """Tests for the CANOPY ArchetypeManager component"""
    
    @pytest.fixture
    def archetype_manager(self):
        """Create an instance of ArchetypeManager for testing"""
        manager = ArchetypeManager()
        # Ensure test environment doesn't use production cache
        manager._cache.clear()
        return manager
    
    @pytest.fixture
    def sample_text_with_archetypes(self):
        """Sample text containing archetypal patterns"""
        return """
        Sarah felt like she was always guiding her friends through difficult situations.
        Though exhausted, she couldn't stop helping others, feeling responsible for their wellbeing.
        Meanwhile, her own struggles went unaddressed as she focused on solving everyone else's problems.
        """
    
    @pytest.fixture
    def sample_text_multiple_archetypes(self):
        """Sample text with multiple overlapping archetypes"""
        return """
        Despite being new to the team, Michael took charge during the crisis.
        His unconventional approach upset the established order but ultimately saved the project.
        Though some resented his methods, most came to respect his authentic leadership style.
        """
    
    def test_basic_archetype_identification(self, archetype_manager, sample_text_with_archetypes):
        """Test basic identification of archetypes in text"""
        archetypes = archetype_manager.identify_archetypes(sample_text_with_archetypes)
        
        # Should identify at least one archetype
        assert len(archetypes) >= 1
        
        # The Caregiver archetype should be identified
        caregiver_found = any(a.name == "Caregiver" for a in archetypes)
        assert caregiver_found, "Expected to find Caregiver archetype"
        
        # Check for proper structure in returned archetypes
        for archetype in archetypes:
            assert isinstance(archetype, SymbolicArchetype)
            assert isinstance(archetype.name, str)
            assert isinstance(archetype.confidence, float)
            assert 0.0 <= archetype.confidence <= 1.0
            assert isinstance(archetype.text_evidence, list)
            assert len(archetype.text_evidence) > 0
    
    def test_multiple_archetype_identification(self, archetype_manager, sample_text_multiple_archetypes):
        """Test identification of multiple archetypes in the same text"""
        archetypes = archetype_manager.identify_archetypes(sample_text_multiple_archetypes)
        
        # Should identify at least two archetypes
        assert len(archetypes) >= 2
        
        # Hero and Rebel archetypes should be present
        archetype_names = [a.name for a in archetypes]
        assert "Hero" in archetype_names, "Expected to find Hero archetype"
        assert "Rebel" in archetype_names, "Expected to find Rebel archetype"
        
        # Check confidence levels are properly set
        for archetype in archetypes:
            assert 0.0 <= archetype.confidence <= 1.0
    
    def test_archetype_relationships(self, archetype_manager, sample_text_multiple_archetypes):
        """Test identification of relationships between archetypes"""
        archetype_profile = archetype_manager.create_archetype_profile(sample_text_multiple_archetypes)
        
        # Check that the profile contains relationships
        assert len(archetype_profile.relationships) > 0
        
        # Verify relationship structure
        for relationship in archetype_profile.relationships:
            assert isinstance(relationship, ArchetypeRelationship)
            assert isinstance(relationship.source_archetype, str)
            assert isinstance(relationship.target_archetype, str)
            assert isinstance(relationship.relationship_type, RelationshipType)
            assert isinstance(relationship.strength, float)
            assert 0.0 <= relationship.strength <= 1.0
    
    def test_archetype_mapping_with_context(self, archetype_manager):
        """Test that archetype mapping considers contextual information"""
        # Text with ambiguous archetypal content that requires context
        ambiguous_text = "They consistently took what they wanted without asking."
        
        # Different contexts should yield different primary archetypes
        context_1 = "childhood development and learning through play"
        context_2 = "interpersonal boundaries and relationship dynamics"
        
        archetypes_1 = archetype_manager.identify_archetypes(ambiguous_text, context=context_1)
        archetypes_2 = archetype_manager.identify_archetypes(ambiguous_text, context=context_2)
        
        # The primary archetypes should differ based on context
        primary_1 = sorted(archetypes_1, key=lambda a: a.confidence, reverse=True)[0]
        primary_2 = sorted(archetypes_2, key=lambda a: a.confidence, reverse=True)[0]
        
        assert primary_1.name != primary_2.name, "Different contexts should yield different primary archetypes"
    
    def test_archetype_profile_creation(self, archetype_manager, sample_text_with_archetypes):
        """Test creation of a comprehensive archetype profile"""
        profile = archetype_manager.create_archetype_profile(sample_text_with_archetypes)
        
        # Verify profile structure
        assert isinstance(profile, ArchetypeProfile)
        assert isinstance(profile.primary_archetype, SymbolicArchetype)
        assert isinstance(profile.supporting_archetypes, list)
        assert isinstance(profile.shadow_archetypes, list)
        assert isinstance(profile.relationships, list)
        
        # Primary archetype should be the one with highest confidence
        all_archetypes = [profile.primary_archetype] + profile.supporting_archetypes + profile.shadow_archetypes
        highest_confidence = max(all_archetypes, key=lambda a: a.confidence)
        assert profile.primary_archetype == highest_confidence
    
    def test_archetype_mapping_transformation(self, archetype_manager):
        """Test transformation of text based on archetypal mapping"""
        # Source text with specific archetypal framing
        source_text = """
        I always prioritize other people's needs and neglect my own. 
        I can't seem to say no even when I'm exhausted.
        """
        
        # Target archetype for transformation
        target_archetype = "Self-Advocate"
        
        transformed_text = archetype_manager.transform_text_with_archetype(
            source_text, target_archetype
        )
        
        # Transformation should reframe the narrative toward target archetype
        assert transformed_text != source_text
        assert "prioritize" in transformed_text
        assert "needs" in transformed_text
        
        # The transformed text should reflect the target archetype values
        assert "boundaries" in transformed_text.lower() or "self-care" in transformed_text.lower()
    
    def test_caching_behavior(self, archetype_manager, sample_text_with_archetypes):
        """Test caching behavior of archetype identification"""
        # First call should query the model
        with patch.object(archetype_manager, '_identify_archetypes_from_model') as mock_identify:
            mock_identify.return_value = [
                SymbolicArchetype(
                    name="Caregiver", 
                    confidence=0.9,
                    text_evidence=["guiding her friends", "helping others"]
                )
            ]
            
            # First call
            result1 = archetype_manager.identify_archetypes(sample_text_with_archetypes)
            assert mock_identify.call_count == 1
            
            # Second call with same text should use cache
            result2 = archetype_manager.identify_archetypes(sample_text_with_archetypes)
            assert mock_identify.call_count == 1  # Still only called once
            
            # Results should be identical from cache
            assert len(result1) == len(result2)
            assert result1[0].name == result2[0].name
            assert result1[0].confidence == result2[0].confidence
    
    def test_custom_archetype_mapping(self, archetype_manager):
        """Test applying custom archetype mappings"""
        # Create custom mapping
        custom_mapping = ArchetypeMapping(
            source_archetype="Perfectionist",
            target_archetype="Growth Mindset",
            transformation_patterns=[
                ("cannot make mistakes", "can learn from attempts"),
                ("must be flawless", "can improve with practice"),
                ("failure is unacceptable", "setbacks are opportunities")
            ]
        )
        
        # Text with perfectionist framing
        text = "I cannot make mistakes in this presentation. It must be flawless."
        
        # Apply custom mapping
        transformed = archetype_manager.apply_custom_mapping(text, custom_mapping)
        
        # Should replace patterns according to the mapping
        assert "cannot make mistakes" not in transformed
        assert "can learn from attempts" in transformed
        assert "must be flawless" not in transformed
        assert "can improve with practice" in transformed
    
    def test_error_handling(self, archetype_manager):
        """Test handling of invalid inputs"""
        # Empty text
        result = archetype_manager.identify_archetypes("")
        assert len(result) == 0
        
        # None text
        with pytest.raises(ValueError):
            archetype_manager.identify_archetypes(None)
        
        # Invalid target archetype
        with pytest.raises(ValueError):
            archetype_manager.transform_text_with_archetype("Some text", "NonexistentArchetype123")
    
    def test_temporal_changes_in_archetypes(self, archetype_manager):
        """Test identification of archetype patterns across time"""
        texts = [
            "I need to be perfect at everything I do. No mistakes allowed.",
            "I'm trying to accept that mistakes happen, but it's hard to let go.",
            "Today I made a mistake and used it as a learning opportunity."
        ]
        
        # Get archetype profiles for each text
        profiles = [archetype_manager.create_archetype_profile(t) for t in texts]
        
        # Should see evolution in primary archetypes
        assert profiles[0].primary_archetype.name != profiles[2].primary_archetype.name
        
        # Check for temporal shift analysis
        temporal_analysis = archetype_manager.analyze_archetype_evolution(profiles)
        
        assert "shift" in temporal_analysis
        assert "progression" in temporal_analysis
    
    def test_shadow_archetype_identification(self, archetype_manager):
        """Test identification of shadow (repressed) archetypes"""
        text = """
        I always follow the rules and do what's expected of me.
        I never cause any trouble or rock the boat, even when I disagree strongly.
        """
        
        profile = archetype_manager.create_archetype_profile(text)
        
        # Should identify shadow archetypes
        assert len(profile.shadow_archetypes) > 0
        
        # Common shadow archetype for this pattern would be the Rebel
        rebel_shadow = any(a.name == "Rebel" for a in profile.shadow_archetypes)
        assert rebel_shadow, "Expected 'Rebel' as shadow archetype"


class TestArchetypeTransformations:
    """Tests for archetype transformations and clinical applications"""
    
    @pytest.fixture
    def archetype_manager(self):
        """Create an instance of ArchetypeManager for testing"""
        return ArchetypeManager()
    
    def test_therapeutic_reframing(self, archetype_manager):
        """Test therapeutic reframing using archetype transformations"""
        negative_framing = """
        I'm such a failure. Every time I try something new, I mess it up.
        I'll never be good enough no matter how hard I try.
        """
        
        # Transform toward Hero archetype
        transformed = archetype_manager.transform_text_with_archetype(
            negative_framing,
            "Hero"
        )
        
        # Should reframe the narrative in terms of the Hero's journey
        assert "failure" not in transformed.lower()
        assert "journey" in transformed.lower() or "challenge" in transformed.lower()
        assert "strength" in transformed.lower() or "courage" in transformed.lower()
    
    def test_archetype_conflict_resolution(self, archetype_manager):
        """Test resolution strategies for conflicting archetypes"""
        text_with_conflict = """
        Part of me wants to take risks and pursue my dreams,
        but another part is too afraid of failure and keeps me playing it safe.
        """
        
        # Identify conflicting archetypes
        profile = archetype_manager.create_archetype_profile(text_with_conflict)
        
        # Should have conflicting archetypes with opposing relationship
        conflicting = archetype_manager.identify_conflicting_archetypes(profile)
        assert len(conflicting) > 0
        
        # Get resolution strategies
        resolutions = archetype_manager.generate_archetype_integration_strategies(conflicting)
        
        # Should provide concrete integration strategies
        assert len(resolutions) > 0
        for resolution in resolutions:
            assert "strategy" in resolution
            assert "rationale" in resolution
    
    def test_archetype_balance_assessment(self, archetype_manager):
        """Test assessment of archetype balance/imbalance"""
        imbalanced_text = """
        I'm constantly trying to save everyone around me, even when they don't ask for help.
        I feel personally responsible for fixing other people's problems and feel guilty
        if I ever take time for myself instead of helping someone else.
        """
        
        assessment = archetype_manager.assess_archetype_balance(imbalanced_text)
        
        # Should identify caregiver archetype as imbalanced
        assert "imbalance" in assessment
        assert "caregiver" in assessment.lower()
        assert "boundaries" in assessment.lower()


class TestArchetypeClinicalApplications:
    """Tests for clinical applications of the archetype mapping system"""
    
    @pytest.fixture
    def archetype_manager(self):
        """Create an instance of ArchetypeManager for testing"""
        return ArchetypeManager()
    
    def test_archetype_based_intervention_generation(self, archetype_manager):
        """Test generation of clinical interventions based on archetypes"""
        client_text = """
        I keep falling into the same pattern in relationships where I give everything
        to my partner and then feel resentful when they don't appreciate it enough.
        I can't seem to break this cycle even though I know it's happening.
        """
        
        # Generate interventions based on archetype profile
        interventions = archetype_manager.generate_archetype_interventions(client_text)
        
        # Should provide relevant interventions
        assert len(interventions) >= 2
        
        # Check intervention quality
        for intervention in interventions:
            assert "title" in intervention
            assert "description" in intervention
            assert "rationale" in intervention
            assert "technique" in intervention
