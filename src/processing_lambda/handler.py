import os
import json
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Processing lambda triggered by S3 event for raw payloads.

    It downloads the raw JSON produced by the ingestion lambda, selects a
    subset of fields (track_name, album_title, composer, milliseconds, unitprice),
    and writes a transformed JSON to the analytics bucket.
    """
    import os
    import json
    import logging

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    _boto3 = None
    def boto3_client(service_name):
        global _boto3
        if _boto3 is None:
            import boto3 as _b
            _boto3 = _b
        return _boto3.client(service_name)

    def lambda_handler(event, context):
        """Read raw payload from S3 (written by ingestion), simplify rows to track_name and album_title,
        write processed payload to processed bucket and write analytics summary (counts per album) to analytics bucket.
        Expects env vars: RAW_BUCKET, PROCESSED_BUCKET, ANALYTICS_BUCKET
        """
        logger.info('Processing lambda invoked')
        raw_bucket = os.environ.get('RAW_BUCKET', '')
        processed_bucket = os.environ.get('PROCESSED_BUCKET', '')
        analytics_bucket = os.environ.get('ANALYTICS_BUCKET', '')

        # Extract S3 key from event (support S3 event records)
        try:
            record = event.get('Records', [event])[0]
            s3_info = record.get('s3', {})
            bucket = s3_info.get('bucket', {}).get('name', raw_bucket)
            key = s3_info.get('object', {}).get('key')
        except Exception:
            logger.exception('Failed to parse event')
            return {'status': 'error', 'message': 'invalid event'}

        if not key:
            logger.error('S3 object key not found in event')
            return {'status': 'error', 'message': 'no key in event'}

        # Read object from S3
        try:
            s3 = boto3_client('s3')
            resp = s3.get_object(Bucket=bucket, Key=key)
            body = resp['Body'].read()
            payload = json.loads(body)
        except Exception as e:
            logger.exception('Failed to read raw payload from s3')
            return {'status': 'error', 'message': str(e)}

        rows = payload.get('rows', [])
        # Simplify rows
        processed_rows = []
        album_counts = {}
        for r in rows:
            track = {
                'track_name': r.get('track_name') or r.get('Name') or r.get('name'),
                'album_title': r.get('album_title') or r.get('Title') or r.get('Album')
            }
            processed_rows.append(track)
            album = track['album_title'] or 'UNKNOWN'
            album_counts[album] = album_counts.get(album, 0) + 1

        # Upload processed payload
        now_key = key.replace('raw/', 'processed/')
        processed_payload = {'processed_at': payload.get('fetched_at'), 'row_count': len(processed_rows), 'rows': processed_rows}
        try:
            if processed_bucket:
                s3.put_object(Bucket=processed_bucket, Key=now_key, Body=json.dumps(processed_payload).encode('utf-8'))
                processed_path = f's3://{processed_bucket}/{now_key}'
            else:
                # local fallback
                out_dir = os.environ.get('LOCAL_UPLOAD_DIR', 'build/local_uploads')
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, now_key.replace('/', '_'))
                with open(out_path, 'wb') as f:
                    f.write(json.dumps(processed_payload).encode('utf-8'))
                processed_path = out_path
        except Exception as e:
            logger.exception('Failed to upload processed payload')
            return {'status': 'error', 'message': str(e)}

        # Upload analytics summary
        analytics_key = now_key.replace('processed/', 'analytics/').replace('.json', '_summary.json')
        analytics_payload = {'generated_from': key, 'album_counts': album_counts}
        try:
            if analytics_bucket:
                s3.put_object(Bucket=analytics_bucket, Key=analytics_key, Body=json.dumps(analytics_payload).encode('utf-8'))
                analytics_path = f's3://{analytics_bucket}/{analytics_key}'
            else:
                out_dir = os.environ.get('LOCAL_UPLOAD_DIR', 'build/local_uploads')
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, analytics_key.replace('/', '_'))
                with open(out_path, 'wb') as f:
                    f.write(json.dumps(analytics_payload).encode('utf-8'))
                analytics_path = out_path
        except Exception as e:
            logger.exception('Failed to upload analytics payload')
            return {'status': 'error', 'message': str(e)}

        logger.info(f'Wrote processed payload to {processed_path} and analytics to {analytics_path}')
        return {'status': 'ok', 'processed_path': processed_path, 'analytics_path': analytics_path, 'rows': len(processed_rows)}

    s3 = boto3.client('s3')
    analytics_bucket = os.environ.get('ANALYTICS_BUCKET')
    if not analytics_bucket:
        raise RuntimeError('ANALYTICS_BUCKET environment variable must be set')

    records = event.get('Records', []) if isinstance(event, dict) else []
    # We'll process each record and write one transformed file per input
    results = []
    for rec in records:
        try:
            s3_info = rec.get('s3', {})
            bucket = s3_info.get('bucket', {}).get('name')
            key = s3_info.get('object', {}).get('key')
            if not bucket or not key:
                logger.warning('Skipping record with missing bucket/key')
                continue

            obj = s3.get_object(Bucket=bucket, Key=key)
            body = obj['Body'].read()
            payload = json.loads(body)
            rows = payload.get('rows', [])

            # Transform: select fields and rename
            transformed = []
            for r in rows:
                transformed.append({
                    'track_id': r.get('TrackId') or r.get('track_id') or r.get('TrackID'),
                    'track_name': r.get('Name') or r.get('track_name') or r.get('name'),
                    'album_title': r.get('Title') or r.get('album_title') or r.get('AlbumTitle'),
                    'composer': r.get('Composer'),
                    'milliseconds': r.get('Milliseconds'),
                    'unit_price': r.get('UnitPrice') or r.get('Unit_Price')
                })

            now = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')
            out_key = f'analytics/{now}/{key.split("/")[-1]}'
            out_body = json.dumps({'processed_at': now, 'row_count': len(transformed), 'rows': transformed}, default=str)
            s3.put_object(Bucket=analytics_bucket, Key=out_key, Body=out_body.encode('utf-8'))
            results.append({'input': f's3://{bucket}/{key}', 'output': f's3://{analytics_bucket}/{out_key}', 'rows': len(transformed)})

        except Exception as e:
            logger.exception('Error processing record')
            results.append({'error': str(e)})

    return {'status': 'ok', 'results': results}
