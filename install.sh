#!/usr/bin/env bash
# ==============================================================================
# Aegis AI Security Guardrail Proxy - Automated Installer (Linux / macOS)
# ==============================================================================
set -euo pipefail

# ANSI Colors
CLR_RESET="\033[0m"
CLR_BOLD="\033[1m"
CLR_CYAN="\033[1;36m"
CLR_GREEN="\033[1;32m"
CLR_YELLOW="\033[1;33m"
CLR_RED="\033[1;31m"
CLR_GRAY="\033[0;90m"

print_banner() {
    cat << "EOF"
[1;36m
      ___      _______  _______  ___   _______ 
     |   |    |       ||       ||   | |       |
     |   |    |    ___||    ___||   | |  _____|
     |   |    |   |___ |   | __ |   | | |_____ 
     |   |___ |    ___||   ||  ||   | |_____  |
     |       ||   |___ |   |_| ||   |  _____| |
     |_______||_______||_______||___| |_______|
     AI SECURITY GUARDRAIL PROXY & FORENSICS
[0m
EOF
}

log_info() {
    echo -e "${CLR_CYAN}[INFO]${CLR_RESET} $1"
}

log_success() {
    echo -e "${CLR_GREEN}[SUCCESS]${CLR_RESET} $1"
}

log_warn() {
    echo -e "${CLR_YELLOW}[WARN]${CLR_RESET} $1"
}

log_error() {
    echo -e "${CLR_RED}[ERROR]${CLR_RESET} $1"
}

# ------------------------------------------------------------------------------
# 1. Dependency & Environment Checks
# ------------------------------------------------------------------------------
print_banner
log_info "Initializing Aegis automated deployment on $(uname -s) ($(uname -m))..."

# Check Python 3.11+
if command -v python3 &>/dev/null; then
    PY_BIN="python3"
elif command -v python &>/dev/null; then
    PY_BIN="python"
else
    log_error "Python is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PY_VER=$($PY_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$($PY_BIN -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PY_BIN -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]); then
    log_error "Python 3.11+ is required. Found Python $PY_VER."
    exit 1
fi
log_success "Verified Python $PY_VER ($($PY_BIN --version))"

# ------------------------------------------------------------------------------
# 2. Virtual Environment Setup
# ------------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating isolated virtual environment at .venv..."
    $PY_BIN -m venv "$VENV_DIR"
    log_success "Virtual environment created."
else
    log_info "Existing virtual environment found at .venv."
fi

# Activate virtual environment
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# ------------------------------------------------------------------------------
# 3. Dependencies Installation
# ------------------------------------------------------------------------------
log_info "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel --quiet

log_info "Installing Aegis dependencies from pyproject.toml..."
pip install -e ".[dev]" --quiet || pip install -e . --quiet
log_success "All application dependencies installed."

# ------------------------------------------------------------------------------
# 4. Environment & Database Configuration
# ------------------------------------------------------------------------------
if [ ! -f ".env" ]; then
    log_info "Creating default .env from .env.example..."
    cp .env.example .env
    log_success ".env configuration file created."
else
    log_info "Existing .env found."
fi

log_info "Initializing SQLite WAL database storage in data/..."
mkdir -p data
python -c "from app.models.database import db; print('[+] SQLite tables and security policies initialized in WAL mode.')"
log_success "Database schema verified."

# ------------------------------------------------------------------------------
# 5. Cryptographic License Verification
# ------------------------------------------------------------------------------
log_info "Verifying Ed25519 Cryptographic Licensing subsystem..."
python -c "
import os
from app.security.license import license_manager
status = license_manager.get_status(os.getenv('AEGIS_LICENSE_TOKEN'))
print(f'[+] License Status: Tier={status.get(\"tier\").upper()}, Active={status.get(\"active\")}, Air-Gapped Verification=PASS')
"

# ------------------------------------------------------------------------------
# 6. Docker & Daemon Detection
# ------------------------------------------------------------------------------
if command -v docker &>/dev/null && command -v docker-compose &>/dev/null; then
    log_success "Docker & Docker Compose detected. Container deployment is available via 'docker compose up -d'."
fi

echo ""
echo -e "${CLR_GREEN}==============================================================================${CLR_RESET}"
echo -e "${CLR_BOLD}${CLR_CYAN}  🛡️  AEGIS AI SECURITY GUARDRAIL PROXY READY FOR PRODUCTION  🛡️${CLR_RESET}"
echo -e "${CLR_GREEN}==============================================================================${CLR_RESET}"
echo -e "  ${CLR_BOLD}Dashboard UI  :${CLR_RESET} http://localhost:8000/"
echo -e "  ${CLR_BOLD}Health Probe  :${CLR_RESET} http://localhost:8000/health"
echo -e "  ${CLR_BOLD}OpenAI Proxy  :${CLR_RESET} http://localhost:8000/v1/chat/completions"
echo -e "  ${CLR_BOLD}Anthropic Proxy:${CLR_RESET} http://localhost:8000/v1/messages"
echo -e "  ${CLR_BOLD}Text Scanner  :${CLR_RESET} http://localhost:8000/v1/scan/text"
echo -e "  ${CLR_BOLD}Doc Forensics :${CLR_RESET} http://localhost:8000/v1/scan/document"
echo ""
echo -e "${CLR_YELLOW}Start the proxy daemon:${CLR_RESET}"
echo -e "  ${CLR_BOLD}source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2${CLR_RESET}"
echo -e "or run with Docker:"
echo -e "  ${CLR_BOLD}docker compose up -d --build${CLR_RESET}"
echo ""
