"""Analyze test coverage and generate report."""
import json
from pathlib import Path


def analyze_coverage(json_path: Path, threshold: float = 80.0):
    """Analyze coverage report."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_percent = data['totals']['percent_covered']
    print(f"\n{'='*60}")
    print(f"Total Coverage: {total_percent:.1f}%")
    print(f"{'='*60}\n")

    # Extract module coverage
    files = data.get('files', {})
    modules = []

    for file_path, file_data in files.items():
        # Get file name (remove app/ prefix)
        file_name = file_path.replace('app\\', '').replace('/', '\\').split('\\')[-1]
        percent = file_data['summary']['percent_covered']
        covered = file_data['summary']['covered_lines']
        total = file_data['summary']['num_statements']

        modules.append({
            'name': file_name,
            'percent': percent,
            'covered': covered,
            'total': total,
            'missing': total - covered
        })

    # Sort by coverage
    modules.sort(key=lambda x: x['percent'])

    # Show modules below threshold
    low_coverage = [m for m in modules if m['percent'] < threshold]
    high_coverage = [m for m in modules if m['percent'] >= threshold]

    if low_coverage:
        print(f"[X] Modules below {threshold}% (need more tests):")
        print(f"{'Module Name':<40} {'Coverage':<10} {'Covered/Total':<15}")
        print("-" * 70)
        for m in low_coverage:
            print(f"{m['name']:<40} {m['percent']:<10.1f}% {m['covered']:>4}/{m['total']:<4}")
        print()

    # Show good modules
    print(f"[OK] Modules >= {threshold}%:")
    print(f"{'Module Name':<40} {'Coverage':<10} {'Covered/Total':<15}")
    print("-" * 70)
    for m in high_coverage:
        marker = "[100]" if m['percent'] == 100 else "[OK]"
        print(f"{marker} {m['name']:<35} {m['percent']:<10.1f}% {m['covered']:>4}/{m['total']:<4}")

    # Statistics
    avg_coverage = sum(m['percent'] for m in modules) / len(modules)
    below_threshold = len(low_coverage)
    above_threshold = len(high_coverage)

    print(f"\n{'='*60}")
    print(f"Total Modules: {len(modules)}")
    print(f"Average Coverage: {avg_coverage:.1f}%")
    print(f"Coverage >= {threshold}%: {above_threshold} modules")
    print(f"Coverage < {threshold}%: {below_threshold} modules")
    print(f"{'='*60}\n")

    # Generate priority list
    print("[LIST] Test Coverage Priority:")
    print(f"{'Priority':<10} {'Module Name':<40} {'Coverage':<10}")
    print("-" * 60)

    # P0: < 50%
    p0 = [m for m in low_coverage if m['percent'] < 50]
    for m in p0:
        print(f"{'P0':<10} {m['name']:<40} {m['percent']:<10.1f}%")

    # P1: 50-70%
    p1 = [m for m in low_coverage if 50 <= m['percent'] < 70]
    for m in p1:
        print(f"{'P1':<10} {m['name']:<40} {m['percent']:<10.1f}%")

    # P2: 70-80%
    p2 = [m for m in low_coverage if 70 <= m['percent'] < 80]
    for m in p2:
        print(f"{'P2':<10} {m['name']:<40} {m['percent']:<10.1f}%")

    return {
        'total_percent': total_percent,
        'avg_percent': avg_coverage,
        'below_threshold': below_threshold,
        'above_threshold': above_threshold,
        'p0_count': len(p0),
        'p1_count': len(p1),
        'p2_count': len(p2),
    }


if __name__ == "__main__":
    import sys

    json_path = Path("coverage_baseline.json")
    if not json_path.exists():
        print(f"[ERROR] File not found: {json_path}")
        sys.exit(1)

    threshold = 80.0
    if len(sys.argv) > 1:
        threshold = float(sys.argv[1])

    analyze_coverage(json_path, threshold)
