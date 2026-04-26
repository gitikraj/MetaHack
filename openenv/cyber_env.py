"""
openenv/cyber_env.py – CyberMultiAgentEnv

A fully Gymnasium-compatible environment that wraps the multi-agent pipeline.

Observation
───────────
  [case_embedding (384-D) ‖ policy_vector (5-D)] → Box(389,)

Action
──────
  5 continuous deltas: [Δlog_sens, Δcode_sens, Δreq_sens, Δfusion_temp, Δconf_thresh]
  Each in [-0.2, 0.2]. Applied to current PolicyState before agents run.

Reward
──────
  final_score − penalty   (clipped to [-1, 1])

Episode
───────
  Each episode = one incident case.
  Episode length = 1 (immediate evaluation).
  To train for N cases, set total_timesteps = N in PPO.learn().

Usage
─────
  env = CyberMultiAgentEnv(cases, agents_dict, evaluator, policy_state)
  env.reset()
  obs, reward, term, trunc, info = env.step(action)
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:
    import gym
    from gym import spaces

from schemas import (
    AgentPrediction,
    IncidentCase,
    PolicyState,
)
from utils import get_embedding_engine, setup_logging, truncate

logger = setup_logging("openenv")

OBS_DIM = 389  # 384 embedding + 5 policy dims

class CyberMultiAgentEnv(gym.Env):
    """
    Gymnasium-compatible environment for training multi-agent cybersecurity detector.
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        cases: List[Any],
        agents: Dict[str, Any],
        evaluator: Any,
        policy: Optional[PolicyState] = None,
    ):
        self.cases = cases
        self.agents = agents
        self.evaluator = evaluator
        self.policy = policy or PolicyState()
        self.engine = get_embedding_engine()
        
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(OBS_DIM,), dtype=np.float32)
        self.action_space = spaces.Box(low=-0.2, high=0.2, shape=(5,), dtype=np.float32)
        
        self.current_episode = 0
        self.current_case: Optional[IncidentCase] = None
        self.last_reward = 0.0

    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """Reset environment to a new case."""
        if seed is not None:
            np.random.seed(seed)
        
        if self.current_episode >= len(self.cases):
            self.current_episode = 0
        
        self.current_case = self.cases[self.current_episode]
        self.current_episode += 1
        
        obs = self._make_observation()
        return obs, {}

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """Execute one step: apply action and evaluate."""
        if self.current_case is None:
            raise RuntimeError("Environment not reset")
        
        # Apply action to policy
        old_policy = PolicyState(
            log_sensitivity=self.policy.log_sensitivity,
            code_sensitivity=self.policy.code_sensitivity,
            req_sensitivity=self.policy.req_sensitivity,
            fusion_temperature=self.policy.fusion_temperature,
            confidence_threshold=self.policy.confidence_threshold,
        )
        
        self.policy.log_sensitivity = max(0.1, min(2.0, self.policy.log_sensitivity + float(action[0])))
        self.policy.code_sensitivity = max(0.1, min(2.0, self.policy.code_sensitivity + float(action[1])))
        self.policy.req_sensitivity = max(0.1, min(2.0, self.policy.req_sensitivity + float(action[2])))
        self.policy.fusion_temperature = max(0.1, min(2.0, self.policy.fusion_temperature + float(action[3])))
        self.policy.confidence_threshold = max(0.1, min(0.9, self.policy.confidence_threshold + float(action[4])))
        
        # Run agents with new policy
        try:
            prediction = asyncio.run(self._run_agents())
        except Exception as e:
            logger.debug(f"Agent execution failed: {e}")
            prediction = AgentPrediction(case_id=self.current_case.case_id)
        
        # Evaluate
        eval_result = self.evaluator.grade(prediction, self.current_case.known_truth)
        reward = float(eval_result.reward)
        self.last_reward = reward
        
        obs = self._make_observation()
        terminated = True  # Each case is one episode
        truncated = False
        info = {"reward": reward, "case_id": self.current_case.case_id}
        
        return obs, reward, terminated, truncated, info

    async def _run_agents(self) -> AgentPrediction:
        """Run all agents on current case."""
        log_r = await self.agents["log"].analyze(self.current_case.logs)
        code_r = await self.agents["code"].analyze(self.current_case.code)
        req_r = await self.agents["req"].analyze(self.current_case.requirements)
        fusion_r = await self.agents["fusion"].fuse(log_r, code_r, req_r)
        
        return AgentPrediction(
            case_id=self.current_case.case_id,
            flagged_logs=log_r.flagged_logs,
            flagged_code=code_r.flagged_code,
            flagged_requirements=req_r.flagged_requirements,
            attack_type=fusion_r.attack_type,
            confidence=fusion_r.confidence,
            reasoning=fusion_r.reasoning,
            log_analysis=log_r,
            code_analysis=code_r,
            req_analysis=req_r,
            fusion_result=fusion_r,
        )

    def _make_observation(self) -> np.ndarray:
        """Construct observation: [case_embedding ‖ policy_vector]."""
        if self.current_case is None:
            case_emb = np.zeros(384, dtype=np.float32)
        else:
            case_text = f"{self.current_case.attack_type} {len(self.current_case.logs)} {len(self.current_case.code)}"
            case_emb = self.engine.encode(case_text).astype(np.float32)
        
        policy_vec = np.array(self.policy.as_vector(), dtype=np.float32)
        obs = np.concatenate([case_emb, policy_vec])
        return obs.astype(np.float32)

    def render(self) -> None:
        """Render is not implemented."""
        pass
