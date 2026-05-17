#!/bin/bash
# PORT-777 Installation Script
# Usage: curl -sSL https://raw.githubusercontent.com/PORT-777/0xMrPORT777/main/install.sh | bash
# Or:    chmod +x install.sh && ./install.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "  ██████╗  ██████╗ ██████╗ ████████╗    ███████╗███████╗███████╗"
echo "  ██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝    ╚════██║╚════██║╚════██║"
echo "  ██████╔╝██║   ██║██████╔╝   ██║           ██╔╝    ██╔╝    ██╔╝"
echo "  ██╔═══╝ ██║   ██║██╔══██╗   ██║          ██╔╝    ██╔╝    ██╔╝"
echo "  ██║     ╚██████╔╝██║  ██║   ██║          ██║     ██║     ██║"
echo "  ╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝          ╚═╝     ╚═╝     ╚═╝"
echo -e "  PORT-777 v5.3 — Installer${NC}"
echo ""

# Check OS
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}⚠️  Warning: This script is optimized for Kali Linux.${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Auto-update check
if [ -d ".git" ]; then
    echo -e "${YELLOW}🔄 Checking for updates...${NC}"
    git stash --quiet 2>/dev/null || true
    git fetch --quiet origin main 2>/dev/null || true
    LOCAL=$(git rev-parse HEAD 2>/dev/null)
    REMOTE=$(git rev-parse origin/main 2>/dev/null)
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo -e "${YELLOW}📥 New version available. Updating...${NC}"
        git pull origin main --quiet
        echo -e "${GREEN}✅ Updated to latest version.${NC}"
    else
        echo -e "${GREEN}✅ Already up to date.${NC}"
    fi
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Installing...${NC}"
    sudo apt update && sudo apt install -y python3 python3-pip python3-venv
fi

# Check Pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ Pip not found. Installing...${NC}"
    sudo apt install -y python3-pip
fi

# Install System Dependencies (idempotent)
echo -e "${YELLOW}📦 Installing system dependencies...${NC}"
sudo apt update -qq

# Package list — split to handle failures gracefully
CORE_PACKAGES="nmap git curl wget libxml2-dev libxslt1-dev libcairo2-dev libpango1.0-dev libffi-dev shared-mime-info"
PDF_PACKAGES="libgdk-pixbuf-2.0-dev libgdk-pixbuf2.0-0"

echo -e "${YELLOW}  → Core packages...${NC}"
sudo apt install -y $CORE_PACKAGES 2>/dev/null || true

echo -e "${YELLOW}  → PDF rendering packages...${NC}"
sudo apt install -y $PDF_PACKAGES 2>/dev/null || {
    echo -e "${YELLOW}  ⚠️  PDF packages not available, trying alternatives...${NC}"
    sudo apt install -y libgdk-pixbuf2.0-0 2>/dev/null || true
}

# Install Python Dependencies
echo -e "${YELLOW}🐍 Installing Python dependencies...${NC}"
pip3 install -r requirements.txt --break-system-packages 2>/dev/null || pip3 install -r requirements.txt

# Install Dev Dependencies (Optional)
if [ -f "requirements-dev.txt" ]; then
    echo -e "${YELLOW}🧪 Installing dev dependencies (tests)...${NC}"
    pip3 install -r requirements-dev.txt --break-system-packages 2>/dev/null || pip3 install -r requirements-dev.txt
fi

# Setup Env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}🔑 Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env. Please edit it to add your API key.${NC}"
fi

# Build UI (if source exists)
if [ -d "server/ui" ] && command -v npm &> /dev/null; then
    echo -e "${YELLOW}🌐 Building Web UI...${NC}"
    cd server/ui
    npm install --quiet
    npm run build --quiet
    cd ../..
    echo -e "${GREEN}✅ Web UI built.${NC}"
elif [ ! -d "server/ui" ]; then
    echo -e "${GREEN}✅ Web UI already built or source not found.${NC}"
fi

# Run Tests
echo -e "${YELLOW}🧪 Running tests...${NC}"
python3 -m pytest tests/ -q --tb=short || echo -e "${RED}⚠️  Some tests failed. Check output above.${NC}"

echo ""
echo -e "${GREEN}✨ Installation Complete!${NC}"
echo ""
echo -e "🚀 Run CLI:    ${YELLOW}python3 port777.py${NC}"
echo -e "🖥️  Run Web:    ${YELLOW}python3 port777.py --serve${NC}"
echo ""
echo -e "${RED}⚠️  Don't forget to add your API key in .env!${NC}"
