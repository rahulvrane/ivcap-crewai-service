"""
Unit Tests for Knowledge Processor
Tests the conversion of additional inputs into CrewAI Knowledge Sources.

Created: 2025-01-13
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path to import knowledge_processor
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_processor import create_knowledge_sources_from_inputs
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource


class TestCreateKnowledgeSources:
    """Test suite for create_knowledge_sources_from_inputs function."""
    
    def test_single_string_input(self):
        """Test creating a knowledge source from a single string."""
        content = "# Research Results\n\nKey finding: X impacts Y through mechanism Z."
        sources = create_knowledge_sources_from_inputs(content)
        
        assert len(sources) == 1
        assert isinstance(sources[0], StringKnowledgeSource)
        assert sources[0].content == content
        assert sources[0].metadata["input_index"] == 1
        assert sources[0].metadata["source_type"] == "previous_crew_output"
        assert sources[0].metadata["content_length"] == len(content)
    
    def test_multiple_string_inputs(self):
        """Test creating knowledge sources from a list of strings."""
        inputs = [
            "# First Document\n\nContent of first document.",
            "# Second Document\n\nContent of second document."
        ]
        sources = create_knowledge_sources_from_inputs(inputs)
        
        assert len(sources) == 2
        assert isinstance(sources[0], StringKnowledgeSource)
        assert isinstance(sources[1], StringKnowledgeSource)
        assert sources[0].content == inputs[0]
        assert sources[1].content == inputs[1]
        assert sources[0].metadata["input_index"] == 1
        assert sources[1].metadata["input_index"] == 2
    
    def test_empty_input_none(self):
        """Test handling None input."""
        sources = create_knowledge_sources_from_inputs(None)
        assert sources == []
    
    def test_empty_input_empty_list(self):
        """Test handling empty list input."""
        sources = create_knowledge_sources_from_inputs([])
        assert sources == []
    
    def test_empty_string_input(self):
        """Test handling empty string input."""
        sources = create_knowledge_sources_from_inputs("")
        assert sources == []
    
    def test_whitespace_only_input(self):
        """Test handling whitespace-only input."""
        sources = create_knowledge_sources_from_inputs("   \n\t  ")
        assert sources == []
    
    def test_mixed_valid_and_empty_inputs(self):
        """Test handling list with mix of valid and empty strings."""
        inputs = [
            "# Valid Document\n\nContent here.",
            "",
            "# Another Valid Document\n\nMore content.",
            "   ",
            None  # Should handle gracefully
        ]
        # Filter out None first as the function expects str or list[str]
        inputs_clean = [i for i in inputs if i is not None]
        sources = create_knowledge_sources_from_inputs(inputs_clean)
        
        # Should only create sources for non-empty strings
        assert len(sources) == 2
        assert sources[0].metadata["input_index"] == 1
        assert sources[1].metadata["input_index"] == 3  # Skipped index 2
    
    def test_large_input(self):
        """Test handling large markdown input (simulating real crew output)."""
        # Create a realistic 2000-word research output
        large_content = "# Comprehensive Research Report\n\n"
        large_content += "## Executive Summary\n\n"
        large_content += "This is a comprehensive analysis. " * 100
        large_content += "\n\n## Detailed Findings\n\n"
        large_content += "Finding 1: Important discovery. " * 100
        large_content += "\n\n## Conclusions\n\n"
        large_content += "Concluding remarks here. " * 50
        
        sources = create_knowledge_sources_from_inputs(large_content)
        
        assert len(sources) == 1
        assert len(sources[0].content) > 1000  # Verify it's actually large
        assert sources[0].metadata["content_length"] == len(large_content)
    
    def test_special_characters_and_formatting(self):
        """Test handling markdown with special characters and formatting."""
        content = """# Report with Special Characters

## Section 1
- Bullet point with *italic* and **bold**
- Code snippet: `print("hello")`

## Section 2
| Table | Header |
|-------|--------|
| Data  | Value  |

> Blockquote text

[Link](https://example.com)
"""
        sources = create_knowledge_sources_from_inputs(content)
        
        assert len(sources) == 1
        assert sources[0].content == content
        # Verify special characters preserved
        assert "*italic*" in sources[0].content
        assert "**bold**" in sources[0].content
        assert "`print" in sources[0].content
        assert "|" in sources[0].content
    
    def test_metadata_tracking(self):
        """Test that metadata is properly set for all sources."""
        inputs = [
            "Short content.",
            "Much longer content with more words and characters here.",
            "Medium length content."
        ]
        sources = create_knowledge_sources_from_inputs(inputs)
        
        for idx, source in enumerate(sources, 1):
            assert source.metadata["input_index"] == idx
            assert source.metadata["source_type"] == "previous_crew_output"
            assert source.metadata["source_name"] == f"reference_input_{idx}"
            assert source.metadata["content_length"] == len(inputs[idx-1])
    
    def test_list_with_single_element(self):
        """Test that single-element list is handled same as string."""
        content = "# Single Document\n\nContent here."
        
        # Test with string
        sources_string = create_knowledge_sources_from_inputs(content)
        
        # Test with list
        sources_list = create_knowledge_sources_from_inputs([content])
        
        # Should produce equivalent results
        assert len(sources_string) == len(sources_list) == 1
        assert sources_string[0].content == sources_list[0].content
        assert sources_string[0].metadata["input_index"] == 1
        assert sources_list[0].metadata["input_index"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

