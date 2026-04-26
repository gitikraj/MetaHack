"""
agents/critic_agent.py
Advanced RL Critic Agent with:
1. Real Q-Learning updates
2. Attack-type specific policies
3. Confidence learning (false positive control)
4. Historical reward trend monitoring
5. Replay memory support
6. Self reflection via LLM
"""

from __future__ import annotations
import logging
import statistics
from collections import deque, defaultdict
from typing import Any, Dict, Optional, List

from schemas import (
    AgentPrediction,
    CriticOutput,
    EvaluationResult,
    KnownTruth,
    PolicyState,
)

from utils import get_llm_client, setup_logging

logger = setup_logging("critic_agent")


CRITIC_SYSTEM_PROMPT = """
You are an autonomous RL cybersecurity critic.

Analyze detection mistakes and improve future policy.

Return ONLY JSON:
{
  "policy_update":"short update",
  "parameter_adjustments":{
      "log_sensitivity":0.02
  },
  "self_reflection":"what failed and why"
}
"""


class AdvancedRLCriticAgent:

    def __init__(
        self,
        policy: Optional[PolicyState] = None,
        memory: Optional[Any] = None
    ):

        self.policy = policy or PolicyState()
        self.memory = memory
        self.llm = get_llm_client()

        # RL Hyperparameters
        self.alpha = 0.15      # learning rate
        self.gamma = 0.90      # future reward weight
        self.epsilon = 0.10    # exploration

        # Q Table
        self.q_table = defaultdict(float)

        # Reward history
        self.reward_history = deque(maxlen=10)

        # Replay memory
        self.replay_buffer = deque(maxlen=100)

        # Attack specific policies
        self.attack_profiles = {
            "xss": {
                "code_weight": 1.3,
                "log_weight": 0.8
            },
            "credential stuffing": {
                "log_weight": 1.5,
                "code_weight": 0.6
            },
            "malware": {
                "code_weight": 1.4,
                "req_weight": 1.2
            },
            "data exfiltration": {
                "log_weight": 1.6,
                "network_weight": 1.5
            }
        }

    # ==========================================================
    # STATE ENCODER
    # ==========================================================
    def get_state(self, truth: KnownTruth):
        return truth.attack_type.lower()

    def get_action(self):
        return "tune_policy"

    # ==========================================================
    # Q LEARNING UPDATE
    # ==========================================================
    def update_q_value(self, state, action, reward, next_state):

        key = (state, action)
        next_key = (next_state, action)

        old_q = self.q_table[key]
        next_q = self.q_table[next_key]

        new_q = old_q + self.alpha * (
            reward + self.gamma * next_q - old_q
        )

        self.q_table[key] = new_q

    # ==========================================================
    # TREND CHECK
    # ==========================================================
    def rewards_declining(self):

        if len(self.reward_history) < 10:
            return False

        first_half = list(self.reward_history)[:5]
        second_half = list(self.reward_history)[5:]

        return statistics.mean(second_half) < statistics.mean(first_half)

    # ==========================================================
    # ATTACK PROFILE BOOSTS
    # ==========================================================
    def apply_attack_specific_policy(self, attack_type):

        attack_type = attack_type.lower()

        profile = self.attack_profiles.get(attack_type)

        if not profile:
            return {}

        adjustments = {}

        if "log_weight" in profile:
            adjustments["log_sensitivity"] = round(
                profile["log_weight"] * 0.02, 3
            )

        if "code_weight" in profile:
            adjustments["code_sensitivity"] = round(
                profile["code_weight"] * 0.02, 3
            )

        if "req_weight" in profile:
            adjustments["req_sensitivity"] = round(
                profile["req_weight"] * 0.02, 3
            )

        return adjustments

    # ==========================================================
    # MAIN CRITIQUE LOOP
    # ==========================================================
    async def critique(
        self,
        prediction: AgentPrediction,
        truth: KnownTruth,
        eval_result: EvaluationResult,
    ) -> CriticOutput:

        mistakes = {
            "missed_logs": [
                x for x in truth.flagged_logs
                if x not in prediction.flagged_logs
            ],
            "missed_code": [
                x for x in truth.flagged_code
                if x not in prediction.flagged_code
            ],
            "missed_requirements": [
                x for x in truth.flagged_requirements
                if x not in prediction.flagged_requirements
            ],
            "false_positive_logs": [
                x for x in prediction.flagged_logs
                if x not in truth.flagged_logs
            ],
            "false_positive_code": [
                x for x in prediction.flagged_code
                if x not in truth.flagged_code
            ],
            "predicted_attack": prediction.attack_type,
            "true_attack": truth.attack_type,
        }

        reward = eval_result.reward

        # ======================================================
        # RL State
        # ======================================================
        state = self.get_state(truth)
        action = self.get_action()
        next_state = state

        self.update_q_value(state, action, reward, next_state)

        self.reward_history.append(reward)

        # ======================================================
        # Base Adjustments
        # ======================================================
        adjustments = {}

        # Missed detections
        if mistakes["missed_logs"]:
            adjustments["log_sensitivity"] = 0.04

        if mistakes["missed_code"]:
            adjustments["code_sensitivity"] = 0.04

        if mistakes["missed_requirements"]:
            adjustments["req_sensitivity"] = 0.04

        # Wrong attack type
        if mistakes["predicted_attack"] != mistakes["true_attack"]:
            adjustments["confidence_threshold"] = -0.03

        # ======================================================
        # False Positive Control
        # ======================================================
        fp_count = len(mistakes["false_positive_logs"]) + len(
            mistakes["false_positive_code"]
        )

        if fp_count >= 3:
            adjustments["log_sensitivity"] = adjustments.get(
                "log_sensitivity", 0
            ) - 0.03

            adjustments["code_sensitivity"] = adjustments.get(
                "code_sensitivity", 0
            ) - 0.03

        # ======================================================
        # Attack Specific Learning
        # ======================================================
        profile_adj = self.apply_attack_specific_policy(
            truth.attack_type
        )

        for k, v in profile_adj.items():
            adjustments[k] = adjustments.get(k, 0) + v

        # ======================================================
        # Reward Trend Retraining Trigger
        # ======================================================
        retrain_flag = False

        if self.rewards_declining():
            retrain_flag = True
            adjustments["fusion_temperature"] = 0.05

        # ======================================================
        # Replay Memory
        # ======================================================
        self.replay_buffer.append({
            "state": state,
            "reward": reward,
            "mistakes": mistakes
        })

        # ======================================================
        # Output Object
        # ======================================================
        output = CriticOutput(
            case_id=prediction.case_id,
            mistakes=mistakes,
            reward=reward,
            policy_update="Adaptive RL tuning applied",
            parameter_adjustments=adjustments,
            memory_updated=False,
            self_reflection=""
        )

        # ======================================================
        # LLM Reflection
        # ======================================================
        if self.llm.available:

            try:

                context = f"""
Reward={reward}

Missed Logs={mistakes['missed_logs'][:3]}
Missed Code={mistakes['missed_code'][:3]}
False Positives={fp_count}

Attack Prediction={mistakes['predicted_attack']}
True Attack={mistakes['true_attack']}

Q Value={self.q_table[(state, action)]}

Trend Declining={retrain_flag}
"""

                llm_result = await self.llm.chat_json(
                    CRITIC_SYSTEM_PROMPT,
                    context
                )

                if llm_result:
                    output.policy_update = llm_result.get(
                        "policy_update",
                        output.policy_update
                    )

                    output.self_reflection = llm_result.get(
                        "self_reflection",
                        ""
                    )

                    extra = llm_result.get(
                        "parameter_adjustments",
                        {}
                    )

                    for k, v in extra.items():
                        adjustments[k] = adjustments.get(k, 0) + v

            except Exception as e:
                logger.debug(f"LLM reflection failed: {e}")

        # ======================================================
        # Store Memory
        # ======================================================
        if self.memory:

            try:
                self.memory.store(
                    case_id=prediction.case_id,
                    context=truth.attack_type,
                    result={
                        "reward": reward,
                        "q_value": self.q_table[(state, action)]
                    }
                )

                output.memory_updated = True

            except Exception as e:
                logger.debug(f"memory failed {e}")

        output.parameter_adjustments = adjustments

        return output