#!/bin/bash
# Test runner for snapshot service

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [ "$1" = "integration" ]; then
    echo -e "${BLUE}Running integration tests (mocked APIs)...${NC}"
    python3 tests/test_integration.py -v

elif [ "$1" = "e2e" ]; then
    echo -e "${BLUE}Running end-to-end tests (requires backend running)...${NC}"
    echo ""
    echo "Prerequisites:"
    echo "  1. Backend server must be running at http://localhost:8080"
    echo "  2. Valid .env file with credentials"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."
    echo ""
    python3 tests/test_e2e.py -v

elif [ "$1" = "unit" ]; then
    echo -e "${BLUE}Running unit tests...${NC}"
    python3 -m unittest discover -s tests -p "test_*.py" -v

else
    echo "Usage: $0 {integration|e2e|unit}"
    echo ""
    echo "Test types:"
    echo "  integration  - Integration tests with mocked APIs"
    echo "  e2e          - End-to-end tests against real backend (requires server running)"
    echo "  unit         - All unit tests"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh integration"
    echo "  ./run_tests.sh e2e"
    exit 1
fi

exit $?
