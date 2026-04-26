"""
rl/train.py – Reinforcement Learning Trainer

Uses Stable-Baselines3 PPO inside a CyberMultiAgentEnv (Gymnasium) to learn
optimal policy-parameter adjustments across cybersecurity incident cases.

Training loop
─────────────
1. For each episode, the env loads a case.
2. PPO observes [case_embedding ‖ policy_vector].
3. PPO outputs a 5-D action (delta for each policy parameter).
4. The env runs all agents with the updated policy and evaluates.
5. Reward = final_score − penalty.
6. PPO updates its policy network weights.
7. CriticAgent also stores the episode in memory and logs insights.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from schemas import BenchmarkMetrics, PolicyState

logger = logging.getLogger("rl.train")

class RLTrainer:
    """
    Reinforcement Learning trainer for optimizing attack detection policy.
    """

    def __init__(
        self,
        cases: List[Any],
        agents: Dict[str, Any],
        evaluator: Any,
        policy: Optional[PolicyState] = None,
        checkpoint_dir: str = "./checkpoints",
    ):
        self.cases = cases
        self.agents = agents
        self.evaluator = evaluator
        self.policy = policy or PolicyState()
        self.checkpoint_dir = checkpoint_dir
        self.model = None
        os.makedirs(checkpoint_dir, exist_ok=True)

    def train(self, total_timesteps: int = 1000, callback: Optional[Any] = None) -> None:
        """Train the PPO model."""
        try:
            from stable_baselines3 import PPO
            from openenv import CyberMultiAgentEnv
        except ImportError:
            logger.error("Required packages not installed: stable-baselines3, gymnasium")
            return
        
        env = CyberMultiAgentEnv(self.cases, self.agents, self.evaluator, self.policy)
        
        self.model = PPO(
            "MlpPolicy",
            env,
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            verbose=1,
        )
        
        self.model.learn(total_timesteps=total_timesteps, callback=callback)
        logger.info(f"Training complete after {total_timesteps} timesteps")

    def evaluate(self, n_episodes: int = 20) -> BenchmarkMetrics:
        """Evaluate the trained model."""
        metrics = BenchmarkMetrics(total_cases=0)
        
        if not self.model:
            logger.warning("No trained model available")
            return metrics
        
        try:
            from openenv import CyberMultiAgentEnv
        except ImportError:
            return metrics
        
        env = CyberMultiAgentEnv(self.cases[:n_episodes], self.agents, self.evaluator, self.policy)
        
        for _ in range(n_episodes):
            obs, _ = env.reset()
            done = False
            episode_reward = 0
            
            while not done:
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, _ = env.step(action)
                episode_reward += reward
                done = terminated or truncated
        
        return metrics

    def save(self, directory: str) -> None:
        """Save the trained model."""
        if self.model:
            self.model.save(os.path.join(directory, "ppo_cyber"))
            logger.info(f"Model saved to {directory}")

    def load(self, directory: str) -> None:
        """Load a trained model."""
        try:
            from stable_baselines3 import PPO
            model_path = os.path.join(directory, "ppo_cyber")
            if os.path.exists(model_path + ".zip"):
                self.model = PPO.load(model_path)
                logger.info(f"Model loaded from {model_path}")
        except ImportError:
            logger.error("Stable-Baselines3 not available")

    def make_reward_shaping_callback(self) -> Any:
        """Create a callback for reward shaping during training."""
        class RewardShapingCallback:
            def __init__(self, trainer):
                self.trainer = trainer
            
            def __call__(self, locals_dict, globals_dict):
                return True
        
        return RewardShapingCallback(self)
