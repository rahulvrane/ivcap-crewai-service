# Prompt for Recreating Citation Tracking System from Scratch

**Copy and paste this entire prompt into a new Claude Code session to rebuild the citation tracking system.**

---

## Project Context

I'm working on an IVCAP CrewAI service that runs research crews (multi-agent systems). The current implementation has two critical problems:

1. **Agents hallucinate citations** - they make up DOIs and PMIDs that don't exist, fabricate paper titles, and create fake references.
2. **Agents add superficial citations** - they cite papers without understanding or explaining WHY those sources are relevant, leading to "citation padding" where references are added just to appear scholarly.

I need you to build a comprehensive **Citation Tracking System** that:
- Eliminates hallucinations by validating every citation against authoritative APIs
- **Eliminates superficial citations by REQUIRING agents to explain their intellectual reasoning**

## Why Usage Context Tracking Matters

**The Problem with Traditional Citation Systems:**
Traditional citation tools just track *that* a source was cited, not *why* or *how* it's being used. This leads to:
- **Citation padding**: Adding references to look credible without engaging with content
- **Weak argumentation**: Citations don't clearly support claims
- **Mechanical citation**: Agents treat citations as boxes to check, not intellectual contributions
- **Opaque reasoning**: Readers can't understand why sources were chosen

**Our Solution - Mandatory Usage Context:**
Every citation MUST include:
- **Rationale**: WHY this specific source was chosen (forces selectivity)
- **Contextual Value**: HOW it supports the argument (forces integration)
- **Supporting Claim**: WHAT specific assertion it validates (forces precision)
- **Excerpt/Quote**: WHAT content is actually used (forces engagement)

**Expected Benefits:**
- Agents must **read and understand** sources (not just cite titles)
- Citations become **evidence of intellectual work**, not decoration
- Readers can **trace reasoning** from claim → citation → source content
- **Quality over quantity**: 10 well-justified citations > 50 superficial ones
- Enables **automatic quality assessment** of research depth

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

2. **Mandatory Usage Context Tracking** (NEW - CRITICAL)
   - **REQUIRE agents to explain WHY each source is used**
   - Capture rationale (why source chosen), contextual_value (how it supports argument), supporting_claim (what it proves)
   - Track excerpt/quote (what specific content is used)
   - Record usage_type (evidence, methodology, background, comparison, critique)
   - **Prevents superficial "citation padding" and forces intellectual engagement**
   - Expected impact: 100% of citations have meaningful justification

3. **Automatic Metadata Extraction**
   - Extract complete bibliographic data from DOI (authors, title, journal, year, volume, pages)
   - Extract from PMID (PubMed metadata including abstract)
   - Store in CSL-JSON format (Citation Style Language JSON standard)
   - Expected impact: Increase metadata completeness from 60% to >95%

4. **Duplicate Detection**
   - Exact matching: DOI, PMID, URL normalization
   - Fuzzy matching: Title similarity >85%, Author similarity >90%, Year match
   - Automatic merging of duplicates
   - Expected impact: Reduce duplicates from 10% to <1%

5. **Multi-Format Output**
   - In-text citations: `(Smith, 2023) [1]`
   - Formatted bibliography in APA style
   - BibTeX export for LaTeX users
   - **Usage reports showing intellectual reasoning for each citation**
   - Quality metrics reporting

6. **CrewAI Integration**
   - Provide a CrewAI BaseTool that agents can use
   - Operations: add (DOI/PMID/URL with REQUIRED usage context), validate, format, export, usage_report
   - Integrate with existing deep_search crew
   - **Tool enforces usage context requirements**

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

class CitationUsage(BaseModel):
    """Tracks HOW and WHY a citation is used - captures intellectual reasoning"""
    usage_id: str                  # Unique ID for this specific usage
    excerpt: Optional[str]         # Specific text/data/finding used from source
    quote: Optional[str]           # Direct quote if applicable (use excerpt for paraphrase)
    rationale: str                 # WHY this source was used (required)
    contextual_value: str          # HOW it supports your argument (required)
    supporting_claim: str          # The specific claim this citation supports (required)
    page_number: Optional[str]     # Specific page(s) where content found
    section: Optional[str]         # Section of source (e.g., "Methods", "Results")
    usage_type: Literal["evidence", "background", "methodology", "comparison", "critique"]
    timestamp: datetime            # When this usage was recorded

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

    # USAGE TRACKING - captures intellectual reasoning
    usages: List[CitationUsage] = []  # Multiple uses of same source
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

**CRITICAL REQUIREMENT**: Every citation MUST include usage context. Agents must explain WHY they're using each source.

**Operations**:

