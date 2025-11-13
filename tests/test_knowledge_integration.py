"""
Integration Tests for Knowledge Sources Feature
Tests end-to-end flow of additional_inputs through CrewRequest.

Created: 2025-01-13
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from service_types import CrewRequest, CrewA, AgentA, TaskA
from pydantic import ValidationError


class TestCrewRequestWithKnowledge:
    """Test CrewRequest model accepts additional_inputs field."""
    
    def test_request_with_single_additional_input(self):
        """Test CrewRequest accepts single string additional_input."""
        request_data = {
            "$schema": "urn:sd-core:schema.crewai.request.1",
            "name": "test-with-knowledge",
            "crew": {
                "$schema": "urn:sd:schema.icrew.crew.2",
                "name": "Simple Test Crew",
                "placeholders": ["topic"],
                "agents": [{
                    "name": "analyst",
                    "role": "Analyst",
                    "goal": "Analyze {topic}",
                    "backstory": "Expert analyst"
                }],
                "tasks": [{
                    "description": "Analyze {topic}",
                    "expected_output": "Analysis report",
                    "agent": "analyst"
                }]
            },
            "inputs": {"topic": "AI Safety"},
            "additional-inputs": "# Previous Research\n\nKey findings from earlier work..."
        }
        
        req = CrewRequest(**request_data)
        
        assert req.additional_inputs is not None
        assert isinstance(req.additional_inputs, str)
        assert "Previous Research" in req.additional_inputs
        assert req.name == "test-with-knowledge"
        assert req.inputs["topic"] == "AI Safety"
    
    def test_request_with_multiple_additional_inputs(self):
        """Test CrewRequest accepts list of additional_inputs."""
        request_data = {
            "$schema": "urn:sd-core:schema.crewai.request.1",
            "name": "test-multi-knowledge",
            "crew": {
                "$schema": "urn:sd:schema.icrew.crew.2",
                "name": "Analysis Crew",
                "placeholders": ["topic"],
                "agents": [{
                    "name": "analyst",
                    "role": "Analyst",
                    "goal": "Analyze {topic}",
                    "backstory": "Expert"
                }],
                "tasks": [{
                    "description": "Analyze {topic}",
                    "expected_output": "Report",
                    "agent": "analyst"
                }]
            },
            "inputs": {"topic": "Machine Learning"},
            "additional-inputs": [
                "# Deep Research Output\n\nComprehensive findings...",
                "# Expert Profiles\n\nKey experts in the field..."
            ]
        }
        
        req = CrewRequest(**request_data)
        
        assert req.additional_inputs is not None
        assert isinstance(req.additional_inputs, list)
        assert len(req.additional_inputs) == 2
        assert "Deep Research" in req.additional_inputs[0]
        assert "Expert Profiles" in req.additional_inputs[1]
    
    def test_request_without_additional_inputs(self):
        """Test CrewRequest works without additional_inputs (backward compatible)."""
        request_data = {
            "$schema": "urn:sd-core:schema.crewai.request.1",
            "name": "test-no-knowledge",
            "crew": {
                "$schema": "urn:sd:schema.icrew.crew.2",
                "name": "Simple Crew",
                "placeholders": ["topic"],
                "agents": [{
                    "name": "analyst",
                    "role": "Analyst",
                    "goal": "Analyze {topic}",
                    "backstory": "Expert"
                }],
                "tasks": [{
                    "description": "Analyze {topic}",
                    "expected_output": "Report",
                    "agent": "analyst"
                }]
            },
            "inputs": {"topic": "Quantum Computing"}
        }
        
        req = CrewRequest(**request_data)
        
        assert req.additional_inputs is None
        assert req.name == "test-no-knowledge"
        assert req.inputs["topic"] == "Quantum Computing"
    
    def test_request_with_empty_additional_inputs(self):
        """Test CrewRequest handles empty additional_inputs gracefully."""
        request_data = {
            "$schema": "urn:sd-core:schema.crewai.request.1",
            "name": "test-empty-knowledge",
            "crew": {
                "$schema": "urn:sd:schema.icrew.crew.2",
                "name": "Test Crew",
                "placeholders": ["topic"],
                "agents": [{
                    "name": "agent1",
                    "role": "Worker",
                    "goal": "Do work on {topic}",
                    "backstory": "Worker"
                }],
                "tasks": [{
                    "description": "Work on {topic}",
                    "expected_output": "Result",
                    "agent": "agent1"
                }]
            },
            "inputs": {"topic": "Test"},
            "additional-inputs": []
        }
        
        req = CrewRequest(**request_data)
        
        assert req.additional_inputs == []
    
    def test_request_alias_works(self):
        """Test that 'additional-inputs' alias works correctly."""
        # Using alias (with hyphen)
        request_data_alias = {
            "$schema": "urn:sd-core:schema.crewai.request.1",
            "name": "test-alias",
            "crew": {
                "$schema": "urn:sd:schema.icrew.crew.2",
                "name": "Test",
                "placeholders": [],
                "agents": [{
                    "name": "a",
                    "role": "R",
                    "goal": "G",
                    "backstory": "B"
                }],
                "tasks": [{
                    "description": "D",
                    "expected_output": "O",
                    "agent": "a"
                }]
            },
            "inputs": {},
            "additional-inputs": "Test content"
        }
        
        req = CrewRequest(**request_data_alias)
        assert req.additional_inputs == "Test content"
    
    def test_request_with_artifact_urns_and_additional_inputs(self):
        """Test that additional_inputs works alongside artifact_urns."""
        request_data = {
            "$schema": "urn:sd-core:schema.crewai.request.1",
            "name": "test-both-inputs",
            "crew": {
                "$schema": "urn:sd:schema.icrew.crew.2",
                "name": "Test",
                "placeholders": ["topic"],
                "agents": [{
                    "name": "analyst",
                    "role": "Analyst",
                    "goal": "Analyze {topic}",
                    "backstory": "Expert"
                }],
                "tasks": [{
                    "description": "Analyze {topic} using files and knowledge",
                    "expected_output": "Analysis",
                    "agent": "analyst"
                }]
            },
            "inputs": {"topic": "AI"},
            "artifact-urns": ["urn:ivcap:artifact:12345"],
            "additional-inputs": "# Previous Findings\n\nResults from earlier analysis..."
        }
        
        req = CrewRequest(**request_data)
        
        assert req.artifact_urns == ["urn:ivcap:artifact:12345"]
        assert req.additional_inputs is not None
        assert "Previous Findings" in req.additional_inputs


class TestCrewWithKnowledgeSources:
    """Test that crew building accepts knowledge_sources parameter."""
    
    def test_crewa_as_crew_signature_accepts_knowledge_sources(self):
        """Test that CrewA.as_crew() accepts knowledge_sources parameter."""
        # This is more of a smoke test - actual crew building requires
        # full setup (LLM, job context, etc.) which is integration-level
        
        crew_spec = CrewA(
            name="Test Crew",
            placeholders=["topic"],
            agents=[
                AgentA(
                    name="analyst",
                    role="Analyst",
                    goal="Analyze {topic}",
                    backstory="Expert analyst"
                )
            ],
            tasks=[
                TaskA(
                    description="Analyze {topic}",
                    expected_output="Analysis report",
                    agent="analyst"
                )
            ]
        )
        
        # Verify the method signature includes knowledge_sources
        # by checking if it can be called (we won't actually call it here)
        import inspect
        sig = inspect.signature(crew_spec.as_crew)
        params = sig.parameters
        
        assert 'knowledge_sources' in params
        assert params['knowledge_sources'].default is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

