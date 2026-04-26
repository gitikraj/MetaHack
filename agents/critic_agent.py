"""
agents/critic_agent.py – RL Critic / Self-Improvement Agent

Responsibilities after each evaluation:
  1. Identify missed findings (false negatives per category)
  2. Identify false positives
  3. Compute reward and penalty breakdown
  4. Generate policy update recommendations
  5. Store episode in memory
  6. Update parameter adjustments
  7. Run self-reflection loop: simulate what better parameters would have done
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from schemas import (
    AgentPrediction,
    CriticOutput,
    EvaluationResult,
    KnownTruth,
    PolicyState,
)
from utils import get_llm_client, setup_logging

logger = setup_logging("critic_agent")

CRITIC_SYSTEM_PROMPT = """You are an autonomous RL critic agent embedded in a cybersecurity SOC.
After each incident evaluation you must:
1. Identify what the detection system missed and why.
2. Identify false positives and their root cause.
3. Propose specific parameter adjustments to improve future performance.
4. Write a concise self-reflection for learning.

Return ONLY valid JSON:
{
  "policy_update": "concise one-line update description",
  "parameter_adjustments": {"log_sensitivity": 0.1, ...},
  "self_reflection": "What went wrong and how to improve",
  "memory_updated": true
}"""

class RLCriticAgent:
    """RL Critic Agent for self-improvement and policy updates."""

    def __init__(self, policy: Optional[PolicyState] = None, memory: Optional[Any] = None):
        self.policy = policy or PolicyState()
        self.memory = memory
        self.llm = get_llm_client()

    async def critique(
        self,
        prediction: AgentPrediction,
        truth: KnownTruth,
        eval_result: EvaluationResult,
    ) -> CriticOutput:
        """Generate critique and policy improvements for a single case."""
        
        # Identify mistakes
        mistakes = {
            "missed_logs": [l for l in truth.flagged_logs if l not in prediction.flagged_logs],
            "missed_code": [c for c in truth.flagged_code if c not in prediction.flagged_code],
            "missed_requirements": [r for r in truth.flagged_requirements if r not in prediction.flagged_requirements],
            "false_positive_logs": [l for l in prediction.flagged_logs if l not in truth.flagged_logs],
            "false_positive_code": [c for c in prediction.flagged_code if c not in truth.flagged_code],
            "predicted_attack": prediction.attack_type,
            "true_attack": truth.attack_type,
        }
        
        # Generate policy adjustments
        param_adjustments = {}
        
        # If we missed logs, increase log sensitivity
        if mistakes["missed_logs"]:
            param_adjustments["log_sensitivity"] = 0.05
        
        # If we missed code issues, increase code sensitivity
        if mistakes["missed_code"]:
            param_adjustments["code_sensitivity"] = 0.05
        
        # If we missed requirements, increase req sensitivity
        if mistakes["missed_requirements"]:
            param_adjustments["req_sensitivity"] = 0.05
        
        # If wrong attack type, adjust confidence threshold
        if mistakes["predicted_attack"] != mistakes["true_attack"]:
            param_adjustments["confidence_threshold"] = -0.02
        
        output = CriticOutput(
            case_id=prediction.case_id,
            mistakes=mistakes,
            reward=eval_result.reward,
            policy_update="Adjusting sensitivities based on missed and false positive findings",
            parameter_adjustments=param_adjustments,
            memory_updated=False,
        )
        
        # LLM critique if available
        if self.llm.available:
            try:
                context = f"""
Reward: {eval_result.reward:.3f}
Scores: logs={eval_result.scores.logs_score:.2f}, code={eval_result.scores.code_score:.2f},
        requirements={eval_result.scores.requirements_score:.2f}, attack_type={eval_result.scores.attack_type_score:.2f}
Correct attack: {eval_result.correct_attack}

MISTAKES:
missed_logs: {mistakes['missed_logs'][:3]}
missed_code: {mistakes['missed_code'][:3]}
missed_requirements: {mistakes['missed_requirements'][:3]}
false_positive_logs: {mistakes['false_positive_logs'][:3]}
predicted_attack: {mistakes['predicted_attack']}
true_attack: {mistakes['true_attack']}

CURRENT POLICY:
log_sensitivity: {self.policy.log_sensitivity}
code_sensitivity: {self.policy.code_sensitivity}
req_sensitivity: {self.policy.req_sensitivity}
fusion_temperature: {self.policy.fusion_temperature}
confidence_threshold: {self.policy.confidence_threshold}"""
                
                llm_result = await self.llm.chat_json(CRITIC_SYSTEM_PROMPT, context)
                if llm_result:
                    output.policy_update = llm_result.get("policy_update", output.policy_update)
                    output.parameter_adjustments = llm_result.get("parameter_adjustments", output.parameter_adjustments)
                    output.self_reflection = llm_result.get("self_reflection", "")
            except Exception as e:
                logger.debug(f"LLM critique failed: {e}")
        
        # Store in memory if available
        if self.memory:
            try:
                self.memory.store(
                    case_id=prediction.case_id,
                    context=f"{prediction.attack_type}:{len(prediction.flagged_logs)}",
                    result={"reward": eval_result.reward, "success": eval_result.correct_attack},
                )
                output.memory_updated = True
            except Exception as e:
                logger.debug(f"Memory storage failed: {e}")
        
        return output
