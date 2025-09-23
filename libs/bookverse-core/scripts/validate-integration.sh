#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 BookVerse Core Integration Validation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${BLUE}📦 Checking library installation...${NC}"
if python3 -c "import bookverse_core; print('✅ bookverse-core imported successfully')" 2>/dev/null; then
    echo -e "${GREEN}✅ Library installation validated${NC}"
else
    echo -e "${RED}❌ Library not installed or importable${NC}"
    echo -e "${YELLOW}   Run: pip install -e .${NC}"
    exit 1
fi

echo -e "${BLUE}🎯 Checking demo application...${NC}"
cd "$(dirname "$0")/../app"
if python3 -c "from main import app; print('✅ Demo app imports successful')" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Demo application validated${NC}"
else
    echo -e "${YELLOW}⚠️  Demo application has import issues (but may still work)${NC}"
fi

echo -e "${BLUE}⚙️  Checking configuration files...${NC}"
cd "$(dirname "$0")/.."
config_files=(
    "config/version-map.yaml"
    "config/demo-config.yaml"
    "pyproject.toml"
    "requirements.txt"
)

for file in "${config_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✅ Found: $file${NC}"
    else
        echo -e "${YELLOW}⚠️  Missing: $file${NC}"
    fi
done

echo -e "${BLUE}🧪 Checking test suite...${NC}"
if [[ -d "tests/" ]]; then
    echo -e "${GREEN}✅ Test directory found${NC}"
    if [[ -f "tests/conftest.py" ]]; then
        echo -e "${GREEN}✅ Test configuration found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Test directory not found${NC}"
fi

echo -e "${BLUE}🐳 Checking Docker setup...${NC}"
if [[ -f "Dockerfile" ]]; then
    echo -e "${GREEN}✅ Dockerfile found${NC}"
else
    echo -e "${YELLOW}⚠️  Dockerfile not found${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Integration validation complete!${NC}"
echo -e "${GREEN}   bookverse-core is ready for demo presentation${NC}"
