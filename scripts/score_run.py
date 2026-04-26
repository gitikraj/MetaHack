"""
score_run.py – Run the full pipeline without API key and print plain-text scores.
Bypasses Rich rendering to avoid encoding issues.

Usage:
  python scripts/score_run.py
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ["USE_LLM"] = "false"

from runner import _load_cases, _build_agents, _build_memory
from evaluator import Evaluator
from schemas import AgentPrediction

async def run_all():
    cases = _load_cases("dataset/cases.json")
    memory = _build_memory(load=True)
    agents = _build_agents(memory=memory)
    evaluator = Evaluator()
    
    results = []
    for case in cases:
        log_r = await agents["log"].analyze(case.logs)
        code_r = await agents["code"].analyze(case.code)
        req_r = await agents["req"].analyze(case.requirements)
        fusion_r = await agents["fusion"].fuse(log_r, code_r, req_r)
        
        pred = AgentPrediction(
            case_id=case.case_id,
            flagged_logs=log_r.flagged_logs,
            flagged_code=code_r.flagged_code,
            flagged_requirements=req_r.flagged_requirements,
            attack_type=fusion_r.attack_type,
            confidence=fusion_r.confidence,
        )
        
        result = evaluator.grade(pred, case.known_truth)
        results.append((case.known_truth, pred, result))
    
    return results

results = asyncio.run(run_all())

# ── Aggregate stats ──────────────────────────────────
n = len(results)
rewards = [r.reward for _, _, r in results]
final_scores = [r.scores.final_score for _, _, r in results]
logs_scores = [r.scores.logs_score for _, _, r in results]
code_scores = [r.scores.code_score for _, _, r in results]
req_scores = [r.scores.requirements_score for _, _, r in results]
atk_scores = [r.scores.attack_type_score for _, _, r in results]
correct_attacks = sum(1 for _, _, r in results if r.correct_attack)
penalties = [r.penalties.total_penalty for _, _, r in results]

print()
print("=" * 65)
print("  AGGREGATE SCORES  (no API key  |  rule-based only)")
print("=" * 65)
print(f"  Cases evaluated  : {n}")
print(f"  Attack type acc  : {correct_attacks}/{n}  ({100*correct_attacks/n:.1f}%)")
print()
print(f"  Mean final score : {sum(final_scores)/n:.4f}")
print(f"  Mean reward      : {sum(rewards)/n:+.4f}")
print(f"  Mean penalty     : {sum(penalties)/n:.4f}")
print()
print(f"  Mean logs score  : {sum(logs_scores)/n:.4f}")
print(f"  Mean code score  : {sum(code_scores)/n:.4f}")
print(f"  Mean req score   : {sum(req_scores)/n:.4f}")
print(f"  Mean atk score   : {sum(atk_scores)/n:.4f}")
print()
print(f"  Best  reward     : {max(rewards):+.4f}")
print(f"  Worst reward     : {min(rewards):+.4f}")
print("=" * 65)
