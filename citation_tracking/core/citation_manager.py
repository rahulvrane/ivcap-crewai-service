"""
Citation Manager - Main interface for citation tracking system.

Coordinates validators, duplicate detection, and citation storage.
"""

import logging
from typing import Optional, List, Dict, Tuple
from citation_tracking.core.citation_model import CSLCitation, CitationDatabase
from citation_tracking.validation.doi_validator import DOIValidator
from citation_tracking.validation.pmid_validator import PMIDValidator
from citation_tracking.validation.duplicate_detector import DuplicateDetector

logger = logging.getLogger(__name__)


class CitationManager:
    """
    Main citation management class.

    Handles adding, validating, and managing citations for a research job.
    """

    def __init__(self, job_id: str, style: str = "apa", email: Optional[str] = None):
        """
        Initialize citation manager.

        Args:
            job_id: Unique job ID
            style: Citation style (apa, mla, chicago, vancouver, ieee)
            email: Email for Crossref polite pool
        """
        self.job_id = job_id
        self.style = style

        # Initialize database
        self.database = CitationDatabase(job_id=job_id, style=style)

        # Initialize validators
        self.doi_validator = DOIValidator(email=email)
        self.pmid_validator = PMIDValidator()
        self.duplicate_detector = DuplicateDetector()

        logger.info(f"CitationManager initialized for job {job_id} with style {style}")

    def add_from_doi(self, doi: str, citation_id: Optional[str] = None, added_by: Optional[str] = None) -> CSLCitation:
        """
        Add citation from DOI.

        Args:
            doi: DOI to add
            citation_id: Optional custom citation ID
            added_by: Agent/user who added this citation

        Returns:
            CSLCitation object

        Raises:
            ValueError: If DOI is invalid or not found
        """
        logger.info(f"Adding citation from DOI: {doi}")

        # Create citation from DOI
        citation = self.doi_validator.create_citation_from_doi(doi, citation_id)

        if not citation:
            raise ValueError(f"Invalid or not found DOI: {doi}")

        # Set metadata
        citation.added_by = added_by

        # Check for duplicates
        duplicates = self.duplicate_detector.find_duplicates(citation, self.database.get_all_citations())

        if duplicates:
            logger.warning(f"Duplicate citation found for DOI {doi}: {duplicates[0].id}")
            # Merge with existing
            existing = duplicates[0]
            self.duplicate_detector.merge_citations(existing, citation)
            return existing

        # Add to database
        citation = self.database.add_citation(citation)

        logger.info(f"Citation added successfully: {citation.id} (number: [{citation.citation_number}])")

        return citation

    def add_from_pmid(self, pmid: str, citation_id: Optional[str] = None, added_by: Optional[str] = None) -> CSLCitation:
        """
        Add citation from PMID.

        Args:
            pmid: PubMed ID to add
            citation_id: Optional custom citation ID
            added_by: Agent/user who added this citation

        Returns:
            CSLCitation object

        Raises:
            ValueError: If PMID is invalid or not found
        """
        logger.info(f"Adding citation from PMID: {pmid}")

        # Create citation from PMID
        citation = self.pmid_validator.create_citation_from_pmid(pmid, citation_id)

        if not citation:
            raise ValueError(f"Invalid or not found PMID: {pmid}")

        # Set metadata
        citation.added_by = added_by

        # Check for duplicates
        duplicates = self.duplicate_detector.find_duplicates(citation, self.database.get_all_citations())

        if duplicates:
            logger.warning(f"Duplicate citation found for PMID {pmid}: {duplicates[0].id}")
            existing = duplicates[0]
            self.duplicate_detector.merge_citations(existing, citation)
            return existing

        # Add to database
        citation = self.database.add_citation(citation)

        logger.info(f"Citation added successfully: {citation.id} (number: [{citation.citation_number}])")

        return citation

    def add_from_url(self, url: str, citation_id: Optional[str] = None, added_by: Optional[str] = None) -> CSLCitation:
        """
        Add citation from URL.

        Currently creates a basic webpage citation. Future: extract metadata from page.

        Args:
            url: URL to add
            citation_id: Optional custom citation ID
            added_by: Agent/user who added this citation

        Returns:
            CSLCitation object
        """
        logger.info(f"Adding citation from URL: {url}")

        # Generate ID if not provided
        if not citation_id:
            # Use domain + timestamp as fallback
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace('.', '_')
            citation_id = f"web_{domain}"

        # Create basic citation
        citation = CSLCitation(
            id=citation_id,
            type="webpage",
            URL=url,
            added_by=added_by,
            validated=False,  # URL citations are not auto-validated
            validation_method="URL"
        )

        # Check for duplicates
        duplicates = self.duplicate_detector.find_duplicates(citation, self.database.get_all_citations())

        if duplicates:
            logger.warning(f"Duplicate citation found for URL {url}: {duplicates[0].id}")
            return duplicates[0]

        # Add to database
        citation = self.database.add_citation(citation)

        logger.info(f"Citation added successfully: {citation.id} (number: [{citation.citation_number}])")

        return citation

    def get_citation(self, citation_id: str) -> Optional[CSLCitation]:
        """Get citation by ID."""
        return self.database.get_citation(citation_id)

    def get_citation_by_number(self, number: int) -> Optional[CSLCitation]:
        """Get citation by number."""
        return self.database.get_citation_by_number(number)

    def get_all_citations(self) -> List[CSLCitation]:
        """Get all citations."""
        return self.database.get_all_citations()

    def get_citations_count(self) -> int:
        """Get total number of citations."""
        return self.database.get_citations_count()

    def validate_all(self) -> Dict:
        """
        Validate all citations.

        Returns:
            Dictionary with validation results
        """
        logger.info("Validating all citations")

        citations = self.database.get_all_citations()
        validated = sum([1 for c in citations if c.validated])
        failed = len(citations) - validated

        # Calculate completeness
        avg_completeness = self.database.get_average_completeness()

        # Find duplicates
        all_duplicates = []
        for i, cit in enumerate(citations):
            dups = self.duplicate_detector.find_duplicates(cit, citations[i+1:])
            if dups:
                all_duplicates.append((cit, dups))

        report = {
            "total_citations": len(citations),
            "validated": validated,
            "failed": failed,
            "validation_rate": validated / len(citations) if citations else 0,
            "average_completeness": avg_completeness,
            "duplicates_found": len(all_duplicates),
            "issues": []
        }

        # Add issues for unvalidated citations
        for cit in citations:
            if not cit.validated:
                report["issues"].append({
                    "citation_id": cit.id,
                    "type": "not_validated",
                    "message": f"Citation {cit.id} not validated"
                })

        # Add issues for duplicates
        for original, dups in all_duplicates:
            report["issues"].append({
                "citation_id": original.id,
                "type": "duplicate",
                "message": f"Possible duplicates: {[d.id for d in dups]}"
            })

        logger.info(f"Validation complete: {validated}/{len(citations)} validated, {len(all_duplicates)} duplicates found")

        return report

    def format_intext(self, citation_ids: List[str], page_number: Optional[str] = None) -> str:
        """
        Format in-text citation(s).

        Args:
            citation_ids: List of citation IDs
            page_number: Optional page number for quote

        Returns:
            Formatted in-text citation string
        """
        citations = [self.get_citation(cid) for cid in citation_ids]
        citations = [c for c in citations if c is not None]

        if not citations:
            return "[Citation not found]"

        # Simple APA-style formatting for now
        # TODO: Implement full CSL processor for multiple styles

        if len(citations) == 1:
            cit = citations[0]
            author = cit.get_first_author_family_name() or "Unknown"
            year = cit.get_year() or "n.d."
            number = cit.citation_number or "?"

            if page_number:
                return f"({author}, {year}, p. {page_number}) [{number}]"
            else:
                return f"({author}, {year}) [{number}]"
        else:
            # Multiple citations
            parts = []
            for cit in citations:
                author = cit.get_first_author_family_name() or "Unknown"
                year = cit.get_year() or "n.d."
                number = cit.citation_number or "?"
                parts.append(f"{author}, {year} [{number}]")

            return f"({'; '.join(parts)})"

    def format_bibliography_entry(self, citation_id: str) -> str:
        """
        Format bibliography entry for a citation.

        Args:
            citation_id: Citation ID

        Returns:
            Formatted bibliography entry
        """
        cit = self.get_citation(citation_id)
        if not cit:
            return "[Citation not found]"

        # Simple APA-style formatting for now
        # TODO: Implement full CSL processor

        parts = []

        # Authors
        if cit.author:
            if len(cit.author) == 1:
                author_str = f"{cit.author[0].family}, {cit.author[0].given or ''}"
            elif len(cit.author) == 2:
                author_str = f"{cit.author[0].family}, {cit.author[0].given or ''} & {cit.author[1].family}, {cit.author[1].given or ''}"
            else:
                author_str = f"{cit.author[0].family}, {cit.author[0].given or ''} et al."
            parts.append(author_str.strip())

        # Year
        if cit.issued:
            year = cit.issued.get_year()
            if year:
                parts.append(f"({year}).")

        # Title
        if cit.title:
            parts.append(f"{cit.title}.")

        # Journal/Publisher
        if cit.container_title:
            journal = cit.container_title
            if cit.volume:
                journal += f", {cit.volume}"
            if cit.issue:
                journal += f"({cit.issue})"
            if cit.page:
                journal += f", {cit.page}"
            parts.append(f"{journal}.")

        # DOI or URL
        if cit.DOI:
            parts.append(f"https://doi.org/{cit.DOI}")
        elif cit.URL:
            parts.append(str(cit.URL))

        return " ".join(parts)

    def format_bibliography(self, citation_ids: Optional[List[str]] = None) -> str:
        """
        Format complete bibliography.

        Args:
            citation_ids: Optional list of citation IDs (all if None)

        Returns:
            Formatted bibliography string
        """
        if citation_ids:
            citations = [self.get_citation(cid) for cid in citation_ids]
            citations = [c for c in citations if c is not None]
        else:
            citations = self.get_all_citations()

        # Sort by citation number
        citations = sorted(citations, key=lambda c: c.citation_number or 0)

        lines = []
        for cit in citations:
            entry = self.format_bibliography_entry(cit.id)
            lines.append(f"[{cit.citation_number}] {entry}")

        return "\n".join(lines)

    def export_bibtex(self) -> str:
        """
        Export citations as BibTeX.

        Returns:
            BibTeX formatted string
        """
        citations = self.get_all_citations()

        entries = []
        for cit in citations:
            # Determine entry type
            entry_type = "article" if cit.type == "article-journal" else "misc"

            # Build BibTeX entry
            lines = [f"@{entry_type}{{{cit.id},"]

            if cit.author:
                authors = " and ".join([f"{a.family}, {a.given or ''}" for a in cit.author])
                lines.append(f"  author = {{{authors}}},")

            if cit.title:
                lines.append(f"  title = {{{cit.title}}},")

            if cit.container_title:
                lines.append(f"  journal = {{{cit.container_title}}},")

            if cit.issued:
                year = cit.issued.get_year()
                if year:
                    lines.append(f"  year = {{{year}}},")

            if cit.volume:
                lines.append(f"  volume = {{{cit.volume}}},")

            if cit.issue:
                lines.append(f"  number = {{{cit.issue}}},")

            if cit.page:
                lines.append(f"  pages = {{{cit.page}}},")

            if cit.DOI:
                lines.append(f"  doi = {{{cit.DOI}}},")

            if cit.URL:
                lines.append(f"  url = {{{cit.URL}}},")

            lines.append("}")
            entries.append("\n".join(lines))

        return "\n\n".join(entries)

    def get_quality_metrics(self) -> Dict:
        """
        Calculate quality metrics for citations.

        Returns:
            Dictionary with quality metrics
        """
        citations = self.get_all_citations()

        if not citations:
            return {
                "total_citations": 0,
                "validation_rate": 0,
                "average_completeness": 0,
                "citations_with_doi": 0,
                "citations_with_pmid": 0,
            }

        validated = sum([1 for c in citations if c.validated])
        with_doi = sum([1 for c in citations if c.DOI])
        with_pmid = sum([1 for c in citations if c.PMID])
        avg_completeness = self.database.get_average_completeness()

        return {
            "total_citations": len(citations),
            "validation_rate": validated / len(citations),
            "average_completeness": avg_completeness,
            "citations_with_doi": with_doi,
            "citations_with_doi_pct": with_doi / len(citations),
            "citations_with_pmid": with_pmid,
            "citations_with_pmid_pct": with_pmid / len(citations),
        }
