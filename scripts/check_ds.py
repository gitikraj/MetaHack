"""
check_ds.py – Check dataset integrity and structure.

Usage:
  python scripts/check_ds.py
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

CASES_FILE = Path("dataset/cases.json")

if CASES_FILE.exists():
    d = json.load(open(CASES_FILE, encoding="utf-8"))
    print(f"Loaded {len(d)} cases from {CASES_FILE}")
    print()
    
    # Check structure
    required_fields = ["case_id", "logs", "requirements", "code", "known_truth"]
    required_truth = ["attack_type", "flagged_logs", "flagged_code", "flagged_requirements"]
    
    valid_count = 0
    for i, c in enumerate(d):
        missing = [f for f in required_fields if f not in c]
        if missing:
            print(f"Case {i}: Missing fields {missing}")
            continue
        
        truth = c.get("known_truth", {})
        missing_truth = [f for f in required_truth if f not in truth]
        if missing_truth:
            print(f"Case {i}: Missing truth fields {missing_truth}")
            continue
        
        valid_count += 1
    
    print(f"Valid cases: {valid_count}/{len(d)}")
else:
    print(f"Dataset file not found: {CASES_FILE}")
    print("Creating empty dataset...")
    os.makedirs("dataset", exist_ok=True)
    with open(CASES_FILE, "w") as f:
        json.dump([], f)
    print("Empty dataset created at dataset/cases.json")
