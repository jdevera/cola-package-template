#!/usr/bin/env bash
# ----------------------------------------------------------------------------
# hello.sh - Example bash command
#
# Demonstrates:
#   - Sourcing lib.sh for access to shell utilities
#   - args::check_help_arg for --help/-h support
#   - --complete flag pattern for shell completion
#   - ui:: functions for formatted output
# ----------------------------------------------------------------------------
set -euo pipefail

source "${COLA_PACKAGE_DIR}/libs/sh/lib.sh"

USAGE="Usage: $(cola::launcher_name) examples hello [NAME]"

help() {
    cat <<EOF
$USAGE

Say hello to someone (or the world).

Options:
    -h, --help     Show this help message
    --complete     Output completions for the launcher
EOF
}

# Handle --help
args::check_help_arg help "$@"

# Handle --complete for launcher auto-completion
if [[ "${1:-}" == "--complete" ]]; then
    echo "--help"
    echo "-h"
    exit 0
fi

NAME="${1:-World}"
ui::ok "Hello, ${NAME}!"
