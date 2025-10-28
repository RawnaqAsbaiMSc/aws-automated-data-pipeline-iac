import os
import subprocess
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(__file__))
GET_SCRIPT = os.path.join(ROOT, 'scripts/get_chinook.sh')
DB_PATH = os.path.join(ROOT, 'data/chinook.db')
LOCAL_RUN = os.path.join(ROOT, 'src/ingestion_lambda/local_run.py')

@pytest.fixture(scope='session')
def ensure_chinook():
    if not os.path.isfile(DB_PATH):
        # attempt to download
        subprocess.check_call(['bash', GET_SCRIPT])
    assert os.path.isfile(DB_PATH), 'Chinook DB missing'
    return DB_PATH

def test_ingest_chinook(ensure_chinook):
    # Run the local runner and assert it returns a dict-like JSON with row_count
    res = subprocess.check_output([sys.executable, LOCAL_RUN], universal_newlines=True)
    assert res, 'No output from local runner'
    # basic check: should contain "row_count"
    assert 'row_count' in res
