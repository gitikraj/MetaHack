"""
rl/reward.py – Reward and penalty computation.

Improved scoring formula
────────────────────────
final_score = 0.30 * logs_score
            + 0.25 * code_score
            + 0.20 * requirements_score
            + 0.25 * attack_type_score

penalty = 0.25 * false_positives_avg      (only FPs — recall is in F1)
        + 0.25 * (1 - attack_type_score)  (proportional, not binary)

reward = final_score * (1 - penalty)
"""
from __future__ import annotations

from typing import List, Optional

from schemas import (
    AgentPrediction,
    EvaluationResult,
    EvaluationScores,
    KnownTruth,
    PenaltyBreakdown,
)
from utils import (
    EmbeddingEngine,
    cosine_similarity,
    get_embedding_engine,
    list_match_score,
    setup_logging,
)

logger = setup_logging("rl.reward")

# ─────────────────────────────────────────────────────────────────────────────
# Attack type scoring helpers
# ─────────────────────────────────────────────────────────────────────────────
_SEMANTIC_NEAR_MATCHES = {
    frozenset({"credential stuffing", "phishing compromise"}): 0.60,
    frozenset({"ransomware", "crypto miner"}): 0.55,
    frozenset({"sql injection", "remote code execution"}): 0.45,
    frozenset({"privilege escalation", "lateral movement"}): 0.50,
    frozenset({"insider threat", "data exfiltration"}): 0.65,
    frozenset({"supply chain compromise", "remote code execution"}): 0.40,
}

def score_attack_type(
    predicted: str,
    truth: str,
    engine: Optional[EmbeddingEngine] = None,
) -> float:
    """Return [0, 1] score for the attack type prediction."""
    if predicted.lower().strip() == truth.lower().strip():
        return 1.0
    
    # Check semantic near-matches
    for match_pair, similarity in _SEMANTIC_NEAR_MATCHES.items():
        if {predicted.lower(), truth.lower()} == {s.lower() for s in match_pair}:
            return similarity
    
    # Embedding-based scoring
    if engine is None:
        engine = get_embedding_engine()
    
    try:
        pred_emb = engine.encode(predicted.lower())
        truth_emb = engine.encode(truth.lower())
        sim = cosine_similarity(pred_emb, truth_emb)
        return max(0.0, min(1.0, sim))
    except:
        return 0.0

# ─────────────────────────────────────────────────────────────────────────────
# Penalty computation
# ─────────────────────────────────────────────────────────────────────────────
def compute_penalty(
    pred: AgentPrediction,
    truth: KnownTruth,
    attack_score: float = 0.0,
) -> PenaltyBreakdown:
    """
    Compute penalty breakdown.
    Penalties only from false positives and wrong attack type.
    """
    false_positives_logs = len([l for l in pred.flagged_logs if l not in truth.flagged_logs])
    false_positives_code = len([c for c in pred.flagged_code if c not in truth.flagged_code])
    
    total_flagged = len(pred.flagged_logs) + len(pred.flagged_code)
    if total_flagged > 0:
        fp_ratio = (false_positives_logs + false_positives_code) / total_flagged
    else:
        fp_ratio = 0.0
    
    breakdown = PenaltyBreakdown(
        false_positives=min(1.0, fp_ratio),
        wrong_type=1.0 - attack_score,
    )
    breakdown.compute_total()
    return breakdown

# ─────────────────────────────────────────────────────────────────────────────
# Main reward function
# ─────────────────────────────────────────────────────────────────────────────
def compute_reward(
    pred: AgentPrediction,
    truth: KnownTruth,
    engine: Optional[EmbeddingEngine] = None,
) -> EvaluationResult:
    """
    Compute evaluation result and reward for a prediction.
    Integrates scoring, penalties, and final reward.
    """
    if engine is None:
        engine = get_embedding_engine()
    
    # Component scores
    logs_score = list_match_score(pred.flagged_logs, truth.flagged_logs, engine)
    code_score = list_match_score(pred.flagged_code, truth.flagged_code, engine)
    req_score = list_match_score(pred.flagged_requirements, truth.flagged_requirements, engine)
    attack_score = score_attack_type(pred.attack_type, truth.attack_type, engine)
    
    # Aggregate score
    scores = EvaluationScores(
        logs_score=logs_score,
        code_score=code_score,
        requirements_score=req_score,
        attack_type_score=attack_score,
    )
    scores.compute_final()
    
    # Penalties
    penalties = compute_penalty(pred, truth, attack_score)
    
    # Reward
    reward = scores.final_score * (1 - penalties.total_penalty)
    reward = max(0.0, min(1.0, reward))
    
    return EvaluationResult(
        case_id=pred.case_id,
        scores=scores,
        penalties=penalties,
        reward=reward,
        correct_attack=abs(attack_score - 1.0) < 0.01,
    )
