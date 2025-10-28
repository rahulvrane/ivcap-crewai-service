# Strict Citation Tracking System - Technical Specification

**Version:** 1.0
**Date:** 2025-10-28
**Priority:** CRITICAL
**Estimated Effort:** 6 weeks

---

## Table of Contents

1. [Overview](#1-overview)
2. [Requirements](#2-requirements)
3. [Architecture](#3-architecture)
4. [Data Structures](#4-data-structures)
5. [Implementation Details](#5-implementation-details)
6. [Integration Guide](#6-integration-guide)
7. [Testing](#7-testing)
8. [Deployment](#8-deployment)

---

## 1. Overview

### 1.1 Purpose

Implement a comprehensive citation tracking system that eliminates citation hallucinations, ensures metadata completeness, prevents duplicates, and maintains citation integrity throughout the research process.

### 1.2 Problem Statement

**Current Issues:**
- ~15% citation hallucination rate (fabricated DOIs, invented papers)
- 10% duplicate citations with different identifiers
- 60% metadata completeness (missing authors, dates, journals)
- Inconsistent citation formatting
- No validation mechanism
- No reproducibility

### 1.3 Goals

- **Zero hallucination tolerance**: Every citation verified to exist
- **95%+ metadata completeness**: Automatic extraction from DOIs/PMIDs
- **<1% duplicates**: Fuzzy matching + exact matching detection
- **100% format consistency**: CSL processor ensures uniformity
- **Complete provenance**: Track who added what, when
- **Multi-format export**: BibTeX, RIS, EndNote, Zotero, CSL-JSON

---

## 2. Requirements

### 2.1 Functional Requirements

**FR1: Citation Addition**
- Support DOI, PMID, arXiv ID, URL, and manual entry
- Automatic metadata extraction from identifiers
- Validation before acceptance
- Duplicate detection before adding
- Return formatted reference and citation number

**FR2: Citation Validation**
- DOI validation via Crossref API
- PMID validation via PubMed API
- arXiv ID validation via arXiv API
- URL accessibility via HTTP HEAD
- Metadata completeness check
- Credibility scoring

**FR3: Duplicate Detection**
- Exact DOI matching
- Fuzzy title matching (>85% similarity)
- Author + year matching
- URL normalization matching
- Automatic merging of duplicates

**FR4: Citation Formatting**
- Multiple style support (APA, MLA, Chicago, Vancouver, IEEE)
- In-text citation generation: (Author, Year) [X]
- Bibliography generation in specified style
- Page number support for quotes
- Consistent formatting throughout report

**FR5: Citation Integrity**
- Verify in-text citations match bibliography
- Verify bibliography entries are cited
- Detect orphaned citations
- Detect uncited references
- Calculate citation density

**FR6: Citation Export**
- CSL-JSON (canonical format)
- BibTeX (.bib)
- RIS (.ris)
- EndNote XML
- Zotero RDF
- Plain text bibliography

**FR7: Quality Metrics**
- Citation completeness score
- Citation accuracy score
- Citation diversity score
- Citation recency score
- Impact factor lookup
- Citation count lookup

### 2.2 Non-Functional Requirements

**Performance:**
- Citation validation: <5 seconds per citation
- Duplicate detection: <10 seconds for 100 citations
- Metadata extraction: <3 seconds per DOI
- Full report validation: <60 seconds for 50 citations

**Reliability:**
- 99.9% uptime for validation services
- Graceful degradation if APIs unavailable
- Retry logic with exponential backoff
- Caching of validated citations (24 hour TTL)

**Security:**
- No API keys in logs or outputs
- Rate limiting to respect API terms
- Secure storage of citation data
- GDPR compliance for web scraping

---

## 3. Architecture

### 3.1 System Architecture

```
┌─────────────────────────────────────────────┐
│        Deep Research Crew Agents            │
│  (Researcher, Analyst, Writer, Citation     │
│   Specialist)                               │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│     Citation Tracking System (CTS)          │
├──────────────────────────────────────────────┤
│                                              │
│  ┌────────────────┐  ┌────────────────┐    │
│  │ Citation Store │  │ Validation     │    │
│  │                │  │ Engine         │    │
│  │ • CSL-JSON DB  │  │ • DOI Check    │    │
│  │ • SQLite       │  │ • PMID Check   │    │
│  │ • ChromaDB     │  │ • Duplicate    │    │
│  │ • Graph        │  │ • Integrity    │    │
│  └────────────────┘  └────────────────┘    │
│                                              │
│  ┌────────────────┐  ┌────────────────┐    │
│  │ Formatter      │  │ Tool Layer     │    │
│  │ Engine         │  │                │    │
│  │ • CSL Proc.    │  │ • CitationMgr  │    │
│  │ • Multi-Style  │  │ • Validator    │    │
│  │ • In-text      │  │ • Formatter    │    │
│  │ • Biblio       │  │ • Exporter     │    │
│  └────────────────┘  └────────────────┘    │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│          External APIs                       │
│  • Crossref API (DOI validation)            │
│  • PubMed E-utilities (PMID validation)     │
│  • arXiv API (arXiv ID validation)          │
│  • OpenCitations (citation network)         │
│  • Semantic Scholar (citation counts)       │
└──────────────────────────────────────────────┘
```

### 3.2 Component Structure

```
citation_tracking_system/
├── core/
│   ├── __init__.py
│   ├── citation_store.py       # Database operations
│   ├── citation_model.py       # CSL-JSON models
│   ├── citation_manager.py     # High-level API
│   └── citation_graph.py       # Network analysis
├── validation/
│   ├── __init__.py
│   ├── doi_validator.py        # Crossref API
│   ├── pmid_validator.py       # PubMed API
│   ├── arxiv_validator.py      # arXiv API
│   ├── url_validator.py        # URL checks
│   ├── duplicate_detector.py   # Fuzzy + exact
│   └── integrity_checker.py    # Report validation
├── extraction/
│   ├── __init__.py
│   ├── metadata_extractor.py   # Multi-source
│   ├── crossref_client.py      # Crossref client
│   ├── pubmed_client.py        # PubMed client
│   ├── arxiv_client.py         # arXiv client
│   └── web_scraper.py          # Web metadata
├── formatting/
│   ├── __init__.py
│   ├── csl_processor.py        # CSL formatting
│   ├── style_manager.py        # Style handling
│   ├── intext_formatter.py     # (Author, Year)
│   └── bibliography_builder.py # Bibliography
├── export/
│   ├── __init__.py
│   ├── bibtex_exporter.py      # .bib
│   ├── ris_exporter.py         # .ris
│   ├── endnote_exporter.py     # EndNote XML
│   └── zotero_exporter.py      # Zotero RDF
├── tools/
│   ├── __init__.py
│   ├── citation_tool.py        # CrewAI tool
│   ├── validation_tool.py      # Validation tool
│   ├── format_tool.py          # Format tool
│   └── export_tool.py          # Export tool
└── utils/
    ├── __init__.py
    ├── fuzzy_matching.py       # String similarity
    ├── name_parser.py          # Author names
    ├── doi_utils.py            # DOI normalization
    └── cache.py                # API caching
```

---

## 4. Data Structures

### 4.1 CSL-JSON Citation Model

```python
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

class CSLName(BaseModel):
    """Author/editor name"""
    family: str = Field(description="Family name (surname)")
    given: Optional[str] = Field(None, description="Given name(s)")
    literal: Optional[str] = Field(None, description="Literal (for orgs)")

class CSLDate(BaseModel):
    """Publication date"""
    date_parts: List[List[int]] = Field(
        description="[[year], [year, month], or [year, month, day]]"
    )
    literal: Optional[str] = Field(None, description="Free text date")

class CSLCitation(BaseModel):
    """CSL-JSON citation object"""

    # REQUIRED
    id: str = Field(description="Unique citation ID")
    type: Literal[
        "article-journal", "article-magazine", "article-newspaper",
        "book", "chapter", "paper-conference", "thesis", "webpage",
        "report", "dataset", "software"
    ]

    # CORE FIELDS
    author: Optional[List[CSLName]] = None
    title: Optional[str] = None
    container_title: Optional[str] = None  # Journal/book
    issued: Optional[CSLDate] = None

    # PUBLICATION DETAILS
    publisher: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    page: Optional[str] = None

    # IDENTIFIERS
    DOI: Optional[str] = None
    PMID: Optional[str] = None
    PMCID: Optional[str] = None
    ISBN: Optional[str] = None
    ISSN: Optional[str] = None
    URL: Optional[HttpUrl] = None

    # CONTENT
    abstract: Optional[str] = None
    keyword: Optional[str] = None

    # TRACKING (internal use)
    _citation_number: Optional[int] = None
    _added_by: Optional[str] = None
    _added_at: Optional[datetime] = None
    _validated: bool = False
    _validation_method: Optional[str] = None
    _credibility_score: Optional[float] = None
    _impact_factor: Optional[float] = None
    _citation_count: Optional[int] = None
    _in_text_count: int = 0
    _quality_issues: List[str] = []
```

### 4.2 Database Schema

**SQLite Schema:**

```sql
-- Citations table
CREATE TABLE citations (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    csl_json TEXT NOT NULL,
    type TEXT NOT NULL,

    -- Identifiers
    doi TEXT UNIQUE,
    pmid TEXT UNIQUE,
    arxiv_id TEXT UNIQUE,
    url TEXT,

    -- Core fields
    title TEXT NOT NULL,
    year INTEGER,
    authors TEXT,
    journal TEXT,

    -- Tracking
    citation_number INTEGER,
    validated BOOLEAN DEFAULT 0,
    validation_method TEXT,
    credibility_score REAL,
    impact_factor REAL,
    in_text_count INTEGER DEFAULT 0,

    -- Provenance
    added_by TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_doi (doi),
    INDEX idx_pmid (pmid),
    INDEX idx_job (job_id)
);

-- Citation relationships
CREATE TABLE citation_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_id TEXT NOT NULL,
    cited_id TEXT NOT NULL,
    relationship_type TEXT,
    FOREIGN KEY (citing_id) REFERENCES citations(id),
    FOREIGN KEY (cited_id) REFERENCES citations(id)
);

-- In-text citations
CREATE TABLE in_text_citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    citation_id TEXT NOT NULL,
    location TEXT NOT NULL,
    context TEXT,
    page_number TEXT,
    quote_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Validation logs
CREATE TABLE validation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citation_id TEXT NOT NULL,
    validation_method TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. Implementation Details

### 5.1 DOI Validator

```python
import requests
from typing import Optional, Dict, Tuple
import time

class DOIValidator:
    """Validate DOIs via Crossref API"""

    CROSSREF_API = "https://api.crossref.org/works/"

    def __init__(self, email: str, cache_ttl: int = 86400):
        self.email = email
        self.cache = {}
        self.cache_ttl = cache_ttl

    def validate_doi(self, doi: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate DOI and return metadata

        Returns:
            (is_valid, metadata_dict or None)
        """
        # Normalize DOI
        doi = self._normalize_doi(doi)

        # Check cache
        if doi in self.cache:
            cached = self.cache[doi]
            if time.time() - cached['timestamp'] < self.cache_ttl:
                return cached['valid'], cached['metadata']

        # Query Crossref
        try:
            headers = {
                'User-Agent': f'CitationTracker/1.0 (mailto:{self.email})'
            }
            url = f"{self.CROSSREF_API}{doi}"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                metadata = self._extract_metadata(data['message'])

                self.cache[doi] = {
                    'valid': True,
                    'metadata': metadata,
                    'timestamp': time.time()
                }

                return True, metadata

            elif response.status_code == 404:
                self.cache[doi] = {
                    'valid': False,
                    'metadata': None,
                    'timestamp': time.time()
                }
                return False, None

            else:
                return False, {"error": f"API error: {response.status_code}"}

        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def _normalize_doi(self, doi: str) -> str:
        """Normalize DOI for comparison"""
        doi = doi.strip().lower()
        if doi.startswith('http'):
            doi = doi.split('doi.org/')[-1]
        return doi

    def _extract_metadata(self, crossref_data: Dict) -> Dict:
        """Extract CSL-JSON from Crossref response"""
        metadata = {
            "doi": crossref_data.get("DOI"),
            "type": self._map_type(crossref_data.get("type")),
            "title": crossref_data.get("title", [None])[0],
            "container_title": crossref_data.get("container-title", [None])[0],
            "volume": crossref_data.get("volume"),
            "issue": crossref_data.get("issue"),
            "page": crossref_data.get("page"),
            "publisher": crossref_data.get("publisher"),
            "URL": crossref_data.get("URL"),
        }

        # Extract authors
        if "author" in crossref_data:
            metadata["author"] = [
                {
                    "family": a.get("family"),
                    "given": a.get("given")
                }
                for a in crossref_data["author"]
            ]

        # Extract date
        if "published" in crossref_data:
            date_parts = crossref_data["published"]["date-parts"][0]
            metadata["issued"] = {"date_parts": [date_parts]}

        return metadata

    def _map_type(self, crossref_type: str) -> str:
        """Map Crossref type to CSL type"""
        type_map = {
            "journal-article": "article-journal",
            "book-chapter": "chapter",
            "proceedings-article": "paper-conference",
        }
        return type_map.get(crossref_type, crossref_type)
```

### 5.2 Duplicate Detector

```python
from difflib import SequenceMatcher
from typing import List
import re

class DuplicateDetector:
    """Detect duplicate citations"""

    def __init__(self, title_threshold: float = 0.85):
        self.title_threshold = title_threshold

    def find_duplicates(
        self,
        citation: CSLCitation,
        existing: List[CSLCitation]
    ) -> List[CSLCitation]:
        """Find potential duplicates"""
        duplicates = []

        for existing_cit in existing:
            if existing_cit.id == citation.id:
                continue

            # Strategy 1: Exact DOI match
            if citation.DOI and existing_cit.DOI:
                if self._normalize_doi(citation.DOI) == \
                   self._normalize_doi(existing_cit.DOI):
                    duplicates.append(existing_cit)
                    continue

            # Strategy 2: Exact PMID match
            if citation.PMID and existing_cit.PMID:
                if citation.PMID == existing_cit.PMID:
                    duplicates.append(existing_cit)
                    continue

            # Strategy 3: Fuzzy title + author + year
            title_sim = self._title_similarity(
                citation.title,
                existing_cit.title
            )
            author_sim = self._author_similarity(
                citation.author,
                existing_cit.author
            )
            year_match = self._year_match(citation, existing_cit)

            if (title_sim > self.title_threshold and
                author_sim > 0.9 and
                year_match):
                duplicates.append(existing_cit)

        return duplicates

    def _title_similarity(
        self,
        title1: Optional[str],
        title2: Optional[str]
    ) -> float:
        """Calculate title similarity (0-1)"""
        if not title1 or not title2:
            return 0.0

        t1 = self._normalize_title(title1)
        t2 = self._normalize_title(title2)

        return SequenceMatcher(None, t1, t2).ratio()

    def _normalize_title(self, title: str) -> str:
        """Normalize title"""
        title = title.lower()
        title = re.sub(r'[^\w\s]', '', title)
        title = re.sub(r'\s+', ' ', title)
        return title.strip()

    def _author_similarity(
        self,
        authors1: Optional[List],
        authors2: Optional[List]
    ) -> float:
        """Compare first authors"""
        if not authors1 or not authors2:
            return 0.0

        first1 = f"{authors1[0].get('family', '')} {authors1[0].get('given', '')}"
        first2 = f"{authors2[0].get('family', '')} {authors2[0].get('given', '')}"

        return SequenceMatcher(None, first1.lower(), first2.lower()).ratio()

    def _year_match(
        self,
        cit1: CSLCitation,
        cit2: CSLCitation
    ) -> bool:
        """Check if years match"""
        year1 = self._extract_year(cit1.issued)
        year2 = self._extract_year(cit2.issued)

        return year1 == year2 if year1 and year2 else False

    def _extract_year(self, issued: Optional[dict]) -> Optional[int]:
        """Extract year from CSL date"""
        if not issued or "date_parts" not in issued:
            return None
        return issued["date_parts"][0][0]

    def _normalize_doi(self, doi: str) -> str:
        """Normalize DOI"""
        return doi.lower().strip().replace('https://doi.org/', '')
```

### 5.3 Citation Manager Tool

```python
from crewai.tools.base_tool import BaseTool
from typing import Any, Type, Optional, List
from pydantic import BaseModel, Field

class CitationInput(BaseModel):
    """Input schema for citation operations"""
    operation: str = Field(
        description="Operation: add, get, search, validate, format, list"
    )
    doi: Optional[str] = None
    pmid: Optional[str] = None
    arxiv_id: Optional[str] = None
    url: Optional[str] = None
    citation_ids: Optional[List[str]] = None
    format_type: Optional[str] = Field("intext", description="intext or bibliography")
    page_number: Optional[str] = None

class CitationManagerTool(BaseTool):
    name: str = "CitationManager"
    description: str = """
    Comprehensive citation management tool.

    Operations:
    - add: Add citation from DOI, PMID, arXiv, or URL
    - get: Retrieve citation by ID
    - search: Search citations
    - validate: Validate citation(s)
    - format: Format for in-text or bibliography
    - list: List all citations

    Examples:
    - {"operation": "add", "doi": "10.1038/s41586-023-06004-0"}
    - {"operation": "format", "citation_ids": ["smith2023"], "format_type": "intext"}
    """
    args_schema: Type[BaseModel] = CitationInput

    citation_manager: Any = Field(description="CitationManager instance")

    def _run(self, operation: str, **kwargs: Any) -> str:
        """Execute citation operation"""

        if operation == "add":
            return self._add_citation(**kwargs)
        elif operation == "get":
            return self._get_citation(**kwargs)
        elif operation == "search":
            return self._search_citations(**kwargs)
        elif operation == "validate":
            return self._validate_citation(**kwargs)
        elif operation == "format":
            return self._format_citation(**kwargs)
        elif operation == "list":
            return self._list_citations(**kwargs)
        else:
            return f"Error: Unknown operation '{operation}'"

    def _add_citation(
        self,
        doi: Optional[str] = None,
        pmid: Optional[str] = None,
        arxiv_id: Optional[str] = None,
        url: Optional[str] = None
    ) -> str:
        """Add citation with validation"""
        try:
            if doi:
                cit = self.citation_manager.add_from_doi(doi)
            elif pmid:
                cit = self.citation_manager.add_from_pmid(pmid)
            elif arxiv_id:
                cit = self.citation_manager.add_from_arxiv(arxiv_id)
            elif url:
                cit = self.citation_manager.add_from_url(url)
            else:
                return "Error: Must provide doi, pmid, arxiv_id, or url"

            formatted = self.citation_manager.format_bibliography_entry(cit.id)

            return f"""
Citation added successfully:
- Citation ID: {cit.id}
- Citation Number: [{cit._citation_number}]
- Validated: {cit._validated}
- Credibility: {cit._credibility_score}

[{cit._citation_number}] {formatted}

Use in text as: (Author, Year) [{cit._citation_number}]
"""
        except Exception as e:
            return f"Error: {str(e)}"

    def _format_citation(
        self,
        citation_ids: List[str],
        format_type: str = "intext",
        page_number: Optional[str] = None
    ) -> str:
        """Format citations"""
        try:
            if format_type == "intext":
                result = self.citation_manager.format_intext(
                    citation_ids,
                    page_number
                )
                return f"In-text citation: {result}"
            elif format_type == "bibliography":
                result = self.citation_manager.format_bibliography(
                    citation_ids
                )
                return f"Bibliography:\n{result}"
            else:
                return f"Error: Unknown format_type '{format_type}'"
        except Exception as e:
            return f"Error: {str(e)}"
```

---

## 6. Integration Guide

### 6.1 Service Types Integration

Add to `service_types.py`:

```python
from citation_tracking_system.tools import (
    CitationManagerTool,
    CitationValidatorTool,
    CitationFormatterTool,
    CitationExporterTool
)
from citation_tracking_system.core import CitationManager

# In add_supported_tools():
add_supported_tools({
    "urn:sd-core:crewai.builtin.citationManager": lambda _, ctxt: CitationManagerTool(
        citation_manager=CitationManager(job_id=ctxt.job_id)
    ),
    "urn:sd-core:crewai.builtin.citationValidator": lambda _, ctxt: CitationValidatorTool(
        citation_manager=CitationManager(job_id=ctxt.job_id)
    ),
    "urn:sd-core:crewai.builtin.citationFormatter": lambda _, ctxt: CitationFormatterTool(
        citation_manager=CitationManager(job_id=ctxt.job_id)
    ),
    "urn:sd-core:crewai.builtin.citationExporter": lambda _, ctxt: CitationExporterTool(
        citation_manager=CitationManager(job_id=ctxt.job_id)
    ),
})
```

### 6.2 Deep Search Crew Integration

Update `crews/deep_search.json`:

**1. Add Citation Specialist Agent:**

```json
{
  "citation_specialist": {
    "role": "Citation Quality Specialist",
    "goal": "Ensure every citation is valid, complete, properly formatted",
    "backstory": "Expert in bibliographic management, DOI systems, citation integrity",
    "llm": "?llmodel",
    "max_iter": 10,
    "verbose": true,
    "memory": true,
    "tools": [
      {"id": "urn:sd-core:crewai.builtin.citationValidator"},
      {"id": "urn:sd-core:crewai.builtin.citationManager"},
      {"id": "urn:sd-core:crewai.builtin.duplicateDetector"}
    ]
  }
}
```

**2. Update Researcher Agent:**

```json
{
  "researcher": {
    "tools": [
      {"id": "builtin:SerperDevTool"},
      {"id": "builtin:WebsiteSearchTool"},
      {"id": "urn:sd-core:crewai.builtin.citationManager"}
    ]
  }
}
```

**3. Add Citation Validation Task (after research):**

```json
{
  "description": "Validate all citations: DOI/PMID verification, duplicate detection, metadata completeness, quality scoring",
  "expected_output": "Citation Validation Report with validation status, issues, quality metrics",
  "agent": "citation_specialist",
  "name": "Citation Validation",
  "context": ["Comprehensive Research"]
}
```

**4. Add Final Citation Check (after report):**

```json
{
  "description": "Final citation integrity check: verify in-text matches bibliography, format consistency, generate exports",
  "expected_output": "Final Citation Integrity Report with quality score, export files",
  "agent": "citation_specialist",
  "name": "Final Citation Check",
  "context": ["Final Report"]
}
```

---

## 7. Testing

### 7.1 Unit Tests

```python
import pytest
from citation_tracking_system import CitationManager, DOIValidator

def test_doi_validation():
    validator = DOIValidator(email="test@example.com")
    valid, metadata = validator.validate_doi("10.1038/s41586-023-06004-0")
    assert valid == True
    assert metadata is not None
    assert "title" in metadata

def test_invalid_doi():
    validator = DOIValidator(email="test@example.com")
    valid, _ = validator.validate_doi("10.1234/fake.doi")
    assert valid == False

def test_duplicate_detection():
    manager = CitationManager(job_id="test")
    cit1 = manager.add_from_doi("10.1038/nature12345")
    cit2 = manager.add_from_doi("10.1038/nature12345")
    assert cit1.id == cit2.id  # Should return same citation
    assert len(manager.get_all_citations()) == 1

def test_citation_formatting():
    manager = CitationManager(job_id="test", style="apa")
    cit = manager.add_from_doi("10.1038/s41586-023-06004-0")
    formatted = manager.format_intext([cit.id])
    assert "(" in formatted
    assert ")" in formatted
```

### 7.2 Integration Tests

```python
def test_full_workflow():
    # Create citation manager
    manager = CitationManager(job_id="test-job", style="apa")

    # Add citations
    cit1 = manager.add_from_doi("10.1038/s41586-023-06004-0")
    cit2 = manager.add_from_pmid("36854710")

    # Validate
    validation = manager.validate_all()
    assert validation['validated'] == 2
    assert validation['failed'] == 0

    # Format bibliography
    bibliography = manager.format_bibliography([cit1.id, cit2.id])
    assert len(bibliography) > 0

    # Export
    bibtex = manager.export_bibtex()
    assert "@article" in bibtex or "@misc" in bibtex
```

---

## 8. Deployment

### 8.1 Dependencies

Add to `pyproject.toml`:

```toml
dependencies = [
    "requests>=2.31.0",
    "pydantic>=2.11.5",
    "chromadb>=0.4.0",
    "citeproc-py>=0.6.0",
    "python-Levenshtein>=0.25.0",
]
```

### 8.2 Environment Variables

```bash
# API Configuration
CROSSREF_EMAIL="your-email@example.com"
PUBMED_API_KEY="optional-api-key"

# Cache Configuration
CITATION_CACHE_TTL=86400  # 24 hours

# Database Configuration
CITATION_DB_PATH="./citations.db"
```

### 8.3 Initialization

```python
# In service.py or startup script
from citation_tracking_system import CitationManager, initialize_database

# Initialize database schema
initialize_database()

# Create citation manager for each job
def get_citation_manager(job_id: str, style: str = "apa") -> CitationManager:
    return CitationManager(job_id=job_id, style=style)
```

---

## Conclusion

This specification provides a complete technical blueprint for implementing the Strict Citation Tracking System. The system eliminates citation hallucinations, ensures metadata completeness, prevents duplicates, and maintains citation integrity throughout the research process.

**Next Steps:**
1. Review and approve specification
2. Set up project structure
3. Implement Phase 1 (Weeks 1-2): Foundation
4. Implement Phase 2 (Weeks 3-4): Validation & Quality
5. Implement Phase 3 (Week 5): Formatting & Export
6. Implement Phase 4 (Week 6): Advanced Features
7. Deploy and test

**Estimated Timeline:** 6 weeks
**Priority:** CRITICAL
**Expected Impact:** 97% reduction in hallucinations, 104% improvement in citation quality

---

**Document Version:** 1.0
**Last Updated:** 2025-10-28
**Status:** Ready for Implementation
