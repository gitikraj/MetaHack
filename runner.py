"""
runner.py – Main orchestrator for the CyberMultiAgent platform.

Modes
─────
  python runner.py --mode run        # Run all 20 cases, print results
  python runner.py --mode train      # Train PPO agent for N timesteps
  python runner.py --mode bench      # Benchmark and show metrics
  python runner.py --mode demo       # Demo single case with full output
  python runner.py --case case_001   # Run specific case by ID

Environment variables
─────────────────────
  OPENAI_API_KEY   – enables LLM-enhanced agents
  USE_LLM          – "true"/"false" override
  MEMORY_DIR       – directory for FAISS memory
  CHECKPOINT_DIR   – directory for RL checkpoints
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

# ── Lazy imports to allow partial runs without all deps ───────────────────────
def _load_cases(path: str = "dataset/cases.json") -> List[Any]:
    from schemas import IncidentCase, KnownTruth
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    cases = []
    for item in raw:
        truth_data = item.pop("known_truth", {})
        truth = KnownTruth(**truth_data)
        cases.append(IncidentCase(known_truth=truth, **item))
    return cases

def _build_agents(policy=None, memory=None) -> Dict[str, Any]:
    from schemas import PolicyState
    from agents.log_agent import LogIntelligenceAgent
    from agents.req_agent import RequirementsSecurityAgent
    from agents.code_agent import SecureCodeAgent
    from agents.fusion_agent import ThreatFusionAgent
    from agents.critic_agent import RLCriticAgent

    p = policy or PolicyState()
    return {
        "log":    LogIntelligenceAgent(policy=p),
        "req":    RequirementsSecurityAgent(policy=p),
        "code":   SecureCodeAgent(policy=p),
        "fusion": ThreatFusionAgent(policy=p),
        "critic": RLCriticAgent(policy=p, memory=memory),
    }

def _build_memory(load: bool = True) -> Any:
    from rl.memory import FAISSEpisodicMemory
    memory = FAISSEpisodicMemory()
    mem_dir = os.getenv("MEMORY_DIR", "./memory_store")
    if load and os.path.exists(os.path.join(mem_dir, "episodes.pkl")):
        memory.load(mem_dir)
    return memory

# ─────────────────────────────────────────────────────────────────────────────
# solve() – the single-case solver (OpenEnv-compatible)
# ─────────────────────────────────────────────────────────────────────────────
def solve(case: Any, agents: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run all agents on a single case and return the prediction dict.

    Parameters
    ----------
    case    : IncidentCase (or raw dict conforming to IncidentCase schema)
    agents  : Optional pre-built agents dict

    Returns
    -------
    {
      "flagged_logs": [...],
      "flagged_code": [...],
      "flagged_requirements": [...],
      "attack_type": "..."
    }
    """
    from schemas import IncidentCase, KnownTruth
    if isinstance(case, dict):
        truth_data = case.pop("known_truth", {})
        truth = KnownTruth(**truth_data)
        case = IncidentCase(known_truth=truth, **case)

    if agents is None:
        agents = _build_agents()

    async def _run():
        log_r = await agents["log"].analyze(case.logs)
        code_r = await agents["code"].analyze(case.code)
        req_r = await agents["req"].analyze(case.requirements)
        fusion_r = await agents["fusion"].fuse(log_r, code_r, req_r)
        
        return {
            "case_id": case.case_id,
            "flagged_logs": log_r.flagged_logs,
            "flagged_code": code_r.flagged_code,
            "flagged_requirements": req_r.flagged_requirements,
            "attack_type": fusion_r.attack_type,
            "confidence": fusion_r.confidence,
        }

    return asyncio.run(_run())

# ─────────────────────────────────────────────────────────────────────────────
# grade() – the evaluator (OpenEnv-compatible)
# ─────────────────────────────────────────────────────────────────────────────
def grade(prediction: Dict[str, Any], truth: Any) -> Dict[str, Any]:
    """
    Score a prediction against ground truth.

    Parameters
    ----------
    prediction : dict output from solve()
    truth      : KnownTruth or dict

    Returns
    -------
    {"scores": {...}, "reward": float}
    """
    from schemas import AgentPrediction, KnownTruth
    from evaluator import Evaluator

    if isinstance(truth, dict):
        truth = KnownTruth(**truth)

    pred_obj = AgentPrediction(
        case_id=prediction.get("case_id", ""),
        flagged_logs=prediction.get("flagged_logs", []),
        flagged_code=prediction.get("flagged_code", []),
        flagged_requirements=prediction.get("flagged_requirements", []),
        attack_type=prediction.get("attack_type", ""),
    )
    ev = Evaluator().grade(pred_obj, truth)
    return {
        "scores": ev.scores.model_dump(),
        "penalties": ev.penalties.model_dump(),
        "reward": ev.reward,
        "correct_attack": ev.correct_attack,
    }

