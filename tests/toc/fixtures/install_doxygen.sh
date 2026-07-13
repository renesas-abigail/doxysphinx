#!/bin/bash
# Install a specific doxygen version.
#
# Usage:
#   bash install_doxygen.sh 1.17.0
#   bash install_doxygen.sh apt        # install distro package instead
#
# The binary is installed to $HOME/.local/bin/doxygen

set -euo pipefail

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
    echo "ERROR: version argument required"
    echo "Usage: bash install_doxygen.sh 1.17.0"
    echo "       bash install_doxygen.sh apt"
    exit 1
fi

INSTALL_DIR="$HOME/.local/bin"

if [[ "$VERSION" == "apt" ]]; then
    echo "=== Installing doxygen via apt ==="
    sudo apt-get update
    sudo apt-get install -y doxygen
    echo "Installed: $(doxygen --version)"
    exit 0
fi

# Check if correct version already installed and working
if [[ -f "${INSTALL_DIR}/doxygen" ]]; then
    if INSTALLED="$("${INSTALL_DIR}/doxygen" --version 2>/dev/null)"; then
        if [[ "$INSTALLED" == "$VERSION"* ]]; then
            echo "doxygen ${VERSION} already installed, skipping."
            exit 0
        fi
    else
        echo "Existing doxygen binary is broken, reinstalling..."
        rm -f "${INSTALL_DIR}/doxygen"
    fi
fi

echo "=== Installing doxygen ${VERSION} ==="

VERSION_TAG="Release_$(echo "${VERSION}" | tr '.' '_')"
DOWNLOAD_URL="https://github.com/doxygen/doxygen/releases/download/${VERSION_TAG}/doxygen-${VERSION}.linux.bin.tar.gz"

mkdir -p "$INSTALL_DIR"

echo "Downloading from ${DOWNLOAD_URL}..."
curl -sSLf "$DOWNLOAD_URL" | \
    tar -xzf - \
        --strip-components=2 \
        -C "$INSTALL_DIR" \
        "doxygen-${VERSION}/bin/doxygen"

chmod +x "${INSTALL_DIR}/doxygen"

# Verify correct version
INSTALLED_VERSION="$("${INSTALL_DIR}/doxygen" --version)"
if [[ "$INSTALLED_VERSION" != "$VERSION"* ]]; then
    echo "ERROR: Expected doxygen ${VERSION} but found ${INSTALLED_VERSION}"
    exit 1
fi

echo "Installed doxygen ${VERSION} to ${INSTALL_DIR}/doxygen"

if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo ""
    echo "NOTE: Add to your PATH if not already present:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
