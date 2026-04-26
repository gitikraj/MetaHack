"""
evaluator.py – Grader / Evaluator System

Public API
──────────
  evaluator = Evaluator()

  # Single prediction:
  result: EvaluationResult = evaluator.grade(prediction, known_truth)

  # Batch:
  metrics: BenchmarkMetrics = evaluator.benchmark(predictions, truths)

Scoring
───────
  logs_score         = list_match_score(pred_logs, truth_logs)
  code_score         = list_match_score(pred_code, truth_code)
  requirements_score = list_match_score(pred_reqs, truth_reqs)
  attack_type_score  = score_attack_type(pred_type, truth_type)

  final_score = 0.30*logs + 0.25*code + 0.20*req + 0.25*attack

  penalty = 0.25*false_positives + 0.25*(1 - attack_score)

  reward = final_score * (1 - penalty)  ∈ [0, 1]
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from schemas import (
    AgentPrediction,
    BenchmarkMetrics,
    EvaluationResult,
    EvaluationScores,
    KnownTruth,
    PenaltyBreakdown,
)
from utils import get_embedding_engine, list_match_score, setup_logging

logger = setup_logging("evaluator")

def score_attack_type(predicted: str, truth: str, engine: Any = None) -> float:
    """Return [0, 1] score for attack type prediction."""
    from utils import cosine_similarity
    
    if predicted.lower().strip() == truth.lower().strip():
        return 1.0
    
    if engine is None:
        engine = get_embedding_engine()
    
    try:
        pred_emb = engine.encode(predicted.lower())
        truth_emb = engine.encode(truth.lower())
        sim = cosine_similarity(pred_emb, truth_emb)
        return max(0.0, min(1.0, sim))
    except:
        return 0.0

class Evaluator:
    """Stateless evaluator with semantic scoring via SentenceTransformers."""

    def __init__(self) -> None:
        self._engine = get_embedding_engine()

    # ── Single-case grading ───────────────────────────────────────────────────
    def grade(
        self,
        prediction: AgentPrediction,
        truth: KnownTruth,
    ) -> EvaluationResult:
        """Compute all scores, penalties, and reward for one prediction."""
        
        # Component scores
        logs_score = self.score_logs(prediction.flagged_logs, truth.flagged_logs)
        code_score = self.score_code(prediction.flagged_code, truth.flagged_code)
        req_score = self.score_requirements(prediction.flagged_requirements, truth.flagged_requirements)
        attack_score = self.score_attack(prediction.attack_type, truth.attack_type)
        
        # Aggregate score
        scores = EvaluationScores(
            logs_score=logs_score,
            code_score=code_score,
            requirements_score=req_score,
            attack_type_score=attack_score,
        )
        scores.compute_final()
        
        # False positives and penalties
        false_positives_logs = len([l for l in prediction.flagged_logs if l not in truth.flagged_logs])
        false_positives_code = len([c for c in prediction.flagged_code if c not in truth.flagged_code])
        false_positives_total = (false_positives_logs + false_positives_code) / max(1, len(prediction.flagged_logs) + len(prediction.flagged_code)) if (len(prediction.flagged_logs) + len(prediction.flagged_code)) > 0 else 0
        
        penalties = PenaltyBreakdown(
            false_positives=min(1.0, false_positives_total),
            wrong_type=1.0 - attack_score,
        )
        penalties.compute_total()
        
        # Reward calculation
        reward = scores.final_score * (1 - penalties.total_penalty)
        
        result = EvaluationResult(
            case_id=prediction.case_id,
            scores=scores,
            penalties=penalties,
            reward=max(0.0, min(1.0, reward)),
            correct_attack=abs(attack_score - 1.0) < 0.01,
            missed_findings={
                "logs": [l for l in truth.flagged_logs if l not in prediction.flagged_logs],
                "code": [c for c in truth.flagged_code if c not in prediction.flagged_code],
                "requirements": [r for r in truth.flagged_requirements if r not in prediction.flagged_requirements],
            },
            false_positives_detail={
                "logs": [l for l in prediction.flagged_logs if l not in truth.flagged_logs],
                "code": [c for c in prediction.flagged_code if c not in truth.flagged_code],
            },
        )
        return result

    # ── Per-component scoring ───────────────────────────────────────────────
    def score_logs(
        self,
        pred_logs: List[str],
        truth_logs: List[str],
    ) -> float:
        return round(list_match_score(pred_logs, truth_logs, self._engine), 4)

    def score_code(
        self,
        pred_code: List[str],
        truth_code: List[str],
    ) -> float:
        return round(list_match_score(pred_code, truth_code, self._engine), 4)

    def score_requirements(
        self,
        pred_reqs: List[str],
        truth_reqs: List[str],
    ) -> float:
        return round(list_match_score(pred_reqs, truth_reqs, self._engine), 4)

    def score_attack(self, pred_type: str, truth_type: str) -> float:
        return round(score_attack_type(pred_type, truth_type, self._engine), 4)

    # ── Batch benchmark ───────────────────────────────────────────────────────
    def benchmark(
        self,
        predictions: List[AgentPrediction],
        truths: List[KnownTruth],
    ) -> BenchmarkMetrics:
        """Evaluate all predictions and aggregate BenchmarkMetrics."""
        
        results = [self.grade(p, t) for p, t in zip(predictions, truths)]
        
        metrics = BenchmarkMetrics(
            total_cases=len(results),
            mean_reward=float(np.mean([r.reward for r in results])),
            mean_final_score=float(np.mean([r.scores.final_score for r in results])),
            attack_type_accuracy=sum(1 for r in results if r.correct_attack) / len(results) if results else 0.0,
            mean_logs_score=float(np.mean([r.scores.logs_score for r in results])),
            mean_code_score=float(np.mean([r.scores.code_score for r in results])),
            mean_requirements_score=float(np.mean([r.scores.requirements_score for r in results])),
            all_rewards=[r.reward for r in results],
            all_final_scores=[r.scores.final_score for r in results],
        )
        
        return metrics

    # ── Explainability report ─────────────────────────────────────────────────
    def explain(
        self,
        prediction: AgentPrediction,
        truth: KnownTruth,
        result: Optional[EvaluationResult] = None,
    ) -> Dict[str, Any]:
        """Return a structured explanation of the scoring for a single case."""
        if result is None:
            result = self.grade(prediction, truth)
        
        return {
            "case_id": prediction.case_id,
            "prediction": {
                "attack_type": prediction.attack_type,
                "flagged_logs": prediction.flagged_logs,
                "flagged_code": prediction.flagged_code,
                "flagged_requirements": prediction.flagged_requirements,
            },
            "truth": {
                "attack_type": truth.attack_type,
                "flagged_logs": truth.flagged_logs,
                "flagged_code": truth.flagged_code,
                "flagged_requirements": truth.flagged_requirements,
            },
            "scores": result.scores.model_dump(),
            "penalties": result.penalties.model_dump(),
            "reward": result.reward,
            "correct_attack": result.correct_attack,
            "missed_findings": result.missed_findings,
            "false_positives": result.false_positives_detail,
        }
