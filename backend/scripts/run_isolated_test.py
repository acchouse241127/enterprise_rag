#!/usr/bin/env python3
"""
Run tests in isolated subprocess to avoid numpy import conflicts.
"""

import subprocess
import sys
import os

def run_tests(test_file, coverage_target=None):
    """Run tests for a specific file."""
    cmd = [sys.executable, "-m", "pytest", test_file, "-v"]

    if coverage_target:
        cmd.extend([
            f"--cov={coverage_target}",
            "--cov-report=term-missing",
            "--cov-report=html"
        ])

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)) + "/..")
    return result.returncode

if __name__ == "__main__":
    test_file = sys.argv[1] if len(sys.argv) > 1 else None
    coverage_target = sys.argv[2] if len(sys.argv) > 2 else None

    if not test_file:
        print("Usage: python run_isolated_test.py <test_file> [coverage_target]")
        sys.exit(1)

    sys.exit(run_tests(test_file, coverage_target))
