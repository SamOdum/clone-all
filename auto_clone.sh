#!/bin/bash

# Automated GitHub Organization Cloner
# This script handles SSH agent setup and runs the Python cloner

set -e  # Exit on any error

# Configuration
ORG_NAME="$1"
GITHUB_TOKEN="${2:-$GITHUB_TOKEN}"
SSH_KEY="${3:-$HOME/.ssh/id_ed25519}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check arguments
if [ -z "$ORG_NAME" ]; then
    error "Usage: $0 <organization_name> [github_token] [ssh_key_path]"
    error "Example: $0 microsoft"
    error "Example: $0 microsoft ghp_xxxxx ~/.ssh/id_rsa"
    exit 1
fi

info "Setting up automated cloning for organization: $ORG_NAME"

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    error "SSH key not found at: $SSH_KEY"
    exit 1
fi

# Start SSH agent if not running
if [ -z "$SSH_AGENT_PID" ]; then
    info "Starting SSH agent..."
    eval "$(ssh-agent -s)"
else
    info "SSH agent already running (PID: $SSH_AGENT_PID)"
fi

# Check if key is already loaded
if ssh-add -l | grep -q "$SSH_KEY"; then
    info "SSH key already loaded in agent"
else
    info "Adding SSH key to agent (you may be prompted for passphrase)..."
    ssh-add "$SSH_KEY"
fi

# Verify SSH connection to GitHub
info "Testing SSH connection to GitHub..."
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    info "SSH authentication successful!"
else
    warn "SSH authentication test inconclusive, but proceeding..."
fi

# Build Python command
PYTHON_CMD="python3 github_org_puller.py $ORG_NAME --ssh"

if [ -n "$GITHUB_TOKEN" ]; then
    PYTHON_CMD="$PYTHON_CMD --token $GITHUB_TOKEN"
fi

# Run the Python script
info "Starting repository cloning..."
info "Command: $PYTHON_CMD"

$PYTHON_CMD

# Clean up (optional - comment out if you want to keep agent running)
# info "Cleaning up SSH agent..."
# ssh-agent -k

info "Done!"
