#!/usr/bin/env python
"""Extract key coverage metrics from JSON file."""
import json
import sys

if len(sys.argv) > 1:
    file_path = sys.argv[1]
else:
    file_path = 'coverage_final.json'

with open(file_path, 'r') as f:
    data = json.load(f)

totals = data['totals']
print(f"总语句数: {totals['num_statements']}")
print(f"已覆盖: {totals['covered_lines']}")
print(f"覆盖率: {totals['percent_covered']:.1f}%")
print(f"缺失: {totals['num_statements'] - totals['covered_lines']}")
