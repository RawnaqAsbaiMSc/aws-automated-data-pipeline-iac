#!/usr/bin/env bash
set -euo pipefail

REQ_FILE="$1"
OUT_DIR="${2:-build/layer}"

if [ -z "$REQ_FILE" ]; then
  echo "Usage: $0 <requirements.txt> [out_dir]"
  exit 2
fi

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# Prepare a python/ directory for Lambda Layer (python/lib/python3.11/site-packages for custom runtimes may be required)
LAYER_PY_DIR="$OUT_DIR/python"
mkdir -p "$LAYER_PY_DIR"

# Install into the layer python directory
pip3 install -r "$REQ_FILE" -t "$LAYER_PY_DIR"

# Create zip
pushd "$OUT_DIR" > /dev/null
zip -r ../layer.zip .
popd

echo "Layer package written to: build/layer.zip"
