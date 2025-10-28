"""
CrewAI citation tools.

Provides citation management capabilities to CrewAI agents.
"""

from crewai.tools.base_tool import BaseTool
from typing import Any, Type, Optional, List
from pydantic import BaseModel, Field
import logging

from citation_tracking.core.citation_manager import CitationManager

logger = logging.getLogger(__name__)


class CitationInput(BaseModel):
    """Input schema for citation operations."""

    operation: str = Field(
        description="Operation: add, get, search, validate, format, list, export"
    )

    # For 'add' operation
    doi: Optional[str] = Field(None, description="DOI to add (will auto-extract metadata)")
    pmid: Optional[str] = Field(None, description="PubMed ID to add")
    url: Optional[str] = Field(None, description="URL to add")

    # For 'get' operation
    citation_id: Optional[str] = Field(None, description="Citation ID to retrieve")
    citation_number: Optional[int] = Field(None, description="Citation number to retrieve")

    # For 'format' operation
    citation_ids: Optional[List[str]] = Field(None, description="Citation IDs to format")
    format_type: Optional[str] = Field("intext", description="Format type: 'intext' or 'bibliography'")
    page_number: Optional[str] = Field(None, description="Page number for quote (only for intext)")

    # For 'export' operation
    export_format: Optional[str] = Field("bibtex", description="Export format: 'bibtex'")


