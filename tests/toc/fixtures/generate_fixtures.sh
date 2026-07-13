#!/bin/bash
# Regenerate committed test fixtures for a specific doxygen version.
#
# Usage:
#   DOXYGEN_VERSION=1.9.8  bash generate_fixtures.sh
#   DOXYGEN_VERSION=1.17.0 bash generate_fixtures.sh
#
# Will install the requested doxygen version automatically if not present.
# The generated files are committed to the repo so tests can run
# without needing each version of doxygen installed locally.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/source"

VERSION="${DOXYGEN_VERSION:-}"
if [[ -z "$VERSION" ]]; then
    echo "ERROR: DOXYGEN_VERSION must be set"
    echo "Usage: DOXYGEN_VERSION=1.17.0 bash generate_fixtures.sh"
    exit 1
fi

# Install correct doxygen version if needed
bash "${SCRIPT_DIR}/install_doxygen.sh" "${VERSION}"

# Make sure the just-installed binary is on PATH
export PATH="$HOME/.local/bin:$PATH"

# e.g. 1.17.0 -> 1_17_0,  1.9.8 -> 1_9_8
VERSION_SHORT="$(echo "$VERSION" | tr '.' '_')"
OUT_DIR="${SCRIPT_DIR}/doxygen_${VERSION_SHORT}"

echo ""
echo "=== Generating fixtures for doxygen ${VERSION} ==="
echo "    source:  ${SOURCE_DIR}"
echo "    output:  ${OUT_DIR}"
echo ""

# Run doxygen in a temp dir
TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

# Substitute placeholders in Doxyfile.in
sed \
    -e "s|@OUTPUT_DIR@|${TMP}/output|g" \
    -e "s|@INPUT_DIR@|${SOURCE_DIR}|g" \
    "${SOURCE_DIR}/Doxyfile.in" > "${TMP}/Doxyfile"

echo "Running doxygen ${VERSION}..."
doxygen "${TMP}/Doxyfile"

# Copy fixtures
mkdir -p "$OUT_DIR"
cp "${TMP}/output/html/index.html"  "${OUT_DIR}/index.html"
cp "${TMP}/output/html/menudata.js" "${OUT_DIR}/menudata.js"

if [[ -f "${TMP}/output/html/topics.html" ]]; then
    cp "${TMP}/output/html/topics.html" "${OUT_DIR}/topics.html"
    echo "Copied topics.html  (doxygen > 1.9.8)"
elif [[ -f "${TMP}/output/html/modules.html" ]]; then
    cp "${TMP}/output/html/modules.html" "${OUT_DIR}/modules.html"
    echo "Copied modules.html (doxygen <= 1.9.8)"
else
    echo "WARNING: neither topics.html nor modules.html found"
fi

echo ""
echo "=== Done ==="
echo "Files written to ${OUT_DIR}:"
ls -la "${OUT_DIR}"
echo ""
echo "Remember to commit these fixture files."
