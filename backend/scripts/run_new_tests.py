#!/usr/bin/env python3
"""
Run newly created tests and check coverage.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_test(test_file, coverage_target):
    """Run a single test file with coverage."""
    cmd = [
        sys.executable,
        "-m", "pytest",
        test_file,
        "-v",
        f"--cov={coverage_target}",
        "--cov-report=term-missing",
        "--tb=short"
    ]

    print(f"\n{'='*80}")
    print(f"Running: {test_file}")
    print(f"{'='*80}")

    result = subprocess.run(cmd, cwd=str(Path(__file__).parent.parent))
    return result.returncode

def main():
    """Run all new tests."""
    backend_dir = Path(__file__).parent.parent

    new_tests = [
        ("tests/test_query_cache.py", "app.cache.query_cache"),
        ("tests/test_retrieval_orchestrator_comprehensive.py", "app.rag.retrieval_orchestrator"),
        ("tests/test_pii_anonymizer_comprehensive.py", "app.security.pii_anonymizer"),
        ("tests/test_parent_retriever_comprehensive.py", "app.rag.parent_retriever"),
    ]

    results = []

    for test_file, coverage_target in new_tests:
        test_path = backend_dir / test_file
        if not test_path.exists():
            print(f"Warning: {test_file} does not exist, skipping...")
            continue

        returncode = run_test(test_file, coverage_target)
        results.append((test_file, returncode))

    print(f"\n{'='*80}")
    print("Summary")
    print(f"{'='*80}")

    passed = 0
    failed = 0

    for test_file, returncode in results:
        status = "PASSED" if returncode == 0 else "FAILED"
        print(f"{test_file}: {status}")
        if returncode == 0:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    return 1 if failed > 0 else 0

if __name__ == "__main__":
    sys.exit(main())