class CitationManagerTool(BaseTool):
    """
    Comprehensive citation management tool for CrewAI agents.

    This tool provides zero-hallucination citation tracking by validating
    all DOIs and PMIDs against authoritative databases before acceptance.
    """

    name: str = "CitationManager"
    description: str = """
Comprehensive citation management tool for research.

CRITICAL: Use this tool for EVERY citation you add. Never manually create citations.

Operations:
- add: Add a citation from DOI, PMID, or URL (validates and extracts metadata automatically)
- get: Retrieve a citation by ID or number
- validate: Validate all citations in database
- format: Format citations for in-text or bibliography
- list: List all citations
- export: Export citations (bibtex)

Examples:

1. Add by DOI:
   {"operation": "add", "doi": "10.1038/s41586-023-06004-0"}
   Returns: Citation with complete metadata, citation number, validation status

2. Add by PMID:
   {"operation": "add", "pmid": "36854710"}
   Returns: Citation with complete PubMed metadata

3. Add by URL:
   {"operation": "add", "url": "https://arxiv.org/abs/2301.12345"}
   Returns: Basic citation (will need manual enhancement)

4. Format in-text:
   {"operation": "format", "citation_ids": ["smith2023"], "format_type": "intext"}
   Returns: (Smith, 2023) [1]

5. Format in-text with page:
   {"operation": "format", "citation_ids": ["smith2023"], "format_type": "intext", "page_number": "42"}
   Returns: (Smith, 2023, p. 42) [1]

6. Format bibliography:
   {"operation": "format", "format_type": "bibliography"}
   Returns: Complete formatted bibliography

7. Validate all:
   {"operation": "validate"}
   Returns: Validation report with issues

8. List citations:
   {"operation": "list"}
   Returns: Summary of all citations

9. Export BibTeX:
   {"operation": "export", "export_format": "bibtex"}
   Returns: BibTeX formatted citations

IMPORTANT:
- Always use DOI or PMID when available (ensures metadata accuracy)
- Tool validates citations before adding (prevents hallucinations)
- Duplicate detection prevents adding same source twice
- Every citation gets a unique number [1], [2], etc.
"""
    args_schema: Type[BaseModel] = CitationInput

    citation_manager: CitationManager = Field(description="CitationManager instance")

    def _run(self, operation: str, **kwargs: Any) -> str:
        """Execute citation operation."""

        try:
            if operation == "add":
                return self._add_citation(**kwargs)
            elif operation == "get":
                return self._get_citation(**kwargs)
            elif operation == "validate":
                return self._validate_citations(**kwargs)
            elif operation == "format":
                return self._format_citation(**kwargs)
            elif operation == "list":
                return self._list_citations(**kwargs)
            elif operation == "export":
                return self._export_citations(**kwargs)
            else:
                return f"Error: Unknown operation '{operation}'. Valid operations: add, get, validate, format, list, export"

        except Exception as e:
            logger.error(f"Error in CitationManagerTool: {str(e)}", exc_info=True)
            return f"Error: {str(e)}"

    def _add_citation(
        self,
        doi: Optional[str] = None,
        pmid: Optional[str] = None,
        url: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Add a citation with automatic metadata extraction and validation.

        Returns: Success message with citation details
        """
        try:
            # Determine source and add citation
            if doi:
                citation = self.citation_manager.add_from_doi(doi)
            elif pmid:
                citation = self.citation_manager.add_from_pmid(pmid)
            elif url:
                citation = self.citation_manager.add_from_url(url)
            else:
                return "Error: Must provide doi, pmid, or url"

            # Format response
            formatted = self.citation_manager.format_bibliography_entry(citation.id)

            response = f"""✓ Citation added successfully

Citation Details:
- ID: {citation.id}
- Number: [{citation.citation_number}]
- Validated: {'✓ Yes' if citation.validated else '✗ No'} ({citation.validation_method or 'N/A'})
- Completeness: {citation.get_completeness_score()*100:.0f}%

Formatted Reference:
[{citation.citation_number}] {formatted}

Use in text as: ({citation.get_first_author_family_name() or 'Unknown'}, {citation.get_year() or 'n.d.'}) [{citation.citation_number}]

Or use format operation:
{{"operation": "format", "citation_ids": ["{citation.id}"], "format_type": "intext"}}
"""
            return response

        except ValueError as e:
            return f"✗ Citation validation failed: {str(e)}\n\nThis likely means:\n- DOI/PMID doesn't exist\n- API is unavailable\n- Invalid format\n\nPlease verify the identifier and try again, or use a different source."

        except Exception as e:
            logger.error(f"Error adding citation: {str(e)}", exc_info=True)
            return f"✗ Error adding citation: {str(e)}"

    def _get_citation(
        self,
        citation_id: Optional[str] = None,
        citation_number: Optional[int] = None,
        **kwargs
    ) -> str:
        """Get citation by ID or number."""

        if citation_id:
            citation = self.citation_manager.get_citation(citation_id)
        elif citation_number:
            citation = self.citation_manager.get_citation_by_number(citation_number)
        else:
            return "Error: Must provide citation_id or citation_number"

        if not citation:
            return f"Citation not found: {citation_id or citation_number}"

        formatted = self.citation_manager.format_bibliography_entry(citation.id)

        return f"""Citation [{citation.citation_number}]: {citation.id}

{formatted}

Validation: {citation.validated} ({citation.validation_method or 'N/A'})
Completeness: {citation.get_completeness_score()*100:.0f}%
DOI: {citation.DOI or 'N/A'}
PMID: {citation.PMID or 'N/A'}
URL: {citation.URL or 'N/A'}
"""

    def _validate_citations(self, **kwargs) -> str:
        """Validate all citations."""

        report = self.citation_manager.validate_all()

        response = f"""Citation Validation Report
==========================

Summary:
- Total citations: {report['total_citations']}
- Validated: {report['validated']} ({report['validation_rate']*100:.1f}%)
- Failed validation: {report['failed']}
- Average completeness: {report['average_completeness']*100:.1f}%
- Duplicates found: {report['duplicates_found']}

"""

        if report['issues']:
            response += "Issues Found:\n"
            for issue in report['issues']:
                response += f"- [{issue['citation_id']}] {issue['type']}: {issue['message']}\n"
        else:
            response += "✓ No issues found. All citations validated successfully.\n"

        return response

    def _format_citation(
        self,
        citation_ids: Optional[List[str]] = None,
        format_type: str = "intext",
        page_number: Optional[str] = None,
        **kwargs
    ) -> str:
        """Format citations for in-text or bibliography."""

        if format_type == "intext":
            if not citation_ids:
                return "Error: citation_ids required for intext format"

            formatted = self.citation_manager.format_intext(citation_ids, page_number)
            return f"In-text citation:\n{formatted}"

        elif format_type == "bibliography":
            formatted = self.citation_manager.format_bibliography(citation_ids)
            return f"Bibliography:\n\n{formatted}"

        else:
            return f"Error: Unknown format_type '{format_type}'. Use 'intext' or 'bibliography'"

    def _list_citations(self, **kwargs) -> str:
        """List all citations."""

        citations = self.citation_manager.get_all_citations()

        if not citations:
            return "No citations in database yet."

        # Get quality metrics
        metrics = self.citation_manager.get_quality_metrics()

        response = f"""Citation Database Summary
========================

Total citations: {len(citations)}
Validated: {int(metrics['validation_rate'] * len(citations))} ({metrics['validation_rate']*100:.1f}%)
With DOI: {metrics['citations_with_doi']} ({metrics['citations_with_doi_pct']*100:.1f}%)
With PMID: {metrics['citations_with_pmid']} ({metrics['citations_with_pmid_pct']*100:.1f}%)
Average completeness: {metrics['average_completeness']*100:.1f}%

Citations:
"""

        for cit in sorted(citations, key=lambda c: c.citation_number or 0):
            author = cit.get_first_author_family_name() or "Unknown"
            year = cit.get_year() or "n.d."
            title = cit.title[:50] + "..." if cit.title and len(cit.title) > 50 else (cit.title or "No title")

            status = "✓" if cit.validated else "✗"

            response += f"\n[{cit.citation_number}] {status} {author} ({year}): {title}"

        return response

    def _export_citations(self, export_format: str = "bibtex", **kwargs) -> str:
        """Export citations."""

        if export_format == "bibtex":
            bibtex = self.citation_manager.export_bibtex()
            return f"BibTeX Export:\n\n{bibtex}"
        else:
            return f"Error: Unknown export_format '{export_format}'. Currently only 'bibtex' supported."
