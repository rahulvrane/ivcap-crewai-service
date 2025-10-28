"""
DOI validator using Crossref API.

Validates DOIs and extracts metadata from Crossref.
"""

import requests
import re
import time
import logging
from typing import Optional, Dict, Tuple
from citation_tracking.core.citation_model import CSLCitation, CSLName, CSLDate

logger = logging.getLogger(__name__)


class DOIValidator:
    """Validate DOIs via Crossref API and extract metadata."""

    CROSSREF_API = "https://api.crossref.org/works/"

    # Crossref recommends including email for polite pool (faster response)
    DEFAULT_EMAIL = "citation-tracker@ivcap.works"

    def __init__(self, email: Optional[str] = None, cache_ttl: int = 86400):
        """
        Initialize DOI validator.

        Args:
            email: Email for Crossref polite pool (gets faster response times)
            cache_ttl: Cache time-to-live in seconds (default 24 hours)
        """
        self.email = email or self.DEFAULT_EMAIL
        self.cache = {}
        self.cache_ttl = cache_ttl

    def validate_doi(self, doi: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate DOI and return metadata.

        Args:
            doi: DOI to validate (e.g., '10.1038/nature12345' or 'https://doi.org/10.1038/nature12345')

        Returns:
            Tuple of (is_valid, metadata_dict or None)
            metadata_dict contains CSL-JSON compatible fields
        """
        # Normalize DOI
        doi = self._normalize_doi(doi)

        if not doi:
            logger.warning("Invalid DOI format")
            return False, None

        # Check cache
        cache_key = f"doi:{doi}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < self.cache_ttl:
                logger.debug(f"DOI {doi} found in cache")
                return cached['valid'], cached['metadata']

        # Query Crossref API
        try:
            headers = {
                'User-Agent': f'CitationTracker/1.0 (mailto:{self.email})'
            }
            url = f"{self.CROSSREF_API}{doi}"

            logger.info(f"Validating DOI: {doi}")
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                metadata = self._extract_metadata(data['message'])

                # Cache successful result
                self.cache[cache_key] = {
                    'valid': True,
                    'metadata': metadata,
                    'timestamp': time.time()
                }

                logger.info(f"DOI {doi} validated successfully")
                return True, metadata

            elif response.status_code == 404:
                # DOI not found
                self.cache[cache_key] = {
                    'valid': False,
                    'metadata': None,
                    'timestamp': time.time()
                }
                logger.warning(f"DOI {doi} not found (404)")
                return False, None

            else:
                # API error, don't cache
                logger.error(f"Crossref API error for {doi}: {response.status_code}")
                return False, {"error": f"API returned {response.status_code}"}

        except requests.exceptions.Timeout:
            logger.error(f"Timeout validating DOI {doi}")
            return False, {"error": "Request timeout"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error validating DOI {doi}: {str(e)}")
            return False, {"error": str(e)}

    def _normalize_doi(self, doi: str) -> Optional[str]:
        """
        Normalize DOI for comparison.

        Args:
            doi: Raw DOI string

        Returns:
            Normalized DOI or None if invalid
        """
        if not doi:
            return None

        doi = doi.strip().lower()

        # Remove common prefixes
        if doi.startswith('http://doi.org/'):
            doi = doi.replace('http://doi.org/', '')
        elif doi.startswith('https://doi.org/'):
            doi = doi.replace('https://doi.org/', '')
        elif doi.startswith('doi:'):
            doi = doi.replace('doi:', '')

        # Validate DOI format (10.xxxx/...)
        doi_pattern = r'^10\.\d{4,}/[^\s]+$'
        if not re.match(doi_pattern, doi):
            logger.warning(f"DOI doesn't match expected pattern: {doi}")
            return None

        return doi

    def _extract_metadata(self, crossref_data: Dict) -> Dict:
        """
        Extract CSL-JSON compatible metadata from Crossref response.

        Args:
            crossref_data: Raw Crossref API response

        Returns:
            Dictionary with CSL-JSON compatible fields
        """
        metadata = {
            "DOI": crossref_data.get("DOI"),
            "type": self._map_type(crossref_data.get("type")),
            "title": crossref_data.get("title", [None])[0],
            "container_title": crossref_data.get("container-title", [None])[0],
            "volume": crossref_data.get("volume"),
            "issue": crossref_data.get("issue"),
            "page": crossref_data.get("page"),
            "publisher": crossref_data.get("publisher"),
            "ISSN": crossref_data.get("ISSN", [None])[0],
            "URL": crossref_data.get("URL"),
            "abstract": crossref_data.get("abstract"),
        }

        # Extract authors
        if "author" in crossref_data:
            metadata["author"] = []
            for author in crossref_data["author"]:
                author_data = {
                    "family": author.get("family"),
                    "given": author.get("given")
                }
                # Only add if we have at least a family name
                if author_data["family"]:
                    metadata["author"].append(author_data)

        # Extract editors
        if "editor" in crossref_data:
            metadata["editor"] = []
            for editor in crossref_data["editor"]:
                editor_data = {
                    "family": editor.get("family"),
                    "given": editor.get("given")
                }
                if editor_data["family"]:
                    metadata["editor"].append(editor_data)

        # Extract publication date
        date_fields = ["published", "published-print", "published-online", "created"]
        for field in date_fields:
            if field in crossref_data:
                date_parts = crossref_data[field].get("date-parts")
                if date_parts and len(date_parts) > 0:
                    metadata["issued"] = {"date_parts": date_parts}
                    break

        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}

        return metadata

    def _map_type(self, crossref_type: str) -> str:
        """
        Map Crossref type to CSL type.

        Args:
            crossref_type: Crossref item type

        Returns:
            CSL-JSON type
        """
        type_map = {
            "journal-article": "article-journal",
            "book-chapter": "chapter",
            "posted-content": "report",
            "proceedings-article": "paper-conference",
            "book": "book",
            "monograph": "book",
            "edited-book": "book",
            "reference-book": "book",
            "report": "report",
            "dataset": "dataset",
            "dissertation": "thesis",
        }
        return type_map.get(crossref_type, crossref_type)

    def create_citation_from_doi(self, doi: str, citation_id: Optional[str] = None) -> Optional[CSLCitation]:
        """
        Create a CSLCitation object from a DOI.

        Args:
            doi: DOI to validate and extract metadata from
            citation_id: Optional custom citation ID (auto-generated if None)

        Returns:
            CSLCitation object or None if DOI invalid
        """
        valid, metadata = self.validate_doi(doi)

        if not valid or not metadata:
            return None

        # Generate citation ID if not provided
        if citation_id is None:
            # Try to create ID from first author + year
            if "author" in metadata and len(metadata["author"]) > 0:
                family = metadata["author"][0].get("family", "unknown")
                if "issued" in metadata and "date_parts" in metadata["issued"]:
                    year = metadata["issued"]["date_parts"][0][0]
                    citation_id = f"{family.lower()}{year}"
                else:
                    citation_id = family.lower()
            else:
                # Fallback to DOI-based ID
                citation_id = self._normalize_doi(doi).replace("/", "_").replace(".", "_")

        # Convert author/editor dicts to CSLName objects
        if "author" in metadata:
            metadata["author"] = [CSLName(**a) for a in metadata["author"]]
        if "editor" in metadata:
            metadata["editor"] = [CSLName(**e) for e in metadata["editor"]]

        # Convert issued dict to CSLDate
        if "issued" in metadata:
            metadata["issued"] = CSLDate(**metadata["issued"])

        # Create citation
        citation = CSLCitation(
            id=citation_id,
            **metadata,
            validated=True,
            validation_method="DOI"
        )

        return citation

    def clear_cache(self):
        """Clear the validation cache."""
        self.cache.clear()
        logger.info("DOI validation cache cleared")
