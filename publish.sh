#!/bin/bash
# PyResolvers Publishing Helper Script
# Usage: ./publish.sh [test|prod]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo -e "${RED}Error: Virtual environment not found${NC}"
    echo "Run: python3 -m venv venv && source venv/bin/activate && pip install -e ."
    exit 1
fi

# Ensure tools are installed
echo -e "${BLUE}Checking required tools...${NC}"
pip install --upgrade build twine > /dev/null 2>&1

# Parse arguments
MODE=${1:-test}  # Default to test

if [ "$MODE" != "test" ] && [ "$MODE" != "prod" ]; then
    echo -e "${RED}Usage: $0 [test|prod]${NC}"
    echo "  test - Upload to Test PyPI (recommended first)"
    echo "  prod - Upload to production PyPI"
    exit 1
fi

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}PyResolvers Publishing Script${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Get current version
VERSION=$(python -c "from pyresolvers.lib.core.__version__ import __version__; print(__version__)")
echo -e "${BLUE}Current version: ${GREEN}$VERSION${NC}"
echo ""

# Confirm
if [ "$MODE" == "prod" ]; then
    echo -e "${YELLOW}⚠️  WARNING: You are about to publish to PRODUCTION PyPI${NC}"
    echo -e "${YELLOW}This action cannot be undone!${NC}"
    echo ""
    read -p "Are you sure you want to publish v$VERSION to PyPI? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^yes$ ]]; then
        echo -e "${RED}Aborted.${NC}"
        exit 1
    fi
else
    echo -e "${BLUE}Publishing to Test PyPI...${NC}"
fi

echo ""
echo -e "${BLUE}Step 1: Cleaning old builds...${NC}"
rm -rf dist/ build/ *.egg-info
echo -e "${GREEN}✓ Cleaned${NC}"

echo ""
echo -e "${BLUE}Step 2: Building package...${NC}"
python -m build
echo -e "${GREEN}✓ Built${NC}"

echo ""
echo -e "${BLUE}Step 3: Validating package...${NC}"
twine check dist/*
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Package validation failed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Validated${NC}"

echo ""
echo -e "${BLUE}Step 4: Uploading to $([ "$MODE" == "test" ] && echo "Test PyPI" || echo "PyPI")...${NC}"

if [ "$MODE" == "test" ]; then
    twine upload --repository testpypi dist/*

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}✓ Successfully published to Test PyPI!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${BLUE}Test installation:${NC}"
        echo "  pip install --index-url https://test.pypi.org/simple/ --no-deps pyresolvers"
        echo ""
        echo -e "${BLUE}View on Test PyPI:${NC}"
        echo "  https://test.pypi.org/project/pyresolvers/$VERSION/"
        echo ""
        echo -e "${YELLOW}After testing, publish to production with:${NC}"
        echo "  ./publish.sh prod"
    else
        echo -e "${RED}✗ Upload failed!${NC}"
        exit 1
    fi
else
    twine upload dist/*

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}✓ Successfully published to PyPI!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${BLUE}Installation:${NC}"
        echo "  pip install pyresolvers"
        echo ""
        echo -e "${BLUE}View on PyPI:${NC}"
        echo "  https://pypi.org/project/pyresolvers/$VERSION/"
        echo ""
        echo -e "${BLUE}Next steps:${NC}"
        echo "  1. Test installation: pip install pyresolvers"
        echo "  2. Verify CLI works: pyresolvers -h"
        echo "  3. Create GitHub release: https://github.com/PigeonSec/pyresolvers/releases"
        echo "  4. Create project-specific API token at: https://pypi.org/manage/project/pyresolvers/settings/"
    else
        echo -e "${RED}✗ Upload failed!${NC}"
        exit 1
    fi
fi

echo ""
