# IVCAP CrewAI Service Tests

This directory contains test files and utilities for the IVCAP CrewAI Service.

## Test Categories

### Integration Tests
Python-based integration tests for service features:

- **test_knowledge_integration.py** - Tests for knowledge sources (`additional-inputs`) feature
- **test_knowledge_processor.py** - Unit tests for knowledge processor module
- **test_knowledge_simple.py** - Simple smoke tests for knowledge sources
- **runembedding_test.py** - Tests for embedding functionality

### Crew Test Requests

JSON test request files for specific crews:

- **software_discovery_aspect_test.json** - ML training infrastructure discovery test
- **software_discovery_data_analysis.json** - Bioinformatics tools discovery test

### Test Utilities

- **create_order.sh** - Helper script to create IVCAP orders from test JSON files

### Test Crews

The `test_crews/` directory contains crew definitions used for testing:

- **context_chain.json** - Test crew for task context chaining

## Running Tests

### Python Integration Tests

```bash
# Run knowledge integration tests
python tests/test_knowledge_integration.py

# Run knowledge processor tests
python tests/test_knowledge_processor.py

# Run simple knowledge tests
python tests/test_knowledge_simple.py
```

### Crew Request Tests

See individual README files for specific crew testing instructions:

- **[Software Discovery Crew](README_SOFTWARE_DISCOVERY.md)** - Complete guide for testing the Software Discovery crew with multiple methods

### Quick Test Commands

```bash
# Test service locally (requires service running on port 8077)
make test-local TEST_REQUEST=tests/software_discovery_aspect_test.json

# Create IVCAP order (requires service deployed to IVCAP)
tests/create_order.sh tests/software_discovery_aspect_test.json

# Test with authentication
make test-local-with-auth TEST_REQUEST=tests/software_discovery_aspect_test.json
```

## Test File Format

All crew test request files follow the v0.2.0 format:

```json
{
  "$schema": "urn:sd-core:schema.crewai.request.1",
  "name": "Test Job Name",
  "crew-ref": "urn:sd:crewai:crew.crew_name",
  "inputs": {
    "placeholder1": "value1",
    "placeholder2": "value2"
  }
}
```

### Key Points

- Use `crew-ref` with **entity URN** (e.g., `urn:sd:crewai:crew.software_discovery`)
- Do NOT use artifact URN in `crew-ref`
- Include `$schema` field for validation
- Provide all required placeholders in `inputs` dictionary

## Creating New Tests

### For New Crews

1. Create a JSON test request file: `tests/{crew_name}_test.json`
2. Use the v0.2.0 format with proper entity URN
3. Document expected behavior and results
4. Consider creating a dedicated README if the crew has multiple test scenarios

### For Integration Tests

1. Create a Python test file: `tests/test_{feature_name}.py`
2. Use pytest framework
3. Include docstrings explaining what's being tested
4. Add to this README's integration tests section

## Helper Scripts

### create_order.sh

Simplifies IVCAP order creation from test JSON files.

**Usage**:
```bash
tests/create_order.sh tests/software_discovery_aspect_test.json
```

**Features**:
- Automatic token and URL retrieval
- JSON validation
- Proper order payload formatting
- Returns job ID and monitoring commands

**Requirements**:
- ivcap CLI installed and configured
- jq installed
- Script is executable (`chmod +x tests/create_order.sh`)

## Test Data

Test crews and configurations are stored in:

- `test_crews/` - Crew definitions for testing
- Individual JSON files - Request payloads for specific test scenarios

## Troubleshooting

### "cannot find crew definition"

The crew must be uploaded to IVCAP as an aspect. Verify with:
```bash
ivcap aspect query -s "urn:sd:schema:icrew-crew.1" --entity "urn:sd:crewai:crew.{crew_name}" -o json
```

### "Invalid schema identifier"

Ensure your test file includes:
```json
{
  "$schema": "urn:sd-core:schema.crewai.request.1",
  ...
}
```

### Service not responding

Check if the service is running:
```bash
# Should show service listening on port 8077
curl http://localhost:8077/health
```

Start service if needed:
```bash
poetry ivcap run
```

## Additional Documentation

- [Software Discovery Testing Guide](README_SOFTWARE_DISCOVERY.md) - Comprehensive testing guide for Software Discovery crew
- [Service README](../README.md) - Main service documentation
- [CHANGELOG](../CHANGELOG.md) - Version history and migration guide
- [Testing Guide](../TESTING.md) - General testing guide for the service
- [Architecture Guide](../docs_context/CLAUDE.md) - Service architecture and implementation details

## Environment Setup

Ensure your `.env` file contains:

```bash
# Required
IVCAP_BASE_URL=http://ivcap.local
LITELLM_PROXY_URL=http://localhost:8000

# For web search tools
SERPER_API_KEY=your_api_key

# Model configuration
LITELLM_DEFAULT_MODEL=gpt-4o
```

## Contributing

When adding new tests:

1. Follow the v0.2.0 request format
2. Document expected behavior
3. Include validation criteria
4. Add to this README
5. Consider creating a dedicated README for complex test scenarios

