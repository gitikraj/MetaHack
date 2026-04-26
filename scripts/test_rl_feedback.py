"""
test_rl_feedback.py – Test RL feedback loop on a subset of cases.

Shows how the PolicyState evolves as the system learns from errors.

Usage:
  python scripts/test_rl_feedback.py
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
from schemas import AgentPrediction, PolicyState

# ── Config ────────────────────────────────────────────────────────
TEST_CASES = 5  # Number of test cases
SEP = "=" * 75
THIN = "-" * 75

async def run_with_rl_feedback():
    cases_all = _load_cases("dataset/cases.json")
    cases = cases_all[:min(TEST_CASES, len(cases_all))]
    
    if not cases:
        print("No cases found in dataset/cases.json")
        return
    
    memory = _build_memory(load=False)
    policy = PolicyState()
    agents = _build_agents(policy=policy, memory=memory)
    evaluator = Evaluator()
    
    print(SEP)
    print(f"  RL Feedback Test: Running on {len(cases)} cases")
    print(SEP)
    
    for episode, case in enumerate(cases, 1):
        print(f"\n[Episode {episode}] Case ID: {case.case_id}")
        print(THIN)
        
        # Run agents
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
        
        # Evaluate
        result = evaluator.grade(pred, case.known_truth)
        
        print(f"  Predicted attack: {pred.attack_type}")
        print(f"  True attack:      {case.known_truth.attack_type}")
        print(f"  Correct:          {'✓' if result.correct_attack else '✗'}")
        print(f"  Reward:           {result.reward:.3f}")
        print(f"  Score (final):    {result.scores.final_score:.3f}")
        
        # Critique and update policy
        critic_output = await agents["critic"].critique(pred, case.known_truth, result)
        
        if critic_output.parameter_adjustments:
            print(f"\n  Policy adjustments:")
            for param, delta in critic_output.parameter_adjustments.items():
                old_val = getattr(policy, param)
                new_val = old_val + delta
                print(f"    {param}: {old_val:.4f} → {new_val:.4f}")
                setattr(policy, param, new_val)
        
        print(f"\n  Current policy state:")
        _print_policy(policy)
    
    print(SEP)

def _print_policy(p: PolicyState):
    print(f"    log_sensitivity      : {p.log_sensitivity:.4f}")
    print(f"    code_sensitivity     : {p.code_sensitivity:.4f}")
    print(f"    req_sensitivity      : {p.req_sensitivity:.4f}")
    print(f"    fusion_temperature   : {p.fusion_temperature:.4f}")
    print(f"    confidence_threshold : {p.confidence_threshold:.4f}")
    print(f"    iteration            : {p.iteration}")

asyncio.run(run_with_rl_feedback())
