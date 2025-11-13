# Testing Software Discovery Crew

## Overview

The Software Discovery crew helps researchers find and evaluate software tools for their specific needs across various domains. It performs a three-stage process:
1. **Discovery** - Finds 10-15 potentially relevant tools
2. **Analysis** - Evaluates top 5-10 candidates in detail
3. **Synthesis** - Recommends top 3-5 tools with comparison

## Prerequisites

### Required Software
- **Service Running**: `poetry ivcap run` (for local testing)
- **ivcap CLI**: Installed and configured
- **jq**: JSON processor for command-line
- **curl**: HTTP client

### Required Configuration
- **IVCAP_BASE_URL**: Set in `.env` file (e.g., `http://ivcap.local` or `https://mindweaver.develop.ivcap.io`)
- **SERPER_API_KEY**: Set in `.env` for web search capability
- **LITELLM_PROXY_URL**: LiteLLM proxy URL (optional for local, required for production)

### Crew Upload
The crew must be uploaded to IVCAP as an aspect with entity URN: `urn:sd:crewai:crew.software_discovery`

Verify crew exists:
```bash
ivcap aspect query \
  -s "urn:sd:schema:icrew-crew.1" \
  --entity "urn:sd:crewai:crew.software_discovery" \
  -o json
```

---

## Test Files

### Test 1: ML Training Infrastructure
**File**: `tests/software_discovery_aspect_test.json`

**Use Case**: Finding tools for training large machine learning models

**Inputs**:
- **research_topic**: "Deep Learning Training Infrastructure and MLOps Tools"
- **keywords**: PyTorch, distributed training, GPU clusters, experiment tracking
- **additional_information**: Requirements for multi-node training, 1B+ parameter models

**Expected Output**:
- Discovery of 10-15 relevant tools (PyTorch Lightning, Ray, Horovod, DeepSpeed, etc.)
- Analysis of training frameworks, experiment tracking, and MLOps tools
- Recommendations for top 3-5 with feature comparison

**Execution Time**: ~5-10 minutes (depending on LLM speed and web search)

### Test 2: Bioinformatics Data Analysis
**File**: `tests/software_discovery_data_analysis.json`

**Use Case**: Finding tools for genomics and proteomics data analysis

**Inputs**:
- **research_topic**: "Bioinformatics Data Analysis and Visualization Tools"
- **keywords**: genomics, RNA-seq, variant calling, pipeline automation
- **additional_information**: NGS data analysis, 100GB+ datasets, R/Python integration

**Expected Output**:
- Discovery of bioinformatics tools (Galaxy, Nextflow, Snakemake, Bioconductor, etc.)
- Analysis of workflow engines and visualization platforms
- Recommendations tailored to lab requirements with licensing considerations

**Execution Time**: ~5-10 minutes

---

## Running Tests

### Method 1: Direct Service Test (Local Development)

Test the service directly without creating IVCAP orders. Best for development and debugging.

**Prerequisites**:
- Service running: `poetry ivcap run` in Terminal 1

**Using Makefile** (recommended):
```bash
cd /Users/ran12c/development/ivcapworks/ivcap-crewai-service

# Test ML training use case
make test-local TEST_REQUEST=tests/software_discovery_aspect_test.json

# Test bioinformatics use case
make test-local TEST_REQUEST=tests/software_discovery_data_analysis.json
```

**Using curl directly**:
```bash
# ML training test
curl -X POST \
  -H "Timeout: 360" \
  -H "content-type: application/json" \
  --data @tests/software_discovery_aspect_test.json \
  http://localhost:8077 | jq

# Bioinformatics test
curl -X POST \
  -H "Timeout: 360" \
  -H "content-type: application/json" \
  --data @tests/software_discovery_data_analysis.json \
  http://localhost:8077 | jq
```

**With Authentication** (simulating production):
```bash
TOKEN=$(ivcap context get access-token --refresh-token)

curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Timeout: 360" \
  -H "content-type: application/json" \
  --data @tests/software_discovery_aspect_test.json \
  http://localhost:8077 | jq
```

---

