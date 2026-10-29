"""Sequential login load check; concurrent load is a separate GO."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _helpers import api_test_context, create_test_user, login_as


def test_load_login_100_sequential_under_10_seconds():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "load-user", "secret123")
        started = time.perf_counter()
        for _ in range(100):
            login_as(opener, base_url, "load-user", "secret123")
        elapsed = time.perf_counter() - started

    assert elapsed < 10, (
        f"100 logins séquentiels ont pris {elapsed:.2f} s (limite : 10 s)"
    )
