#!/bin/bash
# RAHUL Advanced AI v4.0 — One-Click Linux Installer

set -e
GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║      RAHUL Advanced AI v4.0 — Linux Installer       ║"
echo "║   OpenRouter + Nvidia + Groq  •  Swarm Architecture  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Python check
python3 -c "import sys; exit(0 if sys.version_info>=(3,10) else 1)" || {
    echo "Python 3.10+ required"; exit 1; }
echo -e "${GREEN}✓ Python OK${NC}"

# System packages
echo -e "\n${CYAN}Installing system tools...${NC}"
sudo apt-get update -qq 2>/dev/null
sudo apt-get install -y python3-tk scrot xclip libnotify-bin \
     at network-manager brightnessctl curl 2>/dev/null || true

# Python packages
echo -e "\n${CYAN}Installing Python packages...${NC}"
pip3 install --upgrade pip -q
pip3 install -r requirements.txt

# Playwright
echo -e "\n${CYAN}Installing Playwright browsers...${NC}"
python3 -m playwright install firefox chromium
python3 -m playwright install-deps 2>/dev/null || true

# Dirs
mkdir -p astra_brain workspaces memory config actions core interface tools assets

# .env setup
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "\n${CYAN}⚠  Edit .env with your API keys before running!${NC}"
    echo "   openrouter.ai  |  build.nvidia.com  |  console.groq.com"
fi

echo -e "\n${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ✅  Setup Complete!                                 ║"
echo "║                                                      ║"
echo "║  1. Edit .env with your FREE API keys               ║"
echo "║  2. python3 run.py                                   ║"
echo "║                                                      ║"
echo "║  FREE keys (all have free tiers):                    ║"
echo "║    openrouter.ai  •  build.nvidia.com               ║"
echo "║    console.groq.com                                  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
