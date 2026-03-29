#!/usr/bin/env bash
# ----------------------------------------------------------------------------
# cola.sh - Command Launcher (COLA) Integration Library
#
# Generic functions for interacting with the Command Launcher.
# These functions use COLA_* environment variables and work in any package.
# ----------------------------------------------------------------------------

# Get completions from the launcher for a given command prefix
cola::complete() {
    local launcher_name
    launcher_name=$(cola::launcher_name)
    "$launcher_name" __completeNoDesc "$@" 2>/dev/null | grep -v '^:4' || true
}

# Check if a command exists in the launcher
# Usage: cola::has_command group subcommand
# The last argument is the command to check, previous args are the path to it
cola::has_command() {
    local candidates
    local last_arg=${!#}
    set -- "${@:1:$#-1}"
    candidates=$(cola::complete "$@" "")
    for candidate in $candidates; do
        if [[ $candidate == "$last_arg" ]]; then
            return 0
        fi
    done
    return 1
}

# Get the launcher name from COLA_FULL_COMMAND_NAME
# e.g., "vht self env" -> "vht"
cola::launcher_name() {
    echo "${COLA_FULL_COMMAND_NAME%% *}"
}

# Ensure a command exists in the launcher, die if not
cola::ensure_has_command() {
    if ! cola::has_command "$@"; then
        ui::die "Required command not found in $(cola::launcher_name): $*"
    fi
    ui::reassure "Required command found in $(cola::launcher_name): $*"
}
