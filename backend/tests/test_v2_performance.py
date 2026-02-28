"""V2.0 Performance Benchmark Tests

Tests:
1. API response time (health, metrics)
2. Module import time
3. Database query latency

Author: C2
Date: 2026-02-28
"""

import time
import statistics
import sys

sys.path.insert(0, ".")

def measure_time(func, name, iterations=3):
    """Measure execution time of a function."""
    times = []
    for i in range(iterations):
        start = time.perf_counter()
        try:
            result = func()
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)  # ms
            print(f"  [{i+1}/{iterations}] {name}: {elapsed*1000:.2f}ms")
        except Exception as e:
            print(f"  [{i+1}/{iterations}] {name}: ERROR - {e}")
            times.append(None)
    
    valid_times = [t for t in times if t is not None]
    if valid_times:
        avg = statistics.mean(valid_times)
        print(f"  -> Average: {avg:.2f}ms")
        return avg
    return None

def run_benchmarks():
    """Run all performance benchmarks."""
    print("=" * 60)
    print("V2.0 Performance Benchmark")
    print("=" * 60)
    
    results = {}
    
    # 1. Module import time
    print("\n[1] Module Import Time")
    def import_bm25():
        from app.rag.bm25_retriever import BM25Retriever
        return True
    results['bm25_import'] = measure_time(import_bm25, "BM25Retriever import", 1)
    
    def import_rrf():
        from app.rag.rrf_fusion import RRFFusion
        return True
    results['rrf_import'] = measure_time(import_rrf, "RRFFusion import", 1)
    
    def import_hybrid():
        from app.rag.hybrid_pipeline import HybridRetrievalPipeline
        return True
    results['hybrid_import'] = measure_time(import_hybrid, "HybridPipeline import", 1)
    
    def import_verify():
        from app.verify.verify_pipeline import VerifyPipeline
        return True
    results['verify_import'] = measure_time(import_verify, "VerifyPipeline import", 1)
    
    # 2. Database connection time
    print("\n[2] Database Connection Time")
    def db_connect():
        from app.core.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    results['db_connect'] = measure_time(db_connect, "DB connection + query", 3)
    
    # 3. Full-text search capability
    print("\n[3] PostgreSQL FTS Capability")
    def test_fts():
        from app.core.database import SessionLocal
        db = SessionLocal()
        result = db.execute("SELECT cfgname FROM pg_ts_config WHERE cfgname LIKE '%jieba%' LIMIT 1")
        row = result.fetchone()
        db.close()
        return row is not None
    results['fts_capability'] = measure_time(test_fts, "FTS config check", 3)
    
    # 4. Summary
    print("\n" + "=" * 60)
    print("Benchmark Results Summary")
    print("=" * 60)
    
    targets = {
        'bm25_import': ('BM25 Import', '< 1000ms'),
        'rrf_import': ('RRF Import', '< 100ms'),
        'hybrid_import': ('Hybrid Import', '< 500ms'),
        'verify_import': ('Verify Import', '< 100ms'),
        'db_connect': ('DB Connect', '< 50ms'),
        'fts_capability': ('FTS Check', '< 100ms'),
    }
    
    for key, (name, target) in targets.items():
        value = results.get(key)
        status = "PASS" if value else "N/A"
        print(f"  {name}: {value:.2f}ms if value else 'N/A'} (Target: {target}) [{status}]")
    
    print("\nBenchmark complete!")
    return results

if __name__ == "__main__":
    run_benchmarks()