```json
// Add citation from DOI WITH USAGE CONTEXT (REQUIRED)
{
  "operation": "add",
  "doi": "10.1038/s41586-023-06004-0",
  "rationale": "Provides foundational theory for transformer architecture",
  "contextual_value": "Establishes baseline performance metrics that we compare against",
  "supporting_claim": "Transformer models achieve state-of-art results on NLP tasks",
  "excerpt": "We show that transformers can outperform RNNs on machine translation",
  "page_number": "6",
  "usage_type": "evidence"
}

// Add from PMID WITH USAGE CONTEXT
{
  "operation": "add",
  "pmid": "36854710",
  "rationale": "Meta-analysis provides systematic review of clinical efficacy",
  "contextual_value": "Synthesizes results from 47 RCTs showing treatment effectiveness",
  "supporting_claim": "Drug X reduces mortality by 23% (95% CI 18-28%)",
  "quote": "Treatment with Drug X was associated with significant mortality reduction",
  "page_number": "1243",
  "section": "Results",
  "usage_type": "evidence"
}

// Add from URL WITH USAGE CONTEXT
{
  "operation": "add",
  "url": "https://arxiv.org/abs/2301.12345",
  "rationale": "Recent preprint demonstrates novel approach to problem",
  "contextual_value": "Shows alternative methodology we can adapt",
  "supporting_claim": "Method Y achieves 15% improvement over baseline",
  "usage_type": "methodology"
}

// Add additional usage to existing citation
{
  "operation": "add_usage",
  "citation_id": "smith2023",
  "rationale": "Figure 3 shows scaling behavior relevant to our hypothesis",
  "contextual_value": "Demonstrates that performance scales logarithmically with dataset size",
  "supporting_claim": "Larger datasets yield diminishing returns beyond 100M examples",
  "excerpt": "Performance improvement plateaus at 10^8 training examples",
  "page_number": "12",
  "usage_type": "evidence"
}

// Validate all citations
{"operation": "validate"}

// Format in-text citation with usage context
{
  "operation": "format",
  "citation_ids": ["smith2023"],
  "format_type": "intext",
  "usage_id": "usage-001"  // Specific usage to reference
}

// Generate bibliography
{"operation": "format", "format_type": "bibliography"}

// Get usage report - shows HOW citations are being used
{"operation": "usage_report"}

// Export BibTeX
{"operation": "export", "export_format": "bibtex"}

// List all citations with usage stats
{"operation": "list"}
```

**Tool Response Format**:
```
✓ Citation added successfully with usage context

Citation Details:
- ID: smith2023ml
- Number: [1]
- Validated: ✓ Yes (DOI via Crossref)
- Completeness: 95%

Formatted Reference:
[1] Smith, J. A. & Doe, J. (2023). Machine Learning Approaches. Nature, 5(6), 123-134. https://doi.org/10.1038/s42256-023-00001-x

Usage Context Recorded:
- Rationale: Provides foundational theory for transformer architecture
- Contextual Value: Establishes baseline performance metrics that we compare against
- Supporting Claim: Transformer models achieve state-of-art results on NLP tasks
- Excerpt: "We show that transformers can outperform RNNs on machine translation"
- Page: 6
- Usage Type: evidence

Use in text as: (Smith, 2023) [1]
```

**Usage Report Format**:
```
Citation Usage Analysis
======================

[1] Smith, J. A. & Doe, J. (2023). Machine Learning Approaches.
    Total usages: 3

    Usage 1 (evidence):
    - Claim: Transformer models achieve state-of-art results on NLP tasks
    - Rationale: Provides foundational theory for transformer architecture
    - Context: Establishes baseline performance metrics that we compare against
    - Page: 6

    Usage 2 (evidence):
    - Claim: Larger datasets yield diminishing returns beyond 100M examples
    - Rationale: Figure 3 shows scaling behavior relevant to our hypothesis
    - Context: Demonstrates that performance scales logarithmically with dataset size
    - Page: 12

Quality Metrics:
- 100% of citations have usage context
- Average usages per citation: 2.3
- Usage types: 60% evidence, 20% methodology, 15% background, 5% comparison
- Citations with missing rationale: 0 (0%)
```

## Good vs Bad Citation Usage Examples

### ❌ BAD - Superficial Citation (What we're preventing)
```json
{
  "operation": "add",
  "doi": "10.1038/nature12345"
}
```
**Problem**: No context! Why is this source relevant? What does it prove? This is citation padding.

