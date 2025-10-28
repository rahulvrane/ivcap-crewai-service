# Prompt for Recreating Citation Tracking System from Scratch

**Copy and paste this entire prompt into a new Claude Code session to rebuild the citation tracking system.**

---

## Project Context

I'm working on an IVCAP CrewAI service that runs research crews (multi-agent systems). The current implementation has a critical problem: **agents hallucinate citations** - they make up DOIs and PMIDs that don't exist, fabricate paper titles, and create fake references.

I need you to build a comprehensive **Citation Tracking System** that eliminates hallucinations by validating every citation against authoritative APIs before acceptance.

## Repository Structure

This is a Python project using:
- **CrewAI**: Multi-agent framework
- **Pydantic**: Data validation
- **FastAPI/ivcap_ai_tool**: Service framework

Key existing files:
- `service.py`: Main service entry point
- `service_types.py`: Type definitions, Context, CrewA class
- `crews/deep_search.json`: Deep research crew definition with 3 agents (researcher, analyst, writer)

## Your Mission

Build a citation tracking system with these capabilities:

### Core Requirements

1. **Zero-Hallucination Validation**
   - Validate DOIs against Crossref API (https://api.crossref.org/works/{doi})
   - Validate PMIDs against PubMed E-utilities API
   - Reject any citation that can't be verified
   - Expected impact: Reduce hallucinations from 15% to <0.5%

2. **Automatic Metadata Extraction**
   - Extract complete bibliographic data from DOI (authors, title, journal, year, volume, pages)
   - Extract from PMID (PubMed metadata including abstract)
   - Store in CSL-JSON format (Citation Style Language JSON standard)
   - Expected impact: Increase metadata completeness from 60% to >95%

3. **Duplicate Detection**
   - Exact matching: DOI, PMID, URL normalization
   - Fuzzy matching: Title similarity >85%, Author similarity >90%, Year match
   - Automatic merging of duplicates
   - Expected impact: Reduce duplicates from 10% to <1%

4. **Multi-Format Output**
   - In-text citations: `(Smith, 2023) [1]`
   - Formatted bibliography in APA style
   - BibTeX export for LaTeX users
   - Quality metrics reporting

5. **CrewAI Integration**
   - Provide a CrewAI BaseTool that agents can use
   - Operations: add (DOI/PMID/URL), validate, format, export
   - Integrate with existing deep_search crew

## Technical Architecture

### Directory Structure to Create

```
citation_tracking/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── citation_model.py      # CSL-JSON Pydantic models
│   └── citation_manager.py    # Main API coordinator
├── validation/
│   ├── __init__.py
│   ├── doi_validator.py       # Crossref API integration
│   ├── pmid_validator.py      # PubMed API integration
│   └── duplicate_detector.py  # Duplicate detection logic
├── tools/
│   ├── __init__.py
│   └── citation_tool.py       # CrewAI tool wrapper
└── utils/
    └── __init__.py
```

### Data Model Specification

**CSL-JSON Citation Model** (use Pydantic):

```python
class CSLName(BaseModel):
    family: str                    # Last name
    given: Optional[str]           # First name
    literal: Optional[str]         # For organizations

class CSLDate(BaseModel):
    date_parts: List[List[int]]    # [[year, month, day]]
    literal: Optional[str]

class CSLCitation(BaseModel):
    # Required
    id: str                        # Unique identifier
    type: Literal["article-journal", "book", "chapter", ...]

    # Core fields
    author: Optional[List[CSLName]]
    title: Optional[str]
    container_title: Optional[str] # Journal/book title
    issued: Optional[CSLDate]      # Publication date

    # Identifiers
    DOI: Optional[str]
    PMID: Optional[str]
    PMCID: Optional[str]
    URL: Optional[HttpUrl]

    # Publication details
    publisher: Optional[str]
    volume: Optional[str]
    issue: Optional[str]
    page: Optional[str]

    # Tracking metadata
    citation_number: Optional[int]  # [1], [2], etc.
    validated: bool = False
    validation_method: Optional[str]
    credibility_score: Optional[float]
    in_text_count: int = 0
```

### API Integration Specifications

**1. Crossref API (DOI Validation)**
- Endpoint: `https://api.crossref.org/works/{doi}`
- Headers: `User-Agent: CitationTracker/1.0 (mailto:your-email@example.com)`
- Cache responses for 24 hours
- Map Crossref response to CSL-JSON fields
- Handle 404 (not found) vs 200 (found)

**2. PubMed E-utilities API (PMID Validation)**
- Endpoint: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi`
- Parameters: `db=pubmed&id={pmid}&retmode=xml&rettype=abstract`
- Parse XML response to extract metadata
- Convert PubMed XML to CSL-JSON format

**3. Duplicate Detection Algorithm**
```python
def is_duplicate(cit1, cit2):
    # Strategy 1: Exact identifier match
    if cit1.DOI and cit2.DOI:
        if normalize_doi(cit1.DOI) == normalize_doi(cit2.DOI):
            return True

    # Strategy 2: Fuzzy title + author + year
    title_similarity = calculate_similarity(cit1.title, cit2.title)
    author_similarity = compare_first_author(cit1.author, cit2.author)
    year_match = (cit1.get_year() == cit2.get_year())

    if title_similarity > 0.85 and author_similarity > 0.90 and year_match:
        return True

    return False
```

### CrewAI Tool Interface

**Tool Name**: `CitationManager`

**Operations**:

```json
// Add citation from DOI
{"operation": "add", "doi": "10.1038/s41586-023-06004-0"}

// Add from PMID
{"operation": "add", "pmid": "36854710"}

// Add from URL
{"operation": "add", "url": "https://arxiv.org/abs/2301.12345"}

// Validate all citations
{"operation": "validate"}

// Format in-text citation
{"operation": "format", "citation_ids": ["smith2023"], "format_type": "intext"}

// Format with page number
{"operation": "format", "citation_ids": ["smith2023"], "format_type": "intext", "page_number": "42"}

// Generate bibliography
{"operation": "format", "format_type": "bibliography"}

// Export BibTeX
{"operation": "export", "export_format": "bibtex"}

// List all citations
{"operation": "list"}
```

**Tool Response Format**:
```
✓ Citation added successfully

Citation Details:
- ID: smith2023ml
- Number: [1]
- Validated: ✓ Yes (DOI)
- Completeness: 95%

Formatted Reference:
[1] Smith, J. A. & Doe, J. (2023). Machine Learning Approaches. Nature, 5(6), 123-134. https://doi.org/10.1038/s42256-023-00001-x

Use in text as: (Smith, 2023) [1]
```

## Implementation Steps

### Step 1: Create Core Data Models

File: `citation_tracking/core/citation_model.py`

Implement:
- `CSLName` class with family, given, literal fields
- `CSLDate` class with date_parts
- `CSLCitation` class with all fields listed above
- `CitationDatabase` class to manage collection of citations
- Helper methods: `get_year()`, `get_first_author_family_name()`, `is_complete()`, `get_completeness_score()`

### Step 2: Implement DOI Validator

File: `citation_tracking/validation/doi_validator.py`

Implement:
- `DOIValidator` class with caching (24 hour TTL)
- `validate_doi(doi)` method returns (is_valid, metadata_dict)
- `_normalize_doi(doi)` removes prefixes, validates format
- `_extract_metadata(crossref_data)` converts to CSL-JSON
- `create_citation_from_doi(doi)` returns CSLCitation object
- Handle network errors gracefully

### Step 3: Implement PMID Validator

File: `citation_tracking/validation/pmid_validator.py`

Implement:
- `PMIDValidator` class with XML parsing
- `validate_pmid(pmid)` method returns (is_valid, metadata_dict)
- `_normalize_pmid(pmid)` validates numeric format
- `_extract_metadata(xml_element)` parses PubMed XML to CSL-JSON
- `create_citation_from_pmid(pmid)` returns CSLCitation object
- Handle month name to number conversion

### Step 4: Implement Duplicate Detector

File: `citation_tracking/validation/duplicate_detector.py`

Implement:
- `DuplicateDetector` class with configurable thresholds
- `find_duplicates(citation, existing_citations)` returns list of duplicates
- `_calculate_duplicate_score(cit1, cit2)` returns 0-1 score
- `_title_similarity(title1, title2)` using SequenceMatcher
- `_author_similarity(authors1, authors2)` compares first authors
- `merge_citations(original, duplicate)` merges metadata

### Step 5: Create Citation Manager

File: `citation_tracking/core/citation_manager.py`

Implement:
- `CitationManager` class coordinating all components
- `__init__(job_id, style="apa")` initializes database and validators
- `add_from_doi(doi)` validates, checks duplicates, adds to database
- `add_from_pmid(pmid)` same flow
- `add_from_url(url)` creates basic citation
- `validate_all()` returns validation report
- `format_intext(citation_ids, page_number)` returns formatted string
- `format_bibliography_entry(citation_id)` returns formatted reference
- `export_bibtex()` exports all citations as BibTeX
- `get_quality_metrics()` returns validation rates, completeness

### Step 6: Create CrewAI Tool

File: `citation_tracking/tools/citation_tool.py`

Implement:
- `CitationInput` Pydantic model for tool parameters
- `CitationManagerTool` extending CrewAI's `BaseTool`
- `name = "CitationManager"`
- Detailed `description` with examples
- `_run(operation, **kwargs)` dispatches to correct method
- `_add_citation()` calls citation_manager, formats response nicely
- `_validate_citations()` returns validation report
- `_format_citation()` returns formatted text
- `_list_citations()` returns summary with quality metrics
- `_export_citations()` returns BibTeX

### Step 7: Integration with Service

**A. Modify `service.py`:**

Add import:
```python
from citation_tracking import CitationManager, CitationManagerTool
```

Add to `add_supported_tools()`:
```python
"urn:sd-core:crewai.builtin.citationManager": lambda _, ctxt: CitationManagerTool(
    citation_manager=CitationManager(job_id=ctxt.job_id)
),
```

**B. Modify `service_types.py`:**

Add import:
```python
from citation_tracking import CitationManager, CitationManagerTool
```

Update `Context` dataclass:
```python
@dataclass
class Context():
    job_id: str  # ADD THIS
    vectordb_config: dict
    tmp_dir: str = "/tmp"
```

Update `CrewA.as_crew()` method:
```python
def as_crew(self, llm: LLM, job_id: str, **kwargs) -> Crew:
    ctxt = Context(job_id=job_id, vectordb_config=create_vectordb_config(job_id))
    # ... rest
```

**C. Modify `crews/deep_search.json`:**

Add to researcher agent tools:
```json
{
  "id": "urn:sd-core:crewai.builtin.citationManager",
  "name": "CitationManager",
  "description": "CRITICAL: Use for EVERY source. Validates DOI/PMID, prevents hallucinations."
}
```

Add to writer agent tools:
```json
{
  "id": "urn:sd-core:crewai.builtin.citationManager",
  "name": "CitationManager",
  "description": "Format citations for in-text and bibliography."
}
```

Add new citation_specialist agent:
```json
"citation_specialist": {
  "role": "Citation Quality Specialist",
  "goal": "Ensure every citation is valid, complete, properly formatted with zero tolerance for hallucinations",
  "backstory": "Expert in bibliographic management, DOI systems, PubMed databases. Zero tolerance for fabricated sources.",
  "llm": "?llmodel",
  "max_iter": 10,
  "verbose": true,
  "memory": true,
  "tools": [
    {
      "id": "urn:sd-core:crewai.builtin.citationManager",
      "name": "CitationManager",
      "description": "Validate and manage all citations."
    }
  ],
  "allow_delegation": false
}
```

Update researcher task description (around step 9):
```
9. CRITICAL - USE CITATION TOOL: For EVERY source, add using CitationManager:
   - If DOI: {"operation": "add", "doi": "10.xxxx/xxxxx"}
   - If PMID: {"operation": "add", "pmid": "12345678"}
   - If URL: {"operation": "add", "url": "https://..."}
   Tool validates, extracts metadata, assigns numbers automatically.
10. NEVER manually create citations - always use tool
11. If validation fails, source doesn't exist - find different source
12. After adding all sources: {"operation": "validate"}
```

### Step 8: Create __init__.py Files

Create proper Python package structure with appropriate imports in each `__init__.py`.

### Step 9: Testing

Create simple test to verify:
```python
from citation_tracking import CitationManager

manager = CitationManager(job_id="test-123")
citation = manager.add_from_doi("10.1038/s41586-023-06004-0")
print(f"✓ Added: {citation.title}")
print(f"✓ Validated: {citation.validated}")
```

### Step 10: Commit

```bash
git add citation_tracking/ service.py service_types.py crews/deep_search.json
git commit -m "Implement citation tracking system with zero-hallucination validation"
git push origin [BRANCH_NAME]
```

## Key Implementation Notes

1. **Error Handling**: Gracefully handle API failures, network timeouts
2. **Caching**: Cache API responses for 24 hours to reduce requests
3. **Logging**: Use Python logging module for debugging
4. **Type Safety**: Use Pydantic for all data models
5. **String Similarity**: Use `difflib.SequenceMatcher` for fuzzy matching
6. **XML Parsing**: Use `xml.etree.ElementTree` for PubMed responses
7. **JSON Requests**: Use `requests` library with proper User-Agent headers

## Expected Outcomes

After implementation:
- Citation hallucination rate: 15% → <0.5% (**-97%**)
- Metadata completeness: 60% → >95% (**+58%**)
- Duplicate citations: 10% → <1% (**-90%**)
- Format consistency: 70% → 100% (**+43%**)

## Success Criteria

✅ All citation_tracking Python files created without syntax errors
✅ DOI validation works against Crossref API
✅ PMID validation works against PubMed API
✅ Duplicate detection catches identical papers
✅ CrewAI tool provides all operations (add, validate, format, export)
✅ Integration with service.py, service_types.py, deep_search.json complete
✅ Python imports work: `from citation_tracking import CitationManager`
✅ No hallucinated citations accepted
✅ BibTeX export produces valid output

## References

For implementation details, see the technical specifications that should exist in:
- `docs/CITATION_TRACKING_SPEC.md` (if available)
- `docs/DEEP_RESEARCH_ANALYSIS.md` (if available)

However, you should be able to implement this system based solely on this prompt.

## Questions to Ask Me

If you encounter:
- Uncertainty about data structure
- API integration issues
- Merge conflicts with existing code
- Missing dependencies

Please ask before proceeding.

---

**START IMPLEMENTATION NOW**

Begin with Step 1 (Core Data Models) and work through each step sequentially. Show me your progress as you complete each major component.
