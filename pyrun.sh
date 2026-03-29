#!/usr/bin/env bash
# ----------------------------------------------------------------------------
# pyrun.sh - Python Script Runner for Command Launcher Packages
#
# This script runs Python scripts within the package's uv-managed environment.
# Uses COLA_* environment variables, making it generic for any launcher package.
# ----------------------------------------------------------------------------

if [[ -n $COLA_DEBUG ]]; then
    set -x
fi

# Populate the package dir when not called from the launcher
if [[ -z $COLA_PACKAGE_DIR ]]; then
    THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    export COLA_PACKAGE_DIR=$THIS_DIR
fi

if [[ ${1:-} == "-m" ]]; then
    PYTHONPATH="$COLA_PACKAGE_DIR:$PYTHONPATH"
fi

export PYTHONPATH="$COLA_PACKAGE_DIR/libs/python:$PYTHONPATH"

# Make the script path absolute if it's a relative path to a file in the package
script="$1"
shift
if [[ -f "$COLA_PACKAGE_DIR/$script" ]]; then
    script="$COLA_PACKAGE_DIR/$script"
fi

exec uv --quiet --project "$COLA_PACKAGE_DIR" run python "$script" "$@"
