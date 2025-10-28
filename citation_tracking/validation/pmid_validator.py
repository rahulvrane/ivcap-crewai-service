"""
PMID validator using PubMed E-utilities API.

Validates PubMed IDs and extracts metadata from PubMed.
"""

import requests
import time
import logging
from typing import Optional, Dict, Tuple
from xml.etree import ElementTree as ET
from citation_tracking.core.citation_model import CSLCitation, CSLName, CSLDate

logger = logging.getLogger(__name__)


class PMIDValidator:
    """Validate PMIDs via PubMed E-utilities API and extract metadata."""

    PUBMED_FETCH_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    PUBMED_SUMMARY_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    def __init__(self, api_key: Optional[str] = None, cache_ttl: int = 86400):
        """
        Initialize PMID validator.

        Args:
            api_key: Optional PubMed API key (increases rate limit)
            cache_ttl: Cache time-to-live in seconds (default 24 hours)
        """
        self.api_key = api_key
        self.cache = {}
        self.cache_ttl = cache_ttl

    def validate_pmid(self, pmid: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate PMID and return metadata.

        Args:
            pmid: PubMed ID to validate (numeric string)

        Returns:
            Tuple of (is_valid, metadata_dict or None)
        """
        # Normalize PMID
        pmid = self._normalize_pmid(pmid)

        if not pmid:
            logger.warning("Invalid PMID format")
            return False, None

        # Check cache
        cache_key = f"pmid:{pmid}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < self.cache_ttl:
                logger.debug(f"PMID {pmid} found in cache")
                return cached['valid'], cached['metadata']

        # Query PubMed API
        try:
            params = {
                'db': 'pubmed',
                'id': pmid,
                'retmode': 'xml',
                'rettype': 'abstract'
            }

            if self.api_key:
                params['api_key'] = self.api_key

            logger.info(f"Validating PMID: {pmid}")
            response = requests.get(self.PUBMED_FETCH_API, params=params, timeout=10)

            if response.status_code == 200:
                # Parse XML response
                try:
                    root = ET.fromstring(response.content)

                    # Check if article found
                    article = root.find('.//PubmedArticle')
                    if article is None:
                        logger.warning(f"PMID {pmid} not found")
                        self.cache[cache_key] = {
                            'valid': False,
                            'metadata': None,
                            'timestamp': time.time()
                        }
                        return False, None

                    # Extract metadata
                    metadata = self._extract_metadata(article, pmid)

                    # Cache successful result
                    self.cache[cache_key] = {
                        'valid': True,
                        'metadata': metadata,
                        'timestamp': time.time()
                    }

                    logger.info(f"PMID {pmid} validated successfully")
                    return True, metadata

                except ET.ParseError as e:
                    logger.error(f"Error parsing PubMed XML for {pmid}: {str(e)}")
                    return False, {"error": "XML parsing error"}

            else:
                logger.error(f"PubMed API error for {pmid}: {response.status_code}")
                return False, {"error": f"API returned {response.status_code}"}

        except requests.exceptions.Timeout:
            logger.error(f"Timeout validating PMID {pmid}")
            return False, {"error": "Request timeout"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error validating PMID {pmid}: {str(e)}")
            return False, {"error": str(e)}

    def _normalize_pmid(self, pmid: str) -> Optional[str]:
        """
        Normalize PMID (should be numeric).

        Args:
            pmid: Raw PMID string

        Returns:
            Normalized PMID or None if invalid
        """
        if not pmid:
            return None

        pmid = pmid.strip()

        # Remove PMID: prefix if present
        if pmid.upper().startswith('PMID:'):
            pmid = pmid[5:].strip()

        # Should be purely numeric
        if not pmid.isdigit():
            logger.warning(f"PMID is not numeric: {pmid}")
            return None

        return pmid

    def _extract_metadata(self, article_elem: ET.Element, pmid: str) -> Dict:
        """
        Extract CSL-JSON compatible metadata from PubMed XML.

        Args:
            article_elem: PubmedArticle XML element
            pmid: PubMed ID

        Returns:
            Dictionary with CSL-JSON compatible fields
        """
        metadata = {
            "PMID": pmid,
            "type": "article-journal",  # PubMed articles are journals
        }

        # Extract article info
        article = article_elem.find('.//Article')
        if article is None:
            return metadata

        # Title
        title_elem = article.find('.//ArticleTitle')
        if title_elem is not None and title_elem.text:
            metadata["title"] = title_elem.text

        # Abstract
        abstract_elem = article.find('.//Abstract/AbstractText')
        if abstract_elem is not None and abstract_elem.text:
            metadata["abstract"] = abstract_elem.text

        # Journal
        journal = article.find('.//Journal')
        if journal is not None:
            journal_title = journal.find('.//Title')
            if journal_title is not None and journal_title.text:
                metadata["container_title"] = journal_title.text

            # ISSN
            issn = journal.find('.//ISSN')
            if issn is not None and issn.text:
                metadata["ISSN"] = issn.text

            # Volume/Issue
            issue = journal.find('.//JournalIssue')
            if issue is not None:
                volume = issue.find('.//Volume')
                if volume is not None and volume.text:
                    metadata["volume"] = volume.text

                issue_num = issue.find('.//Issue')
                if issue_num is not None and issue_num.text:
                    metadata["issue"] = issue_num.text

                # Publication date
                pub_date = issue.find('.//PubDate')
                if pub_date is not None:
                    year = pub_date.find('.//Year')
                    month = pub_date.find('.//Month')
                    day = pub_date.find('.//Day')

                    date_parts = []
                    if year is not None and year.text:
                        date_parts.append(int(year.text))
                    if month is not None and month.text:
                        # Convert month name to number if needed
                        month_val = self._parse_month(month.text)
                        if month_val:
                            date_parts.append(month_val)
                    if day is not None and day.text:
                        date_parts.append(int(day.text))

                    if date_parts:
                        metadata["issued"] = {"date_parts": [date_parts]}

        # Pagination
        pagination = article.find('.//Pagination/MedlinePgn')
        if pagination is not None and pagination.text:
            metadata["page"] = pagination.text

        # Authors
        author_list = article.find('.//AuthorList')
        if author_list is not None:
            authors = []
            for author_elem in author_list.findall('.//Author'):
                last_name = author_elem.find('.//LastName')
                fore_name = author_elem.find('.//ForeName')

                if last_name is not None and last_name.text:
                    author_data = {
                        "family": last_name.text,
                        "given": fore_name.text if fore_name is not None else None
                    }
                    authors.append(author_data)

            if authors:
                metadata["author"] = authors

        # DOI
        article_id_list = article_elem.find('.//ArticleIdList')
        if article_id_list is not None:
            for article_id in article_id_list.findall('.//ArticleId'):
                if article_id.get('IdType') == 'doi' and article_id.text:
                    metadata["DOI"] = article_id.text
                elif article_id.get('IdType') == 'pmc' and article_id.text:
                    metadata["PMCID"] = article_id.text

        # URL
        metadata["URL"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        return metadata

    def _parse_month(self, month_str: str) -> Optional[int]:
        """Convert month name/abbreviation to number."""
        month_map = {
            "jan": 1, "january": 1,
            "feb": 2, "february": 2,
            "mar": 3, "march": 3,
            "apr": 4, "april": 4,
            "may": 5,
            "jun": 6, "june": 6,
            "jul": 7, "july": 7,
            "aug": 8, "august": 8,
            "sep": 9, "september": 9,
            "oct": 10, "october": 10,
            "nov": 11, "november": 11,
            "dec": 12, "december": 12,
        }

        month_lower = month_str.lower().strip()

        # Try direct numeric
        if month_lower.isdigit():
            return int(month_lower)

        # Try name lookup
        return month_map.get(month_lower)

    def create_citation_from_pmid(self, pmid: str, citation_id: Optional[str] = None) -> Optional[CSLCitation]:
        """
        Create a CSLCitation object from a PMID.

        Args:
            pmid: PMID to validate and extract metadata from
            citation_id: Optional custom citation ID (auto-generated if None)

        Returns:
            CSLCitation object or None if PMID invalid
        """
        valid, metadata = self.validate_pmid(pmid)

        if not valid or not metadata:
            return None

        # Generate citation ID if not provided
        if citation_id is None:
            if "author" in metadata and len(metadata["author"]) > 0:
                family = metadata["author"][0].get("family", "unknown")
                if "issued" in metadata and "date_parts" in metadata["issued"]:
                    year = metadata["issued"]["date_parts"][0][0]
                    citation_id = f"{family.lower()}{year}"
                else:
                    citation_id = family.lower()
            else:
                citation_id = f"pmid{pmid}"

        # Convert author dicts to CSLName objects
        if "author" in metadata:
            metadata["author"] = [CSLName(**a) for a in metadata["author"]]

        # Convert issued dict to CSLDate
        if "issued" in metadata:
            metadata["issued"] = CSLDate(**metadata["issued"])

        # Create citation
        citation = CSLCitation(
            id=citation_id,
            **metadata,
            validated=True,
            validation_method="PMID"
        )

        return citation

    def clear_cache(self):
        """Clear the validation cache."""
        self.cache.clear()
        logger.info("PMID validation cache cleared")
