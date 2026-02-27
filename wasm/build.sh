#!/usr/bin/env bash
# Build the Pygame casino GUI as a WebAssembly bundle using pygbag.
#
# Prerequisites:
#   pip install pygbag
#
# Usage:
#   cd CScapstone/wasm && ./build.sh
#
# Output:
#   ../frontend/public/game/ — static files (HTML, JS, WASM, assets)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GUI_DIR="$PROJECT_ROOT/gui"
OUTPUT_DIR="$PROJECT_ROOT/frontend/public/game"

echo "==> Building WASM from $GUI_DIR"
echo "==> Output to $OUTPUT_DIR"

# Ensure pygbag is installed
if ! command -v pygbag &> /dev/null; then
    echo "ERROR: pygbag not found. Install it with: pip install pygbag"
    exit 1
fi

# Clean previous build
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# pygbag builds in-place and serves a dev server by default.
# Use --build flag for CI/production builds without starting a server.
cd "$GUI_DIR"
pygbag --build --ume_block 0 --title "Capstone Casino" .

# pygbag outputs to gui/build/web/ — copy to our output directory
if [ -d "$GUI_DIR/build/web" ]; then
    cp -r "$GUI_DIR/build/web/"* "$OUTPUT_DIR/"

    # Fix broken BrowserFS CDN URL (pygbag 0.9.3 references a 404 on its CDN)
    sed -i.bak 's|pygame-web.github.io/cdn/[^"]*browserfs.min.js|cdn.jsdelivr.net/npm/browserfs@1.4.1/dist/browserfs.min.js|g' "$OUTPUT_DIR/index.html"
    rm -f "$OUTPUT_DIR/index.html.bak"

    echo "==> Build complete: $OUTPUT_DIR"
else
    echo "ERROR: pygbag build output not found at $GUI_DIR/build/web/"
    exit 1
fi