### ❌ BAD - Minimal Context (Still inadequate)
```json
{
  "operation": "add",
  "doi": "10.1038/nature12345",
  "rationale": "Relevant paper",
  "contextual_value": "Supports our work",
  "supporting_claim": "AI is useful"
}
```
**Problem**: Vague and generic. Doesn't demonstrate actual engagement with the source.

### ✅ GOOD - Rich Context (What we require)
```json
{
  "operation": "add",
  "doi": "10.1038/s41586-021-03819-2",
  "rationale": "This Nature paper by Jumper et al. demonstrates that AlphaFold2 achieves atomic-level accuracy in protein structure prediction, which directly validates our assumption that deep learning can solve complex scientific problems previously requiring experimental methods",
  "contextual_value": "Provides empirical evidence that transformer architectures (which our approach also uses) can achieve breakthrough performance on structured prediction tasks. Their 92.4 GDT score establishes a benchmark we compare against in Section 4.2",
  "supporting_claim": "Deep learning models can achieve near-experimental accuracy on protein structure prediction (median GDT score of 92.4 across CASP14 targets)",
  "excerpt": "AlphaFold produces atomic-level structures across a range of protein types with median GDT score of 92.4",
  "page_number": "583",
  "section": "Results",
  "usage_type": "evidence"
}
```
**Why this is good:**
- **Specific**: Names authors, paper, exact achievement
- **Connected**: Explains how it relates to current work
- **Precise**: Includes exact metrics (92.4 GDT score)
- **Traceable**: Page number and section provided
- **Purposeful**: Clear what claim it supports

### ✅ GOOD - Methodology Citation
```json
{
  "operation": "add",
  "doi": "10.1136/bmj.n71",
  "rationale": "The PRISMA 2020 guidelines provide the gold standard methodology for conducting systematic reviews with transparency and reproducibility. We adapt their 27-item checklist to structure our literature search and study selection process",
  "contextual_value": "Their flow diagram methodology (Figure 1 in the paper) provides a visual framework we implement in our agent workflow to track studies through identification, screening, and inclusion phases. This ensures our AI-driven review matches human systematic review standards",
  "supporting_claim": "Systematic reviews should follow PRISMA 2020's 27-item checklist to ensure methodological rigor and reporting transparency",
  "section": "Methods - Flow diagram",
  "usage_type": "methodology"
}
```
**Why this is good:**
- **Methodological clarity**: Explains what methodology is being adopted
- **Implementation detail**: Specifies which elements (27-item checklist, flow diagram) are used
- **Standard reference**: Positions work within established best practices

## Implementation Steps

### Step 1: Create Core Data Models

File: `citation_tracking/core/citation_model.py`

Implement:
- `CSLName` class with family, given, literal fields
- `CSLDate` class with date_parts
- **`CitationUsage` class** - captures intellectual reasoning (NEW)
  - Fields: usage_id, excerpt, quote, rationale, contextual_value, supporting_claim
  - Fields: page_number, section, usage_type, timestamp
  - Validation: rationale, contextual_value, supporting_claim are REQUIRED
- `CSLCitation` class with all fields listed above
  - Include `usages: List[CitationUsage] = []` field
- `CitationDatabase` class to manage collection of citations
- Helper methods:
  - `get_year()`, `get_first_author_family_name()`, `is_complete()`, `get_completeness_score()`
  - **`add_usage(usage: CitationUsage)`** - adds usage to citation (NEW)
  - **`get_usage_stats()`** - returns usage statistics (NEW)
  - **`has_usage_context()`** - validates citation has proper usage context (NEW)

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
- **Enhanced add methods with REQUIRED usage context**:
  - `add_from_doi(doi, rationale, contextual_value, supporting_claim, excerpt=None, quote=None, page_number=None, section=None, usage_type="evidence")`
  - `add_from_pmid(pmid, rationale, contextual_value, supporting_claim, ...)`
  - `add_from_url(url, rationale, contextual_value, supporting_claim, ...)`
  - All three MUST capture usage context on first add
- **`add_usage_to_citation(citation_id, rationale, contextual_value, supporting_claim, ...)`** - add another usage to existing citation
- `validate_all()` returns validation report
- **`validate_usage_context()`** - ensures all citations have proper usage context (NEW)
- `format_intext(citation_ids, usage_id=None)` returns formatted string
- `format_bibliography_entry(citation_id)` returns formatted reference
- **`generate_usage_report()`** - detailed report showing HOW each citation is used (NEW)
- `export_bibtex()` exports all citations as BibTeX
- **`export_usage_json()`** - export usage metadata for analysis (NEW)
- `get_quality_metrics()` returns validation rates, completeness, usage coverage

### Step 6: Create CrewAI Tool

File: `citation_tracking/tools/citation_tool.py`

