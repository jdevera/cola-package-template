#!/usr/bin/env bash
# ----------------------------------------------------------------------------
# lib.sh - Shell Library Entry Point
#
# This file sources all shell libraries in the correct order.
# Commands should source this file to get access to all utilities.
#
# Library loading order:
#   1. jdvlib.sh  - Core bash utilities (vendored from jdevera/jdvlib.sh)
#   2. cola.sh    - Command Launcher integration (generic)
# ----------------------------------------------------------------------------

_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# shellcheck source=./jdvlib.sh
source "$_LIB_DIR/jdvlib.sh"

# shellcheck source=./cola.sh
source "$_LIB_DIR/cola.sh"
