# Prompt for Replicating Citation Tracking System to Another Branch

Copy-paste this entire prompt into a new Claude Code session:

---

## Context

I need you to replicate a citation tracking system that was implemented on a different branch. This system eliminates citation hallucinations by validating all DOI/PMID citations against authoritative APIs before acceptance.

## Branch Information

**Source branch (where implementation exists)**: `claude/session-011CUZEYteFK5XKXHKre7kK4`
**Target branch (where I want to apply it)**: [TELL CLAUDE YOUR BRANCH NAME]

**Key commits to replicate**:
- Commit `74b5000`: Documentation (DEEP_RESEARCH_ANALYSIS.md, CITATION_TRACKING_SPEC.md)
- Commit `1d5657a`: Implementation (citation_tracking/ directory, integration)

## What Was Built

A comprehensive citation tracking system with:
- **Zero-hallucination prevention**: DOI/PMID validation via Crossref/PubMed APIs
- **Automatic metadata extraction**: Complete bibliographic data from identifiers
- **Duplicate detection**: Fuzzy + exact matching prevents duplicate citations
- **Multi-format export**: BibTeX, formatted bibliography
- **CSL-JSON data models**: Proper citation data structures
- **CrewAI tool interface**: Agents can use citation manager directly

## Task Instructions

Please perform the following steps:

### Step 1: Examine Current Branch Structure

First, help me understand the current state:

```bash
# Check current branch
git branch

# Check if there are uncommitted changes
git status

# List key files that might conflict
ls -la service.py service_types.py crews/deep_search.json 2>/dev/null || echo "Files may not exist yet"
```

### Step 2: Fetch and Examine Source Branch

```bash
# Fetch all branches
git fetch origin

# Show what exists on source branch
git ls-tree -r --name-only origin/claude/session-011CUZEYteFK5XKXHKre7kK4 | grep -E "(citation_tracking|deep_search\.json|service\.py|service_types\.py|docs/.*CITATION.*|docs/.*ANALYSIS.*)"
```

### Step 3: Create Citation Tracking System Files

Create the entire `citation_tracking/` directory structure with these files:

**File 1: `citation_tracking/__init__.py`**
```python
"""Citation tracking system for IVCAP CrewAI service."""

from citation_tracking.core.citation_manager import CitationManager
from citation_tracking.tools.citation_tool import CitationManagerTool

__all__ = ['CitationManager', 'CitationManagerTool']
```

**File 2: `citation_tracking/core/__init__.py`**
```python
"""Core citation tracking components."""

from citation_tracking.core.citation_model import CSLCitation, CSLName, CSLDate, CitationDatabase
from citation_tracking.core.citation_manager import CitationManager

__all__ = ['CSLCitation', 'CSLName', 'CSLDate', 'CitationDatabase', 'CitationManager']
```

**File 3: `citation_tracking/validation/__init__.py`**
```python
"""Citation validation components."""

from citation_tracking.validation.doi_validator import DOIValidator
from citation_tracking.validation.pmid_validator import PMIDValidator
from citation_tracking.validation.duplicate_detector import DuplicateDetector

__all__ = ['DOIValidator', 'PMIDValidator', 'DuplicateDetector']
```

**File 4: `citation_tracking/tools/__init__.py`**
```python
"""CrewAI tools for citation management."""

from citation_tracking.tools.citation_tool import CitationManagerTool

__all__ = ['CitationManagerTool']
```

**File 5: `citation_tracking/utils/__init__.py`**
```python
"""Utility functions for citation tracking."""

__all__ = []
```

**File 6-10: Main Implementation Files**

For the main implementation files (citation_model.py, citation_manager.py, doi_validator.py, pmid_validator.py, duplicate_detector.py, citation_tool.py), please extract them from the source branch:

```bash
# Extract the implementation files
git show origin/claude/session-011CUZEYteFK5XKXHKre7kK4:citation_tracking/core/citation_model.py > citation_tracking/core/citation_model.py

git show origin/claude/session-011CUZEYteFK5XKXHKre7kK4:citation_tracking/core/citation_manager.py > citation_tracking/core/citation_manager.py

git show origin/claude/session-011CUZEYteFK5XKXHKre7kK4:citation_tracking/validation/doi_validator.py > citation_tracking/validation/doi_validator.py

git show origin/claude/session-011CUZEYteFK5XKXHKre7kK4:citation_tracking/validation/pmid_validator.py > citation_tracking/validation/pmid_validator.py

git show origin/claude/session-011CUZEYteFK5XKXHKre7kK4:citation_tracking/validation/duplicate_detector.py > citation_tracking/validation/duplicate_detector.py

git show origin/claude/session-011CUZEYteFK5XKXHKre7kK4:citation_tracking/tools/citation_tool.py > citation_tracking/tools/citation_tool.py
```

