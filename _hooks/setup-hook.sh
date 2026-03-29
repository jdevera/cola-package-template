#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR="${COLA_PACKAGE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
JDVLIB_FILE="$PACKAGE_DIR/libs/sh/jdvlib.sh"
JDVLIB_VERSION_FILE="$PACKAGE_DIR/jdvlib.version"

# --- jdvlib.sh version check and download (plain bash, no dependencies) ---

if [[ ! -f "$JDVLIB_VERSION_FILE" ]]; then
    echo "ERROR: jdvlib.version file not found at $JDVLIB_VERSION_FILE" >&2
    exit 1
fi

PINNED_VERSION=$(tr -d '[:space:]' < "$JDVLIB_VERSION_FILE")

INSTALLED_VERSION=""
if [[ -f "$JDVLIB_FILE" ]]; then
    INSTALLED_VERSION=$(grep -m1 "^__JDVLIB_VERSION=" "$JDVLIB_FILE" | sed "s/^__JDVLIB_VERSION='\\(.*\\)'/\\1/" | cut -d- -f1-1)
    # Normalize: version file has "v0.2.0", jdvlib header has "v0.2.0-0" -> compare base
fi

if [[ "$INSTALLED_VERSION" != "$PINNED_VERSION" ]]; then
    echo "Downloading jdvlib.sh $PINNED_VERSION..."
    DOWNLOAD_URL="https://github.com/jdevera/jdvlib.sh/releases/download/${PINNED_VERSION}/jdvlib.sh"
    if command -v curl &>/dev/null; then
        curl -fsSL "$DOWNLOAD_URL" -o "$JDVLIB_FILE"
    elif command -v wget &>/dev/null; then
        wget -q "$DOWNLOAD_URL" -O "$JDVLIB_FILE"
    else
        echo "ERROR: Neither curl nor wget found. Cannot download jdvlib.sh" >&2
        exit 1
    fi
    echo "jdvlib.sh $PINNED_VERSION installed."
else
    echo "jdvlib.sh $PINNED_VERSION already installed."
fi

# --- Now source the library and use its functions ---

# shellcheck source=../libs/sh/lib.sh
source "$PACKAGE_DIR/libs/sh/lib.sh"

sys::ensure_has_commands uv

cd "$PACKAGE_DIR" || ui::die "Failed to change to the package directory"
uv sync
