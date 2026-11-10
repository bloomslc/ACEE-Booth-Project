#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="https://github.com/bloomslc/ACEE-Booth-Project.git"
INSTALL_DIR="${1:-$HOME/ACEE-Booth-Project}"
ENV_DIR="${ENV_DIR:-/home/bloomslc/env}"
INSTALL_DIR="$(mkdir -p "$(dirname "$INSTALL_DIR")" && cd "$(dirname "$INSTALL_DIR")" && pwd)/$(basename "$INSTALL_DIR")"

require_command() {
	if ! command -v "$1" >/dev/null 2>&1; then
		echo "Error: '$1' is required but was not found in PATH." >&2
		exit 1
	fi
}

require_command git
require_command python3

ensure_bun() {
	if command -v bun >/dev/null 2>&1; then
		return
	fi

	require_command curl
	echo "Bun was not found. Installing Bun."
	curl -fsSL https://bun.sh/install | bash

	export BUN_INSTALL="${BUN_INSTALL:-$HOME/.bun}"
	export PATH="$BUN_INSTALL/bin:$PATH"
	hash -r 2>/dev/null || true
	require_command bun
}

copy_environment_files() {
	if [[ ! -f "$ENV_DIR/.env.frontend" || ! -f "$ENV_DIR/.env.backend" ]]; then
		echo "Error: expected environment files in $ENV_DIR:" >&2
		echo "  $ENV_DIR/.env.frontend" >&2
		echo "  $ENV_DIR/.env.backend" >&2
		return 1
	fi

	echo "Copying frontend environment: $ENV_DIR/.env.frontend"
	cp "$ENV_DIR/.env.frontend" "$INSTALL_DIR/frontend/.env"
	echo "Copying backend environment: $ENV_DIR/.env.backend"
	cp "$ENV_DIR/.env.backend" "$INSTALL_DIR/backend/.env"
}

setup_project() {
	ensure_bun
	if [[ -d "$INSTALL_DIR/.git" ]]; then
		echo "Updating existing checkout: $INSTALL_DIR"
		git -C "$INSTALL_DIR" pull --ff-only
	elif [[ -e "$INSTALL_DIR" ]]; then
		echo "Error: $INSTALL_DIR exists but is not a Git checkout." >&2
		return 1
	else
		echo "Cloning repository into: $INSTALL_DIR"
		git clone "$REPO_URL" "$INSTALL_DIR"
	fi

	cd "$INSTALL_DIR"
	copy_environment_files

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
}

remove_and_setup() {
	local confirmation
	if [[ ! -e "$INSTALL_DIR" ]]; then
		echo "No existing project folder found. Starting setup."
		setup_project
		return
	fi

	echo "This will permanently delete: $INSTALL_DIR"
	read -rp "Type REMOVE to continue: " confirmation
	if [[ "$confirmation" != "REMOVE" ]]; then
		echo "Removal cancelled."
		return 1
	fi

	rm -rf -- "$INSTALL_DIR"
	setup_project
}

run_in_terminal() {
	local title="$1"
	local command="$2"
	local terminal_command

	terminal_command="cd \"$INSTALL_DIR\" && $command; printf '\\nProcess stopped. Press Enter to close this terminal.'; read -r"
	if command -v lxterminal >/dev/null 2>&1; then
		lxterminal --title="$title" -e bash -lc "$terminal_command" >/dev/null 2>&1 &
	elif command -v gnome-terminal >/dev/null 2>&1; then
		gnome-terminal --title="$title" -- bash -lc "$terminal_command" >/dev/null 2>&1 &
	elif command -v x-terminal-emulator >/dev/null 2>&1; then
		x-terminal-emulator -T "$title" -e bash -lc "$terminal_command" >/dev/null 2>&1 &
	else
		return 1
	fi
}

run_project() {
	ensure_bun
	if [[ ! -x "$INSTALL_DIR/.venv/bin/uvicorn" || ! -d "$INSTALL_DIR/frontend/node_modules" ]]; then
		echo "The project is not set up yet. Choose setup first." >&2
		return 1
	fi

	local backend_command=".venv/bin/uvicorn app.main:app --host 10.1.87.237 --port 8080 --app-dir backend"
	local frontend_command="cd frontend && bun start"
	if ! run_in_terminal "ACEE backend" "$backend_command" || ! run_in_terminal "ACEE frontend" "$frontend_command"; then
		echo "No supported terminal emulator was found. Run these commands in two terminals:"
		echo "  cd $INSTALL_DIR && $backend_command"
		echo "  cd $INSTALL_DIR && $frontend_command"
		return 1
	fi

	echo "Backend and frontend terminals launched."
}

choose_action() {
	local choice
	echo
	echo "ACEE Booth Raspberry Pi setup"
	echo "1) Setup project"
	echo "2) Run project"
	echo "3) Setup project and run"
	echo "4) Remove existing project and setup fresh"
	echo "5) Exit"

	read -rp "Select an option [1-5]: " choice
	case "$choice" in
		1) setup_project ;;
		2) run_project ;;
		3) setup_project && run_project ;;
		4) remove_and_setup ;;
		5) exit 0 ;;
		*) echo "Invalid option." >&2; return 1 ;;
	esac
}

choose_action

echo
echo "Pi setup complete."
echo "Repository: $INSTALL_DIR"
echo "Python environment: $INSTALL_DIR/.venv"
echo "Frontend production build: $INSTALL_DIR/frontend/.next"