### Step 4: Extract Documentation

```bash
# Extract documentation
git show origin/claude/session-011CUZEYteFK5XKXHKre7kK4:docs/DEEP_RESEARCH_ANALYSIS.md > docs/DEEP_RESEARCH_ANALYSIS.md

git show origin/claude/session-011CUZEYteFK5XKXHKre7kK4:docs/CITATION_TRACKING_SPEC.md > docs/CITATION_TRACKING_SPEC.md
```

### Step 5: Integration Changes

Now apply these integration changes:

**A. Modify `service.py`**

Add these imports at the top (after existing imports):
```python
from citation_tracking import CitationManager, CitationManagerTool
```

Find the `add_supported_tools` call and add this entry:
```python
"urn:sd-core:crewai.builtin.citationManager": lambda _, ctxt: CitationManagerTool(citation_manager=CitationManager(job_id=ctxt.job_id)),
```

**B. Modify `service_types.py`**

Add import after other imports:
```python
from citation_tracking import CitationManager, CitationManagerTool
```

Update the `Context` dataclass to include `job_id`:
```python
@dataclass
class Context():
    job_id: str
    vectordb_config: dict
    tmp_dir: str = "/tmp"
```

Update the `as_crew` method in `CrewA` class:
```python
def as_crew(self, llm: LLM, job_id: str, **kwargs) -> Crew:
    ctxt = Context(job_id=job_id, vectordb_config=create_vectordb_config(job_id))
    # ... rest of method
```

**C. Modify `crews/deep_search.json`**

Add CitationManager tool to researcher agent's tools array:
```json
{
  "id": "urn:sd-core:crewai.builtin.citationManager",
  "name": "CitationManager",
  "description": "CRITICAL: Use this tool for EVERY source you find. Validates DOI/PMID, extracts metadata automatically, prevents hallucinations."
}
```

Add CitationManager tool to writer agent's tools array:
```json
{
  "id": "urn:sd-core:crewai.builtin.citationManager",
  "name": "CitationManager",
  "description": "Citation management for formatting in-text citations and bibliography."
}
```

Add new citation_specialist agent (after writer agent):
```json
"citation_specialist": {
  "role": "Citation Quality Specialist",
  "goal": "Ensure every citation is valid, complete, and properly formatted with zero tolerance for hallucinated sources",
  "backstory": "Expert in bibliographic management with deep knowledge of DOI systems, PubMed databases, academic citation standards. Zero tolerance for fabricated sources.",
  "llm": "?llmodel",
  "max_iter": 10,
  "verbose": true,
  "memory": true,
  "tools": [
    {
      "id": "urn:sd-core:crewai.builtin.citationManager",
      "name": "CitationManager",
      "description": "CRITICAL tool for validating, managing, and formatting all citations."
    }
  ],
  "allow_delegation": false
}
```

Update researcher task description (around step 9-12):
Replace the citation recording instructions with:
```
9. CRITICAL - USE CITATION TOOL: For EVERY source you find, immediately add it using the CitationManager tool:
   - If source has DOI: {"operation": "add", "doi": "10.xxxx/xxxxx"}
   - If source has PMID: {"operation": "add", "pmid": "12345678"}
   - If source is a URL: {"operation": "add", "url": "https://..."}
   The tool will automatically validate, extract metadata, assign citation numbers.
10. NEVER manually create citations - always use the CitationManager tool
11. If tool reports "validation failed", the source doesn't exist - find a different source
12. After adding all sources, validate them: {"operation": "validate"}
```

### Step 6: Handle Conflicts

**IMPORTANT**: If any files already exist and have different content:

1. **Read the existing file first** to understand current structure
2. **Merge intelligently** - don't just overwrite
3. **Preserve existing functionality** while adding citation tracking
4. **Ask me if unsure** about how to merge conflicts