### Method 2: IVCAP Order via Makefile

Create an IVCAP order using existing Makefile targets. Service must be deployed to IVCAP.

**Prerequisites**:
- Service deployed to IVCAP
- ivcap CLI configured
- Authentication token available

**Commands**:
```bash
cd /Users/ran12c/development/ivcapworks/ivcap-crewai-service

# Using poetry ivcap exec-job (streams output)
make test-job-ivcap TEST_REQUEST=tests/software_discovery_aspect_test.json

# Using curl (returns job ID)
make test-job-ivcap-curl TEST_REQUEST=tests/software_discovery_aspect_test.json
```

**Get Service ID**:
```bash
SERVICE_ID=$(poetry ivcap --silent get-service-id)
echo $SERVICE_ID
```

---

### Method 3: IVCAP Order via Helper Script

Use the `create_order.sh` helper script for simplified order creation.

**Prerequisites**:
- ivcap CLI configured
- jq installed
- Script is executable (`chmod +x tests/create_order.sh`)

**Usage**:
```bash
# From repository root
tests/create_order.sh tests/software_discovery_aspect_test.json

# From tests directory
cd tests
./create_order.sh software_discovery_aspect_test.json
./create_order.sh software_discovery_data_analysis.json
```

**What the script does**:
1. Validates test file JSON syntax
2. Gets authentication token automatically
3. Gets IVCAP URL and service ID
4. Wraps request in proper order format
5. Submits to IVCAP API
6. Returns job ID and useful monitoring commands

**Example output**:
```
=== IVCAP Order Creation Helper ===

Test file: tests/software_discovery_aspect_test.json
Getting authentication token...
✓ Token obtained
Getting IVCAP URL...
✓ IVCAP URL: https://mindweaver.develop.ivcap.io
Getting service ID...
✓ Service ID: urn:ivcap:service:01555c28-32d0-5839-b92b-f3e52410d6dd
Reading test file...
✓ Test file parsed successfully
Job name: Software Discovery Test - PyTorch Training Infrastructure

Submitting order to IVCAP...
✓ Order created successfully!

Job ID: urn:ivcap:job:abc123...

=== Useful Commands ===

Check job status:
  curl -H "Authorization: Bearer $(ivcap context get access-token --refresh-token)" \
    "https://mindweaver.develop.ivcap.io/1/services2/.../jobs/..." | jq

Get job results:
  curl -H "Authorization: Bearer $(ivcap context get access-token --refresh-token)" \
    "https://mindweaver.develop.ivcap.io/1/services2/.../jobs/...?with-result-content=true" | jq
```

---

### Method 4: IVCAP Order via Direct curl

Create orders directly via IVCAP API with full control over the request.

**Step 1: Set environment variables**
```bash
TOKEN=$(ivcap context get access-token --refresh-token)
IVCAP_URL=$(ivcap context get url)
SERVICE_ID=$(poetry ivcap --silent get-service-id)

echo "Token: ${TOKEN:0:20}..."
echo "IVCAP URL: $IVCAP_URL"
echo "Service ID: $SERVICE_ID"
```

**Step 2: Create order with embedded request body**
```bash
# Note: Request body must be JSON-stringified and embedded in "body" parameter
curl -i -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Timeout: 360" \
  --data '{
    "service": "'"$SERVICE_ID"'",
    "parameters": [
      {
        "name": "body",
        "value": "{\"$schema\":\"urn:sd-core:schema.crewai.request.1\",\"name\":\"Software Discovery - ML Training Tools\",\"crew-ref\":\"urn:sd:crewai:crew.software_discovery\",\"inputs\":{\"research_topic\":\"Deep Learning Training Infrastructure\",\"keywords\":\"PyTorch, distributed training, GPU clusters, experiment tracking\",\"additional_information\":\"Multi-node training support, open-source tools preferred, budget $10k/year\"}}"
      }
    ]
  }' \
  "$IVCAP_URL/1/services2/$SERVICE_ID/jobs"
```

**Step 3: Using a JSON file (cleaner approach)**

