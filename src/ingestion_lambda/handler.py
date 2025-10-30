import os
import json
import logging
import sqlite3
from datetime import datetime
import uuid

# Lazy-import boto3 only when needed for S3 operations
_boto3 = None
def boto3_client(service_name):
    global _boto3
    if _boto3 is None:
        import boto3 as _b
        _boto3 = _b
    return _boto3.client(service_name)
import tempfile

# Lazy import for boto3 only when needed

# Basic logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Environment variables expected:
# DB_TYPE: 'postgres' (default) or 'sqlite'
# For postgres: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
# For sqlite: DB_PATH (path to .db file)
# RAW_BUCKET

DB_TYPE = os.environ.get('DB_TYPE', 'postgres').lower()
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = int(os.environ.get('DB_PORT', 5432))
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_PATH = os.environ.get('DB_PATH')
DB_S3_BUCKET = os.environ.get('DB_S3_BUCKET')
DB_S3_KEY = os.environ.get('DB_S3_KEY')
RAW_BUCKET = os.environ.get('RAW_BUCKET', os.environ.get('RAW_S3_BUCKET', ''))
DB_S3_BUCKET = os.environ.get('DB_S3_BUCKET', '')
DB_S3_KEY = os.environ.get('DB_S3_KEY', '')

# Minimal contract:
# Input: event (not used for scheduled run) and context
# Output: dict with status and uploaded S3 key

def query_db(query, params=None, fetch_size=1000):
    """Connects to the DB (Postgres or SQLite), runs a query and returns rows as list of dicts.

    Supports:
      - Postgres via psycopg2 (default)
      - SQLite via sqlite3 when DB_TYPE=sqlite and DB_PATH is set
    """
    if DB_TYPE == 'sqlite':
        # Work with a local variable here to avoid UnboundLocalError when
        # assigning; support either a direct DB_PATH or separate S3 bucket/key variables
        db_path = DB_PATH
        if not db_path:
            if DB_S3_BUCKET and DB_S3_KEY:
                db_path = f's3://{DB_S3_BUCKET}/{DB_S3_KEY}'
            else:
                raise RuntimeError('DB_PATH must be set for sqlite DB_TYPE (or set DB_S3_BUCKET and DB_S3_KEY)')

        # If db_path is an S3 URI, download it to /tmp so sqlite3 can open it.
        local_path = db_path
        if db_path.startswith('s3://'):
            # parse s3://bucket/key
            try:
                import boto3
            except Exception:
                raise RuntimeError('boto3 is required to download DB from S3')

            s3 = boto3.client('s3')
            parts = db_path[5:].split('/', 1)
            if len(parts) != 2:
                raise RuntimeError('Invalid S3 path for DB_PATH')
            bucket, key = parts
            fd, tmp_local = tempfile.mkstemp(prefix='chinook_', suffix='.db')
            os.close(fd)
            try:
                s3.download_file(bucket, key, tmp_local)
            except Exception as e:
                # Provide helpful error
                raise RuntimeError(f'Failed to download DB from S3 {db_path}: {e}')
            local_path = tmp_local
        conn = None
        try:
            conn = sqlite3.connect(local_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(query, params or ())
            rows = [dict(r) for r in cur.fetchall()]
            cur.close()
            return rows
        finally:
            if conn:
                conn.close()
    else:
        # Import psycopg2 lazily so local sqlite-only tests don't require it
        try:
            import psycopg2
            import psycopg2.extras
        except Exception as e:
            raise RuntimeError('psycopg2 is required for Postgres DB_TYPE but is not installed') from e

        conn = None
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=10
            )
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(query, params or ())
            rows = cur.fetchall()
            cur.close()
            return rows
        finally:
            if conn:
                conn.close()


def upload_json_to_s3(bucket, key, data):
    """Upload JSON to S3 if bucket provided, otherwise write locally for dev/test.

    Returns the s3:// path or local file path.
    """
    body = json.dumps(data, default=str, indent=None)

    if not bucket:
        # Local fallback: write to a local file under build/local_uploads
        out_dir = os.environ.get('LOCAL_UPLOAD_DIR', 'build/local_uploads')
        os.makedirs(out_dir, exist_ok=True)
        # sanitize key into a path
        safe_key = key.replace('/', '_')
        out_path = os.path.join(out_dir, safe_key)
        with open(out_path, 'wb') as f:
            f.write(body.encode('utf-8'))
        return out_path

    # Lazy import boto3 so tests/dev runs without boto3 installed don't fail
    import boto3
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket, Key=key, Body=body.encode('utf-8'))
    return f's3://{bucket}/{key}'


def lambda_handler(event, context):
    logger.info('Starting ingestion lambda')
    # Validate configuration depending on DB type. RAW_BUCKET is optional for local testing.
    if DB_TYPE == 'sqlite':
        # If DB_S3_BUCKET/KEY are provided, download the DB to /tmp and update DB_PATH
        if DB_S3_BUCKET and DB_S3_KEY:
            try:
                tmp_path = '/tmp/chinook.db'
                logger.info(f'Downloading sqlite DB from s3://{DB_S3_BUCKET}/{DB_S3_KEY} to {tmp_path}')
                s3 = boto3_client('s3')
                s3.download_file(DB_S3_BUCKET, DB_S3_KEY, tmp_path)
                # set DB_PATH for this invocation
                global DB_PATH
                DB_PATH = tmp_path
            except Exception as e:
                msg = f'Failed to download sqlite DB from s3: {e}'
                logger.exception(msg)
                return {'status': 'error', 'message': msg}
        if not DB_PATH:
            msg = 'DB_PATH must be set for DB_TYPE=sqlite'
            logger.error(msg)
            return {'status': 'error', 'message': msg}
    else:
        missing = [name for name, val in (('DB_HOST', DB_HOST), ('DB_NAME', DB_NAME), ('DB_USER', DB_USER), ('DB_PASSWORD', DB_PASSWORD)) if not val]
        if missing:
            msg = f'Missing required environment variables for Postgres: {missing}'
            logger.error(msg)
            return {'status': 'error', 'message': msg}

    # Simple example query - override in real deployment
    if os.environ.get('INGEST_QUERY'):
        query = os.environ.get('INGEST_QUERY')
    else:
        # sensible defaults per DB type
        if DB_TYPE == 'sqlite':
            # Chinook sample DB - select track name and album title
            query = os.environ.get('INGEST_QUERY') or (
                "SELECT Track.Name AS track_name, Album.Title AS album_title, Track.Milliseconds, Track.Bytes "
                "FROM Track JOIN Album ON Track.AlbumId = Album.AlbumId LIMIT 500"
            )
        else:
            query = os.environ.get('INGEST_QUERY') or "SELECT * FROM public.data LIMIT 100"

    try:
        rows = query_db(query)
        logger.info(f'Fetched {len(rows)} rows from DB')

        # Build a small manifest and upload
        now = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')
        key = f'raw/{now}/{uuid.uuid4()}.json'

        payload = {
            'fetched_at': now,
            'row_count': len(rows),
            'rows': rows
        }

        s3_path = upload_json_to_s3(RAW_BUCKET, key, payload)
        logger.info(f'Uploaded raw payload to {s3_path}')

        return {
            'status': 'ok',
            's3_path': s3_path,
            'row_count': len(rows)
        }

    except Exception as e:
        logger.exception('Error during ingestion')
        return { 'status': 'error', 'message': str(e) }
