"""
Knowledge Processor for CrewAI Service
Converts additional inputs (previous crew outputs) into CrewAI Knowledge Sources.

Created: 2025-01-13
Purpose: Enable crews to semantically search previous crew outputs via knowledge_sources
"""

from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from typing import List, Union, Optional
import logging

# Use standard logging (will be configured by service.py or test harness)
logger = logging.getLogger("app.knowledge_processor")


def create_knowledge_sources_from_inputs(
    inputs: Union[str, List[str]]
) -> List[StringKnowledgeSource]:
    """
    Convert markdown strings into CrewAI Knowledge sources.
    
    This function takes previous crew outputs (as markdown strings) and creates
    StringKnowledgeSource instances that can be passed to a Crew's knowledge_sources
    parameter. All agents in the crew will automatically have semantic search access
    to these sources via RAG (Retrieval-Augmented Generation).
    
    Args:
        inputs: Single markdown string or list of markdown strings from previous
                crew runs. Each string typically contains research findings, analysis
                results, or other structured output from earlier crews.
    
    Returns:
        List of StringKnowledgeSource instances (one per input string). Empty list
        if inputs is None or empty.
    
    Example:
        >>> previous_research = "# Research Results\\n\\nKey finding: X impacts Y..."
        >>> sources = create_knowledge_sources_from_inputs(previous_research)
        >>> crew = Crew(agents=[...], tasks=[...], knowledge_sources=sources)
        
        >>> multiple_inputs = [
        ...     "# Deep Research Output\\n\\nComprehensive findings...",
        ...     "# Expert Profiles\\n\\nKey experts identified..."
        ... ]
        >>> sources = create_knowledge_sources_from_inputs(multiple_inputs)
    
    Notes:
        - Each source will be chunked, embedded, and stored in ChromaDB automatically
        - The crew's embedder configuration will be used for embeddings
        - Sources are isolated per crew run (no cross-contamination)
        - Metadata is added to each source for tracking and debugging
    """
    if not inputs:
        logger.debug("No additional inputs provided, returning empty list")
        return []
    
    # Normalize to list
    input_list = [inputs] if isinstance(inputs, str) else inputs
    logger.info(f"Processing {len(input_list)} additional input(s) into knowledge sources")
    
    sources = []
    for idx, content in enumerate(input_list, 1):
        if content and content.strip():
            try:
                source = StringKnowledgeSource(
                    content=content,
                    metadata={
                        "source_type": "previous_crew_output",
                        "input_index": idx,
                        "source_name": f"reference_input_{idx}",
                        "content_length": len(content)
                    }
                )
                sources.append(source)
                logger.info(
                    f"✓ Created knowledge source {idx}: "
                    f"{len(content)} chars, "
                    f"{len(content.split())} words"
                )
            except Exception as e:
                logger.error(f"Failed to create knowledge source {idx}: {e}", exc_info=True)
                # Continue processing other inputs even if one fails
        else:
            logger.warning(f"Skipping empty input at index {idx}")
    
    logger.info(f"Successfully created {len(sources)}/{len(input_list)} knowledge source(s)")
    return sources

