#!/bin/bash
# Helper script to create IVCAP orders from test request files
# Usage: ./create_order.sh <test_request_file.json>
# Example: ./create_order.sh tests/software_discovery_aspect_test.json

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is not installed. Please install jq to use this script.${NC}"
    echo "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
    exit 1
fi

# Check if ivcap CLI is installed
if ! command -v ivcap &> /dev/null; then
    echo -e "${RED}Error: ivcap CLI is not installed.${NC}"
    echo "Install from: https://github.com/ivcap-works/ivcap-cli"
    exit 1
fi

# Check arguments
if [ $# -lt 1 ]; then
    echo -e "${YELLOW}Usage: $0 <test_request_file.json>${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 tests/software_discovery_aspect_test.json"
    echo "  $0 tests/software_discovery_data_analysis.json"
    echo ""
    echo "Available test files:"
    ls -1 tests/*.json 2>/dev/null | grep -v "create_order" || echo "  (no test files found in tests/)"
    exit 1
fi

TEST_FILE=$1

# Check if test file exists
if [ ! -f "$TEST_FILE" ]; then
    echo -e "${RED}Error: Test file not found: $TEST_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}=== IVCAP Order Creation Helper ===${NC}"
echo ""
echo -e "${BLUE}Test file:${NC} $TEST_FILE"

# Get authentication token
echo -e "${BLUE}Getting authentication token...${NC}"
TOKEN=$(ivcap context get access-token --refresh-token 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to get authentication token${NC}"
    echo "$TOKEN"
    exit 1
fi
echo -e "${GREEN}✓ Token obtained${NC}"

# Get IVCAP URL
echo -e "${BLUE}Getting IVCAP URL...${NC}"
IVCAP_URL=$(ivcap context get url 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to get IVCAP URL${NC}"
    echo "$IVCAP_URL"
    exit 1
fi
echo -e "${GREEN}✓ IVCAP URL: $IVCAP_URL${NC}"

# Get service ID
echo -e "${BLUE}Getting service ID...${NC}"
# Change to parent directory if we're in tests/
if [[ $(basename $(pwd)) == "tests" ]]; then
    cd ..
fi
SERVICE_ID=$(poetry ivcap --silent get-service-id 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to get service ID${NC}"
    echo "$SERVICE_ID"
    echo -e "${YELLOW}Make sure you're in the service directory and poetry is configured${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Service ID: $SERVICE_ID${NC}"

# Read and validate test file
echo -e "${BLUE}Reading test file...${NC}"
if ! REQUEST_BODY=$(cat "$TEST_FILE" | jq -c . 2>&1); then
    echo -e "${RED}Error: Invalid JSON in test file${NC}"
    echo "$REQUEST_BODY"
    exit 1
fi
echo -e "${GREEN}✓ Test file parsed successfully${NC}"

# Extract job name for display
JOB_NAME=$(echo "$REQUEST_BODY" | jq -r '.name // "Unnamed Job"')
echo -e "${BLUE}Job name:${NC} $JOB_NAME"

# Create the order payload
echo -e "${BLUE}Creating order payload...${NC}"
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

# Submit the order
echo ""
echo -e "${BLUE}Submitting order to IVCAP...${NC}"
echo -e "${BLUE}Endpoint:${NC} $IVCAP_URL/1/services2/$SERVICE_ID/jobs"
echo ""

RESPONSE=$(curl -s -i -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Timeout: 360" \
  --data "$ORDER_PAYLOAD" \
  "$IVCAP_URL/1/services2/$SERVICE_ID/jobs")

# Check HTTP status
HTTP_STATUS=$(echo "$RESPONSE" | grep -i "HTTP" | head -1 | awk '{print $2}')

if [ "$HTTP_STATUS" == "200" ] || [ "$HTTP_STATUS" == "201" ]; then
    echo -e "${GREEN}✓ Order created successfully!${NC}"
    echo ""
    
    # Extract JSON body (after headers)
    JSON_BODY=$(echo "$RESPONSE" | sed -n '/^{/,$p')
    
    # Try to extract job ID
    JOB_ID=$(echo "$JSON_BODY" | jq -r '.id // empty' 2>/dev/null)
    
    if [ -n "$JOB_ID" ]; then
        echo -e "${GREEN}Job ID: $JOB_ID${NC}"
        echo ""
        echo -e "${YELLOW}=== Useful Commands ===${NC}"
        echo ""
        echo "Check job status:"
        echo -e "${BLUE}  curl -H \"Authorization: Bearer \$(ivcap context get access-token --refresh-token)\" \\${NC}"
        echo -e "${BLUE}    \"$IVCAP_URL/1/services2/$SERVICE_ID/jobs/$JOB_ID\" | jq${NC}"
        echo ""
        echo "Get job results:"
        echo -e "${BLUE}  curl -H \"Authorization: Bearer \$(ivcap context get access-token --refresh-token)\" \\${NC}"
        echo -e "${BLUE}    \"$IVCAP_URL/1/services2/$SERVICE_ID/jobs/$JOB_ID?with-result-content=true\" | jq${NC}"
        echo ""
        echo "Stream job events:"
        echo -e "${BLUE}  curl --no-buffer -H \"Authorization: Bearer \$(ivcap context get access-token --refresh-token)\" \\${NC}"
        echo -e "${BLUE}    -H \"Accept: text/event-stream\" \\${NC}"
        echo -e "${BLUE}    \"$IVCAP_URL/1/services2/$SERVICE_ID/jobs/$JOB_ID/events\"${NC}"
        echo ""
        echo "Or use the Makefile:"
        echo -e "${BLUE}  make test-get-result JOB_ID=$JOB_ID${NC}"
    else
        echo -e "${YELLOW}Response:${NC}"
        echo "$JSON_BODY" | jq . 2>/dev/null || echo "$JSON_BODY"
    fi
else
    echo -e "${RED}✗ Order creation failed (HTTP $HTTP_STATUS)${NC}"
    echo ""
    echo -e "${YELLOW}Response:${NC}"
    echo "$RESPONSE"
    exit 1
fi

