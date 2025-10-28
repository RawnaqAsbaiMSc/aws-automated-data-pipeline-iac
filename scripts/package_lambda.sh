#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="$1"
OUT_DIR="${2:-build/function}"

if [ -z "$SRC_DIR" ]; then
  echo "Usage: $0 <source_dir> [out_dir]"
  exit 2
fi

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# Copy source into out dir and create a zip
cp -r "$SRC_DIR"/* "$OUT_DIR"/

pushd "$OUT_DIR" > /dev/null
zip -r ../function.zip .
popd

echo "Function package written to: build/function.zip"
