"""Script to run query_cache tests separately to avoid numpy conflicts."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest

# Run only query_cache tests
if __name__ == "__main__":
    sys.exit(pytest.main([
        "tests/test_query_cache.py",
        "-v",
        "--no-header",
        "--tb=short",
        "-x"
    ]))