Create `tests/order_wrapper.json`:
```json
{
  "service": "$SERVICE_ID",
  "parameters": [
    {
      "name": "body",
      "value": "$REQUEST_BODY"
    }
  ]
}
```

Then use with substitution:
```bash
REQUEST_BODY=$(cat tests/software_discovery_aspect_test.json | jq -c .)
ORDER_PAYLOAD=$(jq -n \
  --arg service "$SERVICE_ID" \
  --arg body "$REQUEST_BODY" \
  '{
    service: $service,
    parameters: [
      {
        name: "body",
        value: $body
      }
    ]
  }')

curl -i -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Timeout: 360" \
  --data "$ORDER_PAYLOAD" \
  "$IVCAP_URL/1/services2/$SERVICE_ID/jobs"
```

---

## Checking Order Status and Results

After creating an order via Method 2, 3, or 4, use these commands to monitor progress:

### Get Order Status
```bash
TOKEN=$(ivcap context get access-token --refresh-token)
IVCAP_URL=$(ivcap context get url)
SERVICE_ID=$(poetry ivcap --silent get-service-id)
JOB_ID="<job-id-from-order-creation>"

# Basic status
curl -H "Authorization: Bearer $TOKEN" \
  "$IVCAP_URL/1/services2/$SERVICE_ID/jobs/$JOB_ID" | jq
```

### Get Results with Content
```bash
# Get complete results including output artifacts
curl -H "Authorization: Bearer $TOKEN" \
  "$IVCAP_URL/1/services2/$SERVICE_ID/jobs/$JOB_ID?with-result-content=true" | jq

# Extract just the final answer
curl -H "Authorization: Bearer $TOKEN" \
  "$IVCAP_URL/1/services2/$SERVICE_ID/jobs/$JOB_ID?with-result-content=true" | \
  jq -r '.result.answer'
```

### Stream Events (Watch Progress)
```bash
# Stream real-time events from the job
curl --no-buffer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: text/event-stream" \
  "$IVCAP_URL/1/services2/$SERVICE_ID/jobs/$JOB_ID/events"
```

### List All Jobs
```bash
# List recent jobs for this service
curl -H "Authorization: Bearer $TOKEN" \
  "$IVCAP_URL/1/services2/$SERVICE_ID/jobs" | jq

# Filter by status
curl -H "Authorization: Bearer $TOKEN" \
  "$IVCAP_URL/1/services2/$SERVICE_ID/jobs" | \
  jq '.items[] | select(.status == "completed") | {id, name, status}'
```

### Using Makefile Commands
```bash
# Get results (requires JOB_ID variable)
make test-get-result JOB_ID=urn:ivcap:job:abc123...

# Get events
make test-get-events JOB_ID=urn:ivcap:job:abc123...

# List all results
make list-results-ivcap
```

---

## Understanding the Request Format

### crew-ref Field

The `crew-ref` field must contain the **entity URN**, not the artifact URN:

✅ **Correct**: `"crew-ref": "urn:sd:crewai:crew.software_discovery"`

❌ **Wrong**: `"crew-ref": "urn:ivcap:artifact:abc123..."`

**Why?** The service queries IVCAP aspects using the entity URN:
```
GET /1/aspects?schema=urn:sd:schema:icrew-crew.1&entity=urn:sd:crewai:crew.software_discovery&include-content=true
```

The aspect contains the crew definition in its `content` field, which the service downloads and parses.

### Placeholders

The Software Discovery crew expects three placeholders to be provided in the `inputs` dictionary:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `research_topic` | The domain/field you're researching | "Deep Learning Training Infrastructure" |
| `keywords` | Specific capabilities or features needed | "PyTorch, distributed training, GPU clusters" |
| `additional_information` | Context about requirements, constraints, budget, team | "Multi-node training, 1B+ parameters, $10k budget, 5-person team" |

**All three placeholders should be populated** for best results. Leave empty string `""` if truly not applicable.

### Request Schema

