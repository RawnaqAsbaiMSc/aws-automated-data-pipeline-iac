#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="data"
OUT_FILE="$OUT_DIR/chinook.db"

mkdir -p "$OUT_DIR"

if [ -f "$OUT_FILE" ]; then
  echo "Chinook DB already exists at $OUT_FILE"
  exit 0
fi

# Official Chinook sqlite raw file hosted in lerocha/chinook-database repo
URL="https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"

echo "Downloading Chinook SQLite DB from $URL"

curl -L -o "$OUT_FILE" "$URL"

if [ -f "$OUT_FILE" ]; then
  echo "Downloaded Chinook DB to $OUT_FILE"
else
  echo "Failed to download Chinook DB"
  exit 2
fi
