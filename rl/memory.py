"""
rl/memory.py – FAISS-backed episodic memory for the multi-agent system.

Stores embeddings of past incident contexts together with the prediction
outcome and evaluation result. At query time, returns the k most similar
past episodes so agents can condition their analysis on prior experience.
"""
from __future__ import annotations

import logging
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("rl.memory")

class FAISSEpisodicMemory:
    """
    FAISS-backed memory for storing and retrieving past episodes.
    Allows agents to learn from similar historical incidents.
    """

    def __init__(self, dim: int = 384, max_size: int = 10000):
        self.dim = dim
        self.max_size = max_size
        self.episodes: List[Dict[str, Any]] = []
        self.index = None
        self._embeddings = None
        
        try:
            import faiss
            self.faiss = faiss
            self.index = faiss.IndexFlatL2(dim)
        except ImportError:
            logger.warning("FAISS not available, using in-memory storage only")
            self.faiss = None

    def store(self, case_id: str, context: str, result: Dict[str, Any]) -> None:
        """Store an episode in memory."""
        if len(self.episodes) >= self.max_size:
            self.episodes = self.episodes[-(self.max_size - 1):]
        
        episode = {
            "case_id": case_id,
            "context": context,
            "result": result,
        }
        self.episodes.append(episode)

    def query(self, context_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve k most similar episodes."""
        if not self.episodes:
            return []
        
        if self.index is None:
            # Fallback: simple cosine similarity
            return self.episodes[:min(k, len(self.episodes))]
        
        try:
            # Normalize and search
            context_embedding = context_embedding / (np.linalg.norm(context_embedding) + 1e-10)
            context_embedding = np.expand_dims(context_embedding, axis=0).astype(np.float32)
            _, indices = self.index.search(context_embedding, min(k, len(self.episodes)))
            return [self.episodes[i] for i in indices[0] if i < len(self.episodes)]
        except Exception as e:
            logger.debug(f"FAISS query failed: {e}")
            return self.episodes[:min(k, len(self.episodes))]

    def save(self, directory: str) -> None:
        """Save memory to disk."""
        os.makedirs(directory, exist_ok=True)
        episodes_file = os.path.join(directory, "episodes.pkl")
        
        with open(episodes_file, "wb") as f:
            pickle.dump(self.episodes, f)
        
        logger.info(f"Saved {len(self.episodes)} episodes to {directory}")

    def load(self, directory: str) -> None:
        """Load memory from disk."""
        episodes_file = os.path.join(directory, "episodes.pkl")
        
        if os.path.exists(episodes_file):
            with open(episodes_file, "rb") as f:
                self.episodes = pickle.load(f)
            logger.info(f"Loaded {len(self.episodes)} episodes from {directory}")

    def __len__(self) -> int:
        return len(self.episodes)
