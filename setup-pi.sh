#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="https://github.com/bloomslc/ACEE-Booth-Project.git"
INSTALL_DIR="${1:-$HOME/ACEE-Booth-Project}"

require_command() {
	if ! command -v "$1" >/dev/null 2>&1; then
		echo "Error: '$1' is required but was not found in PATH." >&2
		exit 1
	fi
}

require_command git
require_command python3
require_command bun

if [[ -d "$INSTALL_DIR/.git" ]]; then
	echo "Updating existing checkout: $INSTALL_DIR"
	git -C "$INSTALL_DIR" pull --ff-only
elif [[ -e "$INSTALL_DIR" ]]; then
	echo "Error: $INSTALL_DIR exists but is not a Git checkout." >&2
	exit 1
else
	echo "Cloning repository into: $INSTALL_DIR"
	git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

if [[ ! -d .venv ]]; then
	echo "Creating Python virtual environment"
	python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

cd frontend
bun install
bun run build

echo
echo "Pi setup complete."
echo "Repository: $INSTALL_DIR"
echo "Python environment: $INSTALL_DIR/.venv"
echo "Frontend production build: $INSTALL_DIR/frontend/.next"
