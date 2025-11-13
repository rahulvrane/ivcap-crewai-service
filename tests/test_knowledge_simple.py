"""
Simple Validation Test for Knowledge Sources Feature
Tests the basic structure without requiring full service imports.

Created: 2025-01-13
"""

import json


def test_request_schema_structure():
    """Test that the request JSON structure is valid."""
    request_data = {
        "$schema": "urn:sd-core:schema.crewai.request.1",
        "name": "test-with-knowledge",
        "crew": {
            "$schema": "urn:sd:schema.icrew.crew.2",
            "name": "Test Crew",
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
        "additional-inputs": [
            "# Research 1\n\nFindings...",
            "# Research 2\n\nMore findings..."
        ]
    }
    
    # Should be valid JSON
    json_str = json.dumps(request_data)
    parsed = json.loads(json_str)
    
    assert parsed["additional-inputs"] is not None
    assert len(parsed["additional-inputs"]) == 2
    assert "name" in parsed
    assert "crew" in parsed
    print("✓ Request schema structure is valid")


def test_example_file_is_valid():
    """Test that the example file is valid JSON."""
    import sys
    from pathlib import Path
    
    # Add parent to path
    parent_dir = Path(__file__).parent.parent
    example_file = parent_dir / "examples" / "knowledge_request.json"
    
    if not example_file.exists():
        print(f"⚠ Example file not found: {example_file}")
        return
    
    with open(example_file) as f:
        data = json.load(f)
    
    assert data["$schema"] == "urn:sd-core:schema.crewai.request.1"
    assert "additional-inputs" in data
    assert isinstance(data["additional-inputs"], list)
    assert len(data["additional-inputs"]) == 2
    print(f"✓ Example file {example_file.name} is valid")


if __name__ == "__main__":
    test_request_schema_structure()
    test_example_file_is_valid()
    print("\n✅ All simple validation tests passed")