# ─────────────────────────────────────────────────────────────────────────────
# Runners
# ─────────────────────────────────────────────────────────────────────────────
async def _async_run_all(
    cases: List[Any],
    agents: Dict[str, Any],
    evaluator: Any,
    show_details: bool = True,
) -> List[Dict[str, Any]]:
    results = []
    for case in cases:
        log_r = await agents["log"].analyze(case.logs)
        code_r = await agents["code"].analyze(case.code)
        req_r = await agents["req"].analyze(case.requirements)
        fusion_r = await agents["fusion"].fuse(log_r, code_r, req_r)
        
        pred = {
            "case_id": case.case_id,
            "flagged_logs": log_r.flagged_logs,
            "flagged_code": code_r.flagged_code,
            "flagged_requirements": req_r.flagged_requirements,
            "attack_type": fusion_r.attack_type,
            "confidence": fusion_r.confidence,
        }
        
        ev = evaluator.grade(
            AgentPrediction(
                case_id=case.case_id,
                flagged_logs=pred["flagged_logs"],
                flagged_code=pred["flagged_code"],
                flagged_requirements=pred["flagged_requirements"],
                attack_type=pred["attack_type"],
            ),
            case.known_truth
        )
        
        results.append({
            "case_id": case.case_id,
            "prediction": pred,
            "eval_result": ev,
        })
    
    return results

def run_mode(args: argparse.Namespace) -> None:
    from agents import LogIntelligenceAgent
    from evaluator import Evaluator
    
    memory = _build_memory(load=True)
    cases = _load_cases(args.dataset)
    agents = _build_agents(memory=memory)
    evaluator = Evaluator()

    if args.case:
        cases = [c for c in cases if c.case_id == args.case]

    results = asyncio.run(_async_run_all(cases, agents, evaluator))

    # Print summary
    print(f"\n{'='*60}")
    print(f"Ran {len(results)} cases")
    for r in results:
        print(f"{r['case_id']}: {r['eval_result'].scores.final_score:.3f}")
    print(f"{'='*60}\n")

    # Save memory
    mem_dir = os.getenv("MEMORY_DIR", "./memory_store")
    memory.save(mem_dir)

def train_mode(args: argparse.Namespace) -> None:
    from rl.train import RLTrainer
    from evaluator import Evaluator
    from schemas import PolicyState

    memory = _build_memory(load=True)
    cases = _load_cases(args.dataset)
    policy = PolicyState()
    agents = _build_agents(policy=policy, memory=memory)
    evaluator = Evaluator()

    ckpt_dir = os.getenv("CHECKPOINT_DIR", "./checkpoints")
    trainer = RLTrainer(
        cases=cases,
        agents=agents,
        evaluator=evaluator,
        policy=policy,
        checkpoint_dir=ckpt_dir,
    )

    print("Training PPO agent...")
    trainer.train(total_timesteps=args.timesteps)
    trainer.save(ckpt_dir)
    print(f"Training complete. Checkpoint saved → {ckpt_dir}")

    memory.save(os.getenv("MEMORY_DIR", "./memory_store"))

def bench_mode(args: argparse.Namespace) -> None:
    from evaluator import Evaluator
    from schemas import AgentPrediction

    memory = _build_memory(load=True)
    cases = _load_cases(args.dataset)
    agents = _build_agents(memory=memory)
    evaluator = Evaluator()

    results = asyncio.run(_async_run_all(cases, agents, evaluator, show_details=False))
    
    print(f"\n{'='*60}")
    print(f"Benchmark Results ({len(results)} cases)")
    print(f"{'='*60}")
    rewards = [r["eval_result"].reward for r in results]
    print(f"Mean reward: {np.mean(rewards):.4f}")
    print(f"Max reward:  {max(rewards):.4f}")
    print(f"Min reward:  {min(rewards):.4f}")
    print(f"{'='*60}\n")

def demo_mode(args: argparse.Namespace) -> None:
    """Run a single case with verbose output."""
    from evaluator import Evaluator

    memory = _build_memory(load=False)
    cases = _load_cases(args.dataset)

    if args.case:
        selected = next((c for c in cases if c.case_id == args.case), None)
    else:
        selected = cases[0]

    agents = _build_agents(memory=memory)
    evaluator = Evaluator()

    results = asyncio.run(_async_run_all([selected], agents, evaluator))
    r = results[0]
    print(f"\nCase: {r['case_id']}")
    print(f"Attack: {r['prediction']['attack_type']}")
    print(f"Confidence: {r['prediction']['confidence']:.2f}")
    print(f"Score: {r['eval_result'].scores.final_score:.3f}")
    print(f"Reward: {r['eval_result'].reward:.3f}\n")

# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    import numpy as np
    
    parser = argparse.ArgumentParser(
        description="CyberMultiAgent Platform – next-gen AI SOC with RL"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="run",
        choices=["run", "train", "bench", "demo"],
        help="Execution mode",
    )
    parser.add_argument("--case", type=str, default=None, help="Run specific case ID")
    parser.add_argument(
        "--dataset",
        type=str,
        default="dataset/cases.json",
        help="Path to cases JSON",
    )
    parser.add_argument(
        "--timesteps",
        type=int,
        default=100,
        help="PPO training timesteps (train mode)",
    )
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    if args.mode == "run":
        run_mode(args)
    elif args.mode == "train":
        train_mode(args)
    elif args.mode == "bench":
        bench_mode(args)
    elif args.mode == "demo":
        demo_mode(args)

if __name__ == "__main__":
    main()
