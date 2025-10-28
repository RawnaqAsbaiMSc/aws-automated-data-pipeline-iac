import os
import json

# Local runner for ingestion lambda using Chinook SQLite DB
# Usage: set environment variables or edit defaults below and run:
# python src/ingestion_lambda/local_run.py

# Defaults for local testing - set these BEFORE importing the handler so the module
# picks up the correct environment at import time.
os.environ.setdefault('DB_TYPE', 'sqlite')
# path inside repo
os.environ.setdefault('DB_PATH', os.path.join(os.path.dirname(__file__), '../../data/chinook.db'))
# For local testing we won't upload to S3; instead set RAW_BUCKET to empty and handler will still run
os.environ.setdefault('RAW_BUCKET', '')

from handler import lambda_handler

if __name__ == '__main__':
    result = lambda_handler({}, None)
    print(json.dumps(result, indent=2, default=str))
