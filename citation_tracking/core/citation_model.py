"""
Citation data models using CSL-JSON format.

CSL-JSON (Citation Style Language JSON) is the canonical format for bibliographic data.
Full specification: https://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime


class CSLName(BaseModel):
    """CSL name object for authors, editors, translators."""

    family: str = Field(description="Family name (surname)")
    given: Optional[str] = Field(None, description="Given name(s)")
    dropping_particle: Optional[str] = Field(None, description="e.g., 'de', 'von'")
    non_dropping_particle: Optional[str] = Field(None, description="e.g., 'de la'")
    suffix: Optional[str] = Field(None, description="e.g., 'Jr.', 'III'")
    literal: Optional[str] = Field(None, description="Literal name (for organizations)")

    @validator('family')
    def family_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Family name cannot be empty")
        return v.strip()

    def __str__(self) -> str:
        """Format name as 'Family, Given'"""
        if self.literal:
            return self.literal
        name_parts = []
        if self.family:
            name_parts.append(self.family)
        if self.given:
            name_parts.append(self.given)
        return ", ".join(name_parts) if len(name_parts) > 1 else name_parts[0]


class CSLDate(BaseModel):
    """CSL date object."""

    date_parts: List[List[int]] = Field(
        description="[[year], [year, month], or [year, month, day]]"
    )
    season: Optional[str] = Field(None, description="Season (1-4) or name")
    circa: Optional[bool] = Field(None, description="Approximate date")
    literal: Optional[str] = Field(None, description="Date in free text")
    raw: Optional[str] = Field(None, description="Raw date string")

    def get_year(self) -> Optional[int]:
        """Extract year from date_parts."""
        if self.date_parts and len(self.date_parts) > 0 and len(self.date_parts[0]) > 0:
            return self.date_parts[0][0]
        return None

    def __str__(self) -> str:
        """Format date as string."""
        if self.literal:
            return self.literal
        if self.date_parts and len(self.date_parts) > 0:
            parts = self.date_parts[0]
            if len(parts) == 1:
                return str(parts[0])
            elif len(parts) == 2:
                return f"{parts[0]}-{parts[1]:02d}"
            elif len(parts) == 3:
                return f"{parts[0]}-{parts[1]:02d}-{parts[2]:02d}"
        return ""


class CSLCitation(BaseModel):
    """
    CSL-JSON citation object.

    This is the canonical format for storing bibliographic data.
    Full spec: https://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html
    """

    # REQUIRED FIELDS
    id: str = Field(description="Unique citation identifier (e.g., 'smith2023ml')")
    type: Literal[
        "article", "article-journal", "article-magazine", "article-newspaper",
        "bill", "book", "broadcast", "chapter", "classic", "collection",
        "dataset", "document", "entry", "entry-dictionary", "entry-encyclopedia",
        "event", "figure", "graphic", "hearing", "interview", "legal_case",
        "legislation", "manuscript", "map", "motion_picture", "musical_score",
        "pamphlet", "paper-conference", "patent", "performance", "periodical",
        "personal_communication", "post", "post-weblog", "regulation", "report",
        "review", "review-book", "software", "song", "speech", "standard",
        "thesis", "treaty", "webpage"
    ] = Field(description="Type of item")

    # CREATOR FIELDS
    author: Optional[List[CSLName]] = Field(None, description="Authors")
    editor: Optional[List[CSLName]] = Field(None, description="Editors")
    translator: Optional[List[CSLName]] = Field(None, description="Translators")

    # TITLE FIELDS
    title: Optional[str] = Field(None, description="Primary title")
    container_title: Optional[str] = Field(None, description="Journal/book title")
    collection_title: Optional[str] = Field(None, description="Series title")

    # DATE FIELDS
    issued: Optional[CSLDate] = Field(None, description="Publication date")
    accessed: Optional[CSLDate] = Field(None, description="Access date (for web resources)")

    # PUBLICATION FIELDS
    publisher: Optional[str] = Field(None, description="Publisher name")
    publisher_place: Optional[str] = Field(None, description="Publication location")

    # LOCATOR FIELDS
    volume: Optional[str] = Field(None, description="Volume number")
    issue: Optional[str] = Field(None, description="Issue number")
    page: Optional[str] = Field(None, description="Page range (e.g., '123-456')")

    # IDENTIFIER FIELDS
    DOI: Optional[str] = Field(None, description="Digital Object Identifier")
    PMID: Optional[str] = Field(None, description="PubMed ID")
    PMCID: Optional[str] = Field(None, description="PubMed Central ID")
    ISBN: Optional[str] = Field(None, description="International Standard Book Number")
    ISSN: Optional[str] = Field(None, description="International Standard Serial Number")
    URL: Optional[HttpUrl] = Field(None, description="URL")

    # DESCRIPTIVE FIELDS
    abstract: Optional[str] = Field(None, description="Abstract")
    keyword: Optional[str] = Field(None, description="Keywords (comma-separated)")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en')")

    # CUSTOM TRACKING FIELDS (prefixed with _ to indicate internal use)
    citation_number: Optional[int] = Field(None, description="Sequential citation number [1], [2], etc.")
    added_by: Optional[str] = Field(None, description="Agent that added this citation")
    added_at: Optional[datetime] = Field(None, description="Timestamp when added")
    validated: Optional[bool] = Field(False, description="Whether citation has been validated")
    validation_method: Optional[str] = Field(None, description="How validated: DOI/PMID/URL/manual")
    credibility_score: Optional[float] = Field(None, description="Source credibility (0-1)", ge=0.0, le=1.0)
    impact_factor: Optional[float] = Field(None, description="Journal impact factor")
    citation_count: Optional[int] = Field(None, description="Times cited (from Google Scholar)")
    in_text_count: Optional[int] = Field(0, description="Times cited in this report")
    quality_issues: Optional[List[str]] = Field([], description="List of quality issues")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "smith2023ml",
                "type": "article-journal",
                "author": [
                    {"family": "Smith", "given": "John A."},
                    {"family": "Doe", "given": "Jane"}
                ],
                "title": "Machine Learning Approaches to Natural Language Processing",
                "container_title": "Nature Machine Intelligence",
                "issued": {"date_parts": [[2023, 6, 15]]},
                "volume": "5",
                "issue": "6",
                "page": "123-134",
                "DOI": "10.1038/s42256-023-00001-x",
                "URL": "https://doi.org/10.1038/s42256-023-00001-x",
                "citation_number": 1,
                "added_by": "researcher",
                "validated": True,
                "validation_method": "DOI",
                "credibility_score": 0.95,
                "impact_factor": 25.8
            }
        }

    def get_first_author_family_name(self) -> Optional[str]:
        """Get family name of first author."""
        if self.author and len(self.author) > 0:
            return self.author[0].family
        return None

    def get_year(self) -> Optional[int]:
        """Get publication year."""
        if self.issued:
            return self.issued.get_year()
        return None

    def get_all_authors_string(self) -> str:
        """Get all authors as semicolon-separated string."""
        if not self.author:
            return ""
        return "; ".join([str(a) for a in self.author])

    def get_citation_key(self) -> str:
        """Generate citation key like 'Smith2023'."""
        family = self.get_first_author_family_name()
        year = self.get_year()
        if family and year:
            return f"{family}{year}"
        return self.id

    def is_complete(self) -> bool:
        """Check if citation has all essential fields."""
        required = [self.title, self.issued]
        if self.type in ["article-journal", "article-magazine", "article-newspaper"]:
            required.append(self.container_title)
        if self.type in ["book", "chapter"]:
            required.append(self.publisher)

        has_author = self.author and len(self.author) > 0
        has_identifier = any([self.DOI, self.PMID, self.ISBN, self.URL])

        return all(required) and has_author and has_identifier

    def get_completeness_score(self) -> float:
        """Calculate metadata completeness (0-1)."""
        total_fields = 0
        filled_fields = 0

        # Core fields (weight: 2)
        core_fields = [self.title, self.author, self.issued]
        total_fields += len(core_fields) * 2
        filled_fields += sum([2 for f in core_fields if f])

        # Important fields (weight: 1.5)
        important_fields = [self.container_title, self.publisher]
        total_fields += len(important_fields) * 1.5
        filled_fields += sum([1.5 for f in important_fields if f])

        # Identifier fields (weight: 2)
        identifier_fields = [self.DOI, self.PMID, self.URL]
        total_fields += len(identifier_fields) * 2
        filled_fields += sum([2 for f in identifier_fields if f])

        # Optional fields (weight: 1)
        optional_fields = [self.volume, self.issue, self.page, self.abstract]
        total_fields += len(optional_fields)
        filled_fields += sum([1 for f in optional_fields if f])

        return filled_fields / total_fields if total_fields > 0 else 0.0


class CitationDatabase(BaseModel):
    """Collection of citations for a research job."""

    job_id: str = Field(description="Job ID this citation database belongs to")
    style: str = Field("apa", description="Citation style (apa, mla, chicago, vancouver, ieee)")
    citations: List[CSLCitation] = Field([], description="List of citations")
    metadata: dict = Field({}, description="Additional metadata")

    def add_citation(self, citation: CSLCitation) -> CSLCitation:
        """
        Add citation to database.

        Returns the citation (may be existing if duplicate detected).
        """
        # Check for exact ID match
        for existing in self.citations:
            if existing.id == citation.id:
                return existing

        # Assign citation number
        if citation.citation_number is None:
            citation.citation_number = len(self.citations) + 1

        self.citations.append(citation)
        return citation

    def get_citation(self, citation_id: str) -> Optional[CSLCitation]:
        """Retrieve citation by ID."""
        for cit in self.citations:
            if cit.id == citation_id:
                return cit
        return None

    def get_citation_by_number(self, number: int) -> Optional[CSLCitation]:
        """Retrieve citation by number."""
        for cit in self.citations:
            if cit.citation_number == number:
                return cit
        return None

    def get_all_citations(self) -> List[CSLCitation]:
        """Get all citations."""
        return self.citations

    def get_citations_count(self) -> int:
        """Get total number of citations."""
        return len(self.citations)

    def get_validated_count(self) -> int:
        """Get number of validated citations."""
        return sum([1 for cit in self.citations if cit.validated])

    def get_average_completeness(self) -> float:
        """Get average completeness score."""
        if not self.citations:
            return 0.0
        return sum([cit.get_completeness_score() for cit in self.citations]) / len(self.citations)