Implement:
- `CitationInput` Pydantic model for tool parameters
  - **MUST validate that rationale, contextual_value, supporting_claim are provided**
- `CitationManagerTool` extending CrewAI's `BaseTool`
- `name = "CitationManager"`
- **Enhanced `description` emphasizing REQUIRED usage context** with examples
- `_run(operation, **kwargs)` dispatches to correct method
- **`_add_citation()`** - REQUIRES usage context parameters, calls citation_manager, formats response with usage info
- **`_add_usage()`** - adds another usage to existing citation (NEW)
- `_validate_citations()` returns validation report
- **`_validate_usage_context()`** - validates all citations have usage context (NEW)
- `_format_citation()` returns formatted text
- **`_usage_report()`** - generates detailed usage analysis (NEW)
- `_list_citations()` returns summary with quality metrics including usage stats
- `_export_citations()` returns BibTeX or usage JSON

**Tool description template**:
```python
description = """
CRITICAL: Use this tool for EVERY citation. You MUST provide usage context.

REQUIRED fields for add operation:
- rationale: WHY you're using this source (2-3 sentences)
- contextual_value: HOW it supports your argument (2-3 sentences)
- supporting_claim: The SPECIFIC claim this citation supports (1 sentence)

OPTIONAL but recommended:
- excerpt: Specific finding/data used from source
- quote: Direct quote if applicable
- page_number: Specific page(s)
- section: Section of source (Methods, Results, etc.)
- usage_type: evidence|background|methodology|comparison|critique

... [include operation examples] ...
"""
```

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
  "description": "CRITICAL: Use for EVERY source. MUST provide rationale, contextual_value, and supporting_claim. Validates DOI/PMID, prevents hallucinations."
}
```

Add to writer agent tools:
```json
{
  "id": "urn:sd-core:crewai.builtin.citationManager",
  "name": "CitationManager",
  "description": "Format citations for in-text and bibliography. Generate usage reports."
}
```

Add new citation_specialist agent:
```json
"citation_specialist": {
  "role": "Citation Quality Specialist",
  "goal": "Ensure every citation has intellectual justification, is valid, complete, properly formatted with zero tolerance for hallucinations or superficial citations",
  "backstory": "Expert in bibliographic management, DOI systems, PubMed databases, and research methodology. Demands clear rationale for every citation. Zero tolerance for citation padding or fabricated sources.",
  "llm": "?llmodel",
  "max_iter": 10,
  "verbose": true,
  "memory": true,
  "tools": [
    {
      "id": "urn:sd-core:crewai.builtin.citationManager",
      "name": "CitationManager",
      "description": "Validate citations and analyze usage patterns."
    }
  ],
  "allow_delegation": false
}
```

**CRITICAL: Update researcher task description with mandatory usage context**:
```
9. CRITICAL - USE CITATION TOOL WITH CONTEXT: For EVERY source, you MUST explain WHY and HOW you're using it:

   Example for evidence citation:
   {
     "operation": "add",
     "doi": "10.1038/s41586-023-06004-0",
     "rationale": "This Nature paper establishes the foundational theory for transformer architectures that our analysis builds upon",
     "contextual_value": "Provides the baseline performance metrics (BLEU score of 28.4 on WMT2014) that we compare our approach against in Section 3.2",
     "supporting_claim": "Transformer models achieve state-of-the-art results on machine translation tasks",
     "excerpt": "Our model achieves a BLEU score of 28.4 on WMT2014 En-De, outperforming all previously published models",
     "page_number": "6",
     "usage_type": "evidence"
   }

   Example for methodology citation:
   {
     "operation": "add",
     "pmid": "36854710",
     "rationale": "This meta-analysis demonstrates the systematic review methodology we adapt for AI literature",
     "contextual_value": "Their PRISMA-compliant approach to study selection provides a validated framework for our screening process",
     "supporting_claim": "Systematic reviews should follow PRISMA 2020 guidelines for transparency",
     "section": "Methods",
     "usage_type": "methodology"
   }

10. REQUIRED FIELDS (tool will reject without these):
    - rationale: WHY this source is being used (2-3 sentences explaining relevance)
    - contextual_value: HOW it supports your argument (2-3 sentences on contribution)
    - supporting_claim: WHAT specific claim this citation supports (1 clear sentence)