### Step 7: Commit and Test

After all changes:

```bash
# Stage all changes
git add citation_tracking/ docs/DEEP_RESEARCH_ANALYSIS.md docs/CITATION_TRACKING_SPEC.md service.py service_types.py crews/deep_search.json

# Show what will be committed
git status

# Commit with detailed message
git commit -m "Implement citation tracking system with zero-hallucination validation

Added comprehensive citation tracking system that validates all citations
against authoritative APIs (Crossref, PubMed) to prevent hallucinations.

Key features:
- DOI/PMID validation before acceptance
- Automatic metadata extraction
- Duplicate detection (fuzzy + exact matching)
- Multi-format export (BibTeX, bibliography)
- CSL-JSON data models
- CrewAI tool interface

Expected impact:
- Citation hallucination: 15% → <0.5% (-97%)
- Metadata completeness: 60% → >95% (+58%)
- Duplicate citations: 10% → <1% (-90%)

Based on implementation from claude/session-011CUZEYteFK5XKXHKre7kK4

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to branch
git push origin [YOUR-BRANCH-NAME]
```

### Step 8: Verify Implementation

Please verify the implementation works:

1. Check all files were created:
```bash
find citation_tracking -type f | sort
```

2. Check imports work (Python):
```bash
python3 -c "from citation_tracking import CitationManager, CitationManagerTool; print('✓ Imports work')"
```

3. Verify integration:
```bash
grep -n "citationManager" service.py service_types.py crews/deep_search.json
```

## Expected File Structure

After completion, you should have:

```
citation_tracking/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── citation_model.py      (400+ lines)
│   └── citation_manager.py    (400+ lines)
├── validation/
│   ├── __init__.py
│   ├── doi_validator.py       (250+ lines)
│   ├── pmid_validator.py      (300+ lines)
│   └── duplicate_detector.py  (250+ lines)
├── tools/
│   ├── __init__.py
│   └── citation_tool.py       (400+ lines)
└── utils/
    └── __init__.py

docs/
├── DEEP_RESEARCH_ANALYSIS.md  (900+ lines)
└── CITATION_TRACKING_SPEC.md  (800+ lines)

Modified files:
├── service.py                  (+ citation imports & tool registration)
├── service_types.py            (+ citation imports, job_id to Context)
└── crews/deep_search.json      (+ citation_specialist agent, + tools)
```

## Troubleshooting

**If you encounter errors:**

1. **Import errors**: Check Python path, ensure __init__.py files exist
2. **Merge conflicts**: Read both versions, ask me how to merge
3. **Missing files**: Re-extract from source branch using git show
4. **Syntax errors**: Validate JSON with `python3 -m json.tool crews/deep_search.json`

## Additional Context

**Agent Usage Examples:**
```json
// Add citation
{"operation": "add", "doi": "10.1038/s41586-023-06004-0"}

// Validate all
{"operation": "validate"}

// Format in-text
{"operation": "format", "citation_ids": ["smith2023"], "format_type": "intext"}

// Export BibTeX
{"operation": "export", "export_format": "bibtex"}
```

**Key Classes:**
- `CSLCitation`: Pydantic model for citations (CSL-JSON format)
- `CitationManager`: Main API for managing citations
- `DOIValidator`: Validates DOIs via Crossref API
- `PMIDValidator`: Validates PMIDs via PubMed API
- `DuplicateDetector`: Finds duplicate citations
- `CitationManagerTool`: CrewAI tool interface

## Success Criteria

The implementation is successful when:
- ✅ All citation_tracking files created without errors
- ✅ Documentation files extracted successfully
- ✅ service.py, service_types.py, deep_search.json modified correctly
- ✅ No Python import errors
- ✅ Git commit created with all changes
- ✅ Changes pushed to target branch
- ✅ citation_specialist agent added to crew
- ✅ CitationManager tool available to researcher and writer agents

---

## My Specific Requirements

**Target Branch**: [FILL IN YOUR BRANCH NAME]

**Known Conflicts**: [TELL CLAUDE ABOUT ANY FILES YOU KNOW ARE DIFFERENT]

**Special Instructions**: [ANY ADDITIONAL CONTEXT ABOUT YOUR BRANCH]

---

Please proceed with the replication. Ask me questions if you need clarification on any conflicts or decisions.
