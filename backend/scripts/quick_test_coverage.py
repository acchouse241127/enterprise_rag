"""Quick test runner for P0 modules."""
import subprocess
import sys
import json

test_files = [
    "tests/test_retrieval_orchestrator.py",
    "tests/test_pii_anonymizer.py",
]

def run_tests():
    """Run tests and collect results."""
    cmd = [
        sys.executable, "-m", "pytest",
        *test_files,
        "-v",
        "--tb=short",
        "-m", "not integration and not slow and not llm",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=json:coverage_quick.json",
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # Read coverage if available
    try:
        with open("coverage_quick.json") as f:
            cov_data = json.load(f)
            print(f"\n{'='*60}")
            print(f"Total Coverage: {cov_data['totals']['percent_covered']:.1f}%")
            print(f"Lines Covered: {cov_data['totals']['covered_lines']}")
            print(f"Total Lines: {cov_data['totals']['num_statements']}")
            
            # Check specific modules
            modules = {
                "app/rag/retrieval_orchestrator.py": "Retrieval Orchestrator",
                "app/security/pii_anonymizer.py": "PII Anonymizer",
            }
            
            print(f"\n{'='*60}")
            print("P0 Module Coverage:")
            for file, name in modules.items():
                if file in cov_data["files"]:
                    file_cov = cov_data["files"][file]
                    print(f"  {name}: {file_cov['summary']['percent_covered']:.1f}%")
    except Exception as e:
        print(f"Could not read coverage: {e}")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