11. NEVER manually create citations - always use tool
12. If validation fails, source doesn't exist - find different source
13. After adding all sources: {"operation": "validate"}
14. Before finalizing: {"operation": "usage_report"} to verify proper citation usage
```

**Add to citation_specialist task**:
```json
{
  "description": "Review all citations added by researcher and writer. For each citation:\n\n1. Validate it exists via DOI/PMID\n2. Verify usage context is meaningful:\n   - Rationale clearly explains WHY source is used\n   - Contextual value describes HOW it supports argument\n   - Supporting claim is specific and verifiable\n   - Excerpt/quote accurately represents source (if provided)\n3. Check for superficial citations (citation padding)\n4. Ensure no duplicate citations\n5. Verify citation density is appropriate (not too few, not too many)\n6. Generate usage report: {\"operation\": \"usage_report\"}\n7. Flag any citations that lack proper intellectual justification\n\nACCEPT only if:\n- 100% of citations validated against DOIs/PMIDs\n- 100% have meaningful usage context\n- No citation padding detected\n- Proper balance of citation types (evidence, methodology, background)\n\nREJECT if any citations are superficial, unvalidated, or lack clear rationale.",
  "expected_output": "Citation quality report with validation status, usage analysis, and recommendations"
}
```

### Step 8: Create __init__.py Files

Create proper Python package structure with appropriate imports in each `__init__.py`.

### Step 9: Testing

**A. Test Basic Functionality:**
```python
from citation_tracking import CitationManager

manager = CitationManager(job_id="test-123")

# This should FAIL (no usage context)
try:
    citation = manager.add_from_doi("10.1038/s41586-023-06004-0")
    print("❌ FAIL: Should have rejected citation without context")
except ValueError as e:
    print(f"✓ PASS: Correctly rejected - {e}")

# This should SUCCEED
citation = manager.add_from_doi(
    doi="10.1038/s41586-023-06004-0",
    rationale="This landmark paper establishes the theoretical foundation for our approach",
    contextual_value="Demonstrates that the method achieves state-of-art results, providing benchmark we compare against",
    supporting_claim="Method X achieves 95% accuracy on benchmark Y"
)
print(f"✓ Added: {citation.title}")
print(f"✓ Validated: {citation.validated}")
print(f"✓ Usage context: {len(citation.usages)} usages recorded")
```

**B. Test Usage Context Validation:**
```python
# This should FAIL (context too short/generic)
try:
    citation = manager.add_from_doi(
        doi="10.1038/nature12345",
        rationale="Good paper",  # Too short
        contextual_value="Relevant",  # Too short
        supporting_claim="AI works"  # Too vague
    )
    print("❌ FAIL: Should have rejected weak context")
except ValueError as e:
    print(f"✓ PASS: Correctly rejected weak context - {e}")
```

**C. Test Usage Report:**
```python
# Add multiple citations with context
manager.add_from_doi(...)
manager.add_from_pmid(...)

# Generate usage report
report = manager.generate_usage_report()
print(report)

# Should show:
# - All citations with their usage context
# - Statistics on usage types
# - Coverage metrics
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
8. **Usage Context Validation** (CRITICAL):
   - Rationale must be >50 characters (forces thoughtful explanation)
   - Contextual_value must be >50 characters (forces meaningful analysis)
   - Supporting_claim must be >20 characters (forces specificity)
   - Reject citations with generic phrases like "relevant paper", "useful source"
   - Consider implementing a quality score based on length, specificity, and keyword richness
9. **UUID Generation**: Use `uuid.uuid4()` for usage_id generation
10. **Timestamp Tracking**: Use `datetime.now(timezone.utc)` for usage timestamps

## Expected Outcomes

After implementation:
- Citation hallucination rate: 15% → <0.5% (**-97%**)
- **Usage context coverage: 0% → 100% (+100%)** - every citation has intellectual justification
- **Superficial citations: ~40% → 0%** - eliminates citation padding
- Metadata completeness: 60% → >95% (**+58%**)
- Duplicate citations: 10% → <1% (**-90%**)
- Format consistency: 70% → 100% (**+43%**)
- **Research quality: Agents demonstrate clear understanding of sources and their relevance**

## Success Criteria

✅ All citation_tracking Python files created without syntax errors
✅ DOI validation works against Crossref API
✅ PMID validation works against PubMed API
✅ Duplicate detection catches identical papers
✅ **CitationUsage model captures rationale, contextual_value, supporting_claim**
✅ **Tool REJECTS citations without usage context**
✅ **Usage report generation works and shows meaningful analysis**
✅ CrewAI tool provides all operations (add, add_usage, validate, format, export, usage_report)
✅ Integration with service.py, service_types.py, deep_search.json complete
✅ Python imports work: `from citation_tracking import CitationManager, CitationUsage`
✅ No hallucinated citations accepted
✅ **No superficial citations without proper justification accepted**
✅ BibTeX export produces valid output
✅ Usage JSON export captures all intellectual reasoning

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