All requests must include the v0.2.0 schema identifier:
```json
{
  "$schema": "urn:sd-core:schema.crewai.request.1",
  "name": "Human-readable job name",
  "crew-ref": "urn:sd:crewai:crew.software_discovery",
  "inputs": {
    "research_topic": "...",
    "keywords": "...",
    "additional_information": "..."
  }
}
```

---

## Expected Results

### Task Outputs (Local Execution)

When running locally, results are saved to `runs/{job_id}/outputs/`:

```
runs/abc123.../outputs/
├── 01_Discovery_Task.md           # List of 10-15 discovered tools
├── 02_Analysis_Task.md             # Detailed analysis of top candidates
├── 03_Synthesis_Task.md            # Final recommendations with comparison
└── final_output.md                 # Complete consolidated report
```

### Response Structure

The service returns a JSON response:

```json
{
  "$schema": "urn:sd-core:schema.crewai.response.1",
  "answer": "# Software Recommendations Report\n\n## Executive Summary\n...",
  "crew_name": "Software Discovery",
  "place_holders": ["research_topic", "keywords", "additional_information"],
  "task_responses": [
    {
      "agent": "discovery_agent",
      "description": "Discover software tools...",
      "summary": "Discovered 15 tools...",
      "raw": "# Software Discovery Report\n\n..."
    },
    {
      "agent": "analysis_agent",
      "description": "Analyze top candidates...",
      "summary": "Analyzed 8 tools...",
      "raw": "# Analysis Report\n\n..."
    },
    {
      "agent": "synthesis_agent",
      "description": "Synthesize recommendations...",
      "summary": "Recommend top 5 tools...",
      "raw": "# Recommendations Report\n\n..."
    }
  ],
  "created_at": "2025-01-13T10:30:00Z",
  "process_time_sec": 45.2,
  "run_time_sec": 287.5,
  "token_usage": {
    "total_tokens": 12453,
    "prompt_tokens": 8234,
    "completion_tokens": 4219
  }
}
```

### Expected Content

**Discovery Phase** should find:
- 10-15 tools matching the search criteria
- Mix of established and emerging tools
- Various categories (frameworks, platforms, libraries)
- URLs and basic descriptions for each

**Analysis Phase** should provide:
- Detailed feature comparison of top 5-10 tools
- Licensing information
- Community/support assessment
- Integration capabilities
- Scalability and performance notes
- Learning curve assessment

**Synthesis Phase** should deliver:
- Top 3-5 final recommendations
- Clear ranking with rationale
- Use case matching
- Comparison table
- Implementation recommendations
- Cost/benefit analysis

---

## Troubleshooting

### Error: "cannot find crew definition"

**Cause**: Entity URN not found in IVCAP

**Solution**: Verify crew is uploaded with correct entity URN:
```bash
ivcap aspect query \
  -s "urn:sd:schema:icrew-crew.1" \
  --entity "urn:sd:crewai:crew.software_discovery" \
  -o json
```

If not found, the crew needs to be uploaded to IVCAP.

### Error: "Invalid schema identifier"

**Cause**: Missing or incorrect `$schema` field

**Solution**: Ensure request has:
```json
{
  "$schema": "urn:sd-core:schema.crewai.request.1",
  ...
}
```

### Error: "Placeholders not replaced"

**Cause**: Input key names don't match crew's placeholder definitions

**Solution**: Use exact placeholder names as defined in crew:
- `research_topic` (not `topic`, `research`, or `research_question`)
- `keywords` (not `keyword`, `search_terms`, or `tags`)
- `additional_information` (not `additional_info`, `context`, or `notes`)

### Error: "Connection refused" (localhost:8077)

**Cause**: Service not running locally

**Solution**: Start the service:
```bash
poetry ivcap run
```

### Error: "401 Unauthorized" (IVCAP API)

**Cause**: Invalid or expired authentication token

**Solution**: Refresh token:
```bash
ivcap context get access-token --refresh-token
```

### Error: "SERPER_API_KEY not found"

**Cause**: Web search tool requires Serper API key

**Solution**: Add to `.env` file:
```bash
SERPER_API_KEY=your_api_key_here
```

Get key from: https://serper.dev/

### Service returns incomplete results

