"""
Duplicate citation detector using multiple strategies.

Detects duplicate citations using exact matching (DOI/PMID) and fuzzy matching (title/author).
"""

import re
import logging
from difflib import SequenceMatcher
from typing import List
from citation_tracking.core.citation_model import CSLCitation

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Detect duplicate citations using multiple strategies."""

    def __init__(self, title_threshold: float = 0.85, author_threshold: float = 0.90):
        """
        Initialize duplicate detector.

        Args:
            title_threshold: Similarity threshold for title matching (0-1)
            author_threshold: Similarity threshold for author matching (0-1)
        """
        self.title_threshold = title_threshold
        self.author_threshold = author_threshold

    def find_duplicates(
        self,
        citation: CSLCitation,
        existing_citations: List[CSLCitation]
    ) -> List[CSLCitation]:
        """
        Find potential duplicate citations.

        Args:
            citation: Citation to check for duplicates
            existing_citations: List of existing citations to compare against

        Returns:
            List of potential duplicate citations
        """
        duplicates = []

        for existing in existing_citations:
            # Don't compare citation to itself
            if existing.id == citation.id:
                continue

            duplicate_score = self._calculate_duplicate_score(citation, existing)

            if duplicate_score > 0:
                logger.info(f"Potential duplicate found: {citation.id} <-> {existing.id} (score: {duplicate_score})")
                duplicates.append(existing)

        return duplicates

    def _calculate_duplicate_score(self, cit1: CSLCitation, cit2: CSLCitation) -> float:
        """
        Calculate duplicate score between two citations.

        Args:
            cit1: First citation
            cit2: Second citation

        Returns:
            Score indicating likelihood of duplicate (0 = not duplicate, 1 = exact duplicate)
        """
        # Strategy 1: Exact DOI match (100% duplicate)
        if cit1.DOI and cit2.DOI:
            if self._normalize_doi(cit1.DOI) == self._normalize_doi(cit2.DOI):
                logger.debug(f"Exact DOI match: {cit1.DOI}")
                return 1.0

        # Strategy 2: Exact PMID match (100% duplicate)
        if cit1.PMID and cit2.PMID:
            if cit1.PMID == cit2.PMID:
                logger.debug(f"Exact PMID match: {cit1.PMID}")
                return 1.0

        # Strategy 3: URL normalization match
        if cit1.URL and cit2.URL:
            if self._normalize_url(str(cit1.URL)) == self._normalize_url(str(cit2.URL)):
                logger.debug(f"Exact URL match: {cit1.URL}")
                return 1.0

        # Strategy 4: Fuzzy title + author + year match
        title_sim = self._title_similarity(cit1.title, cit2.title)
        author_sim = self._author_similarity(cit1.author, cit2.author)
        year_match = self._year_match(cit1, cit2)

        # Require all three to match for fuzzy duplicate
        if (title_sim > self.title_threshold and
            author_sim > self.author_threshold and
            year_match):
            score = (title_sim + author_sim) / 2
            logger.debug(f"Fuzzy match: title={title_sim:.2f}, author={author_sim:.2f}, year=True")
            return score

        return 0.0

    def _normalize_doi(self, doi: str) -> str:
        """Normalize DOI for comparison."""
        doi = doi.lower().strip()
        # Remove common prefixes
        prefixes = ['http://doi.org/', 'https://doi.org/', 'doi:']
        for prefix in prefixes:
            if doi.startswith(prefix):
                doi = doi[len(prefix):]
        # Remove any remaining special characters except . and /
        doi = re.sub(r'[^a-z0-9./]', '', doi)
        return doi

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        url = url.lower().strip()
        # Remove protocol
        url = re.sub(r'^https?://(www\.)?', '', url)
        # Remove trailing slash
        url = re.sub(r'/$', '', url)
        return url

    def _title_similarity(self, title1: Optional[str], title2: Optional[str]) -> float:
        """
        Calculate title similarity (0-1).

        Args:
            title1: First title
            title2: Second title

        Returns:
            Similarity score (0-1)
        """
        if not title1 or not title2:
            return 0.0

        # Normalize titles
        t1 = self._normalize_title(title1)
        t2 = self._normalize_title(title2)

        # Calculate similarity using SequenceMatcher
        return SequenceMatcher(None, t1, t2).ratio()

    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        title = title.lower()
        # Remove punctuation
        title = re.sub(r'[^\w\s]', '', title)
        # Normalize whitespace
        title = re.sub(r'\s+', ' ', title)
        return title.strip()

    def _author_similarity(self, authors1: Optional[List], authors2: Optional[List]) -> float:
        """
        Calculate author list similarity (0-1).

        Focuses on first author as this is most important for identification.

        Args:
            authors1: First author list
            authors2: Second author list

        Returns:
            Similarity score (0-1)
        """
        if not authors1 or not authors2:
            return 0.0

        if len(authors1) == 0 or len(authors2) == 0:
            return 0.0

        # Compare first authors (most important)
        first1 = self._format_author(authors1[0])
        first2 = self._format_author(authors2[0])

        similarity = SequenceMatcher(None, first1, first2).ratio()

        # If first authors match well, check if we have multiple authors
        if similarity > 0.8 and len(authors1) > 1 and len(authors2) > 1:
            # Also compare second author
            second1 = self._format_author(authors1[1])
            second2 = self._format_author(authors2[1])
            second_sim = SequenceMatcher(None, second1, second2).ratio()
            # Average first and second author similarity
            similarity = (similarity + second_sim) / 2

        return similarity

    def _format_author(self, author) -> str:
        """
        Format author for comparison.

        Args:
            author: CSLName object or dict

        Returns:
            Formatted author string (lowercase, normalized)
        """
        if hasattr(author, 'family'):
            # CSLName object
            family = (author.family or "").lower()
            given = (author.given or "").lower()
        else:
            # Dict
            family = (author.get("family") or "").lower()
            given = (author.get("given") or "").lower()

        # Normalize
        family = re.sub(r'[^\w\s]', '', family)
        given = re.sub(r'[^\w\s]', '', given)

        return f"{family} {given}".strip()

    def _year_match(self, cit1: CSLCitation, cit2: CSLCitation) -> bool:
        """
        Check if publication years match.

        Args:
            cit1: First citation
            cit2: Second citation

        Returns:
            True if years match, False otherwise
        """
        year1 = cit1.get_year()
        year2 = cit2.get_year()

        if year1 and year2:
            return year1 == year2

        return False

    def merge_citations(self, original: CSLCitation, duplicate: CSLCitation) -> CSLCitation:
        """
        Merge two duplicate citations, keeping most complete information.

        Args:
            original: Original citation to keep
            duplicate: Duplicate citation to merge from

        Returns:
            Merged citation (modifies original in place)
        """
        logger.info(f"Merging citation {duplicate.id} into {original.id}")

        # Merge fields - prefer non-None values
        fields_to_merge = [
            'title', 'container_title', 'publisher', 'volume', 'issue', 'page',
            'DOI', 'PMID', 'PMCID', 'ISBN', 'ISSN', 'URL', 'abstract', 'keyword'
        ]

        for field in fields_to_merge:
            orig_value = getattr(original, field, None)
            dup_value = getattr(duplicate, field, None)

            # If original doesn't have value but duplicate does, use duplicate's
            if not orig_value and dup_value:
                setattr(original, field, dup_value)
                logger.debug(f"  Merged field '{field}': {dup_value}")

        # Merge authors - prefer longer list
        if duplicate.author and (not original.author or len(duplicate.author) > len(original.author)):
            original.author = duplicate.author
            logger.debug(f"  Merged authors: {len(duplicate.author)} authors")

        # Merge dates - prefer more specific date
        if duplicate.issued and original.issued:
            dup_parts = duplicate.issued.date_parts[0] if duplicate.issued.date_parts else []
            orig_parts = original.issued.date_parts[0] if original.issued.date_parts else []
            if len(dup_parts) > len(orig_parts):
                original.issued = duplicate.issued
                logger.debug(f"  Merged more specific date")
        elif duplicate.issued and not original.issued:
            original.issued = duplicate.issued
            logger.debug(f"  Merged issued date")

        # Update validation status
        if duplicate.validated and not original.validated:
            original.validated = True
            original.validation_method = duplicate.validation_method

        # Merge quality scores - use higher scores
        if duplicate.credibility_score and (not original.credibility_score or duplicate.credibility_score > original.credibility_score):
            original.credibility_score = duplicate.credibility_score

        if duplicate.impact_factor and (not original.impact_factor or duplicate.impact_factor > original.impact_factor):
            original.impact_factor = duplicate.impact_factor

        if duplicate.citation_count and (not original.citation_count or duplicate.citation_count > original.citation_count):
            original.citation_count = duplicate.citation_count

        # Add citation counts together
        if duplicate.in_text_count:
            original.in_text_count = (original.in_text_count or 0) + duplicate.in_text_count

        return original