**Cause**: Timeout or insufficient iterations for agents

**Solution**: Check agent `max_iter` settings in crew definition. Discovery and Analysis agents should have 10-15 iterations.

### Tools discovered are off-topic

**Cause**: Keywords too generic or additional_information missing context

**Solution**: Provide more specific keywords and detailed requirements in `additional_information`.

---

## Frontend Integration Note

⚠️ **Important Migration Required**

The frontend currently uses the **v0.1.x format** which is **NO LONGER SUPPORTED** by the v0.2.0 backend.

**Current frontend (v0.1.x) - BROKEN**:
```typescript
const parameters = [
  { name: 'crew', value: crewAspect.content.artifact },  // ❌ Sends artifact URN
  { name: 'p1', value: `keywords:...` },                 // ❌ Old format
  { name: 'p2', value: `research_topic:...` },           // ❌ Old format
  { name: 'p3', value: `additional_information:...` },   // ❌ Old format
];
```

**Required frontend (v0.2.0) - CORRECT**:
```typescript
const requestBody = {
  "$schema": "urn:sd-core:schema.crewai.request.1",
  "name": `${selectedCrew.content.name} - ${prompt.substring(0, 20)}`,
  "crew-ref": selectedCrew.entity_id,  // ✅ Use entity URN
  "inputs": {
    "research_topic": prompt,
    "keywords": keywords,
    "additional_information": inputContent
  }
};

const parameters = [
  {
    name: "body",
    value: JSON.stringify(requestBody)
  }
];
```

**Key changes**:
1. Use `entity_id` (not `artifact`)
2. No colon-prefix format
3. Wrap entire request in "body" parameter
4. Include `$schema` field

See [CHANGELOG.md](../CHANGELOG.md) for complete migration guide.

---

## Performance Notes

### Typical Execution Times
- **Discovery Task**: 2-3 minutes (web searches and content extraction)
- **Analysis Task**: 2-4 minutes (detailed evaluation of candidates)
- **Synthesis Task**: 1-2 minutes (recommendation generation)
- **Total**: ~5-10 minutes for complete execution

### Token Usage
- **Typical range**: 10,000-20,000 tokens per complete execution
- **Cost estimate**: $0.50-$2.00 depending on model (GPT-4o vs GPT-4o-mini)

### Optimization Tips
1. Use more specific keywords to reduce search space
2. Provide detailed `additional_information` to guide discovery
3. Use `gpt-4o-mini` for faster/cheaper execution during testing
4. Consider setting `max_iter` lower for initial test runs

---

## Additional Resources

- **Service Documentation**: [README.md](../README.md)
- **Architecture Guide**: [CLAUDE.md](../docs_context/CLAUDE.md)
- **Testing Guide**: [TESTING.md](../TESTING.md)
- **Migration Guide**: [CHANGELOG.md](../CHANGELOG.md)
- **Example Crews**: [crews/](../crews/)
- **Makefile Targets**: [Makefile](../Makefile)

---

## Quick Reference

### Common Commands

```bash
# Start service locally
poetry ivcap run

# Test locally
make test-local TEST_REQUEST=tests/software_discovery_aspect_test.json

# Create IVCAP order
tests/create_order.sh tests/software_discovery_aspect_test.json

# Check order status
curl -H "Authorization: Bearer $(ivcap context get access-token --refresh-token)" \
  "$(ivcap context get url)/1/services2/$(poetry ivcap --silent get-service-id)/jobs/$JOB_ID" | jq

# Get results
make test-get-result JOB_ID=your-job-id
```

### Environment Variables

```bash
# .env file
IVCAP_BASE_URL=http://ivcap.local
SERPER_API_KEY=your_serper_key
LITELLM_PROXY_URL=http://localhost:8000
LITELLM_DEFAULT_MODEL=gpt-4o
```

### File Locations

- Test files: `tests/software_discovery_*.json`
- Helper script: `tests/create_order.sh`
- Results: `runs/{job_id}/outputs/`
- Service: `service.py`
- Crew definition: Retrieved from IVCAP aspect

