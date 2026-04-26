"""
utils.py – Shared utilities: embeddings, semantic scoring, LLM client, logging.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from functools import lru_cache
from typing import List, Optional, Tuple

import numpy as np
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────
def setup_logging(name: str = "cyberenv", level: str = "INFO") -> logging.Logger:
    log_level = getattr(logging, os.getenv("LOG_LEVEL", level).upper(), logging.INFO)
    logging.basicConfig(
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        level=log_level,
    )
    return logging.getLogger(name)

logger = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
# Embedding engine (singleton)
# ─────────────────────────────────────────────────────────────────────────────
class EmbeddingEngine:
    """Wraps SentenceTransformers; falls back to TF-IDF hash if unavailable."""

    _instance: Optional["EmbeddingEngine"] = None

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self.dim = 384

    @classmethod
    def get_instance(cls) -> "EmbeddingEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        except ImportError:
            logger.warning("SentenceTransformers not available, using hash embedding fallback")

    def encode(self, text: str) -> np.ndarray:
        self._load()
        try:
            if self._model is not None:
                return self._model.encode(text)
        except Exception as e:
            logger.debug(f"Embedding failed: {e}")
        return self._hash_embed(text)

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        self._load()
        try:
            if self._model is not None:
                return self._model.encode(texts)
        except Exception as e:
            logger.debug(f"Batch embedding failed: {e}")
        return np.stack([self._hash_embed(t) for t in texts])

    @staticmethod
    def _hash_embed(text: str) -> np.ndarray:
        import hashlib
        h = hashlib.sha256(text.encode()).digest()
        vec = np.frombuffer(h, dtype=np.float32)
        vec = np.pad(vec, (0, 384 - len(vec)), mode='constant')[:384]
        return vec / (np.linalg.norm(vec) + 1e-8)

# ─────────────────────────────────────────────────────────────────────────────
# Vector math helpers
# ─────────────────────────────────────────────────────────────────────────────
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = a / (np.linalg.norm(a) + 1e-10)
    b = b / (np.linalg.norm(b) + 1e-10)
    return float(np.clip(np.dot(a, b), -1.0, 1.0))

def jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    return len(set_a & set_b) / len(union) if union else 0.0

# ─────────────────────────────────────────────────────────────────────────────
# Token-level matching (works without embeddings)
# ─────────────────────────────────────────────────────────────────────────────
def _tokenize(text: str) -> set:
    """Split text into lowercase alphanumeric tokens ≥ 2 chars."""
    return {t for t in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if len(t) >= 2}

def token_overlap_score(pred: str, truth: str) -> float:
    """Token-level F1 between two strings."""
    p_tok = _tokenize(pred)
    t_tok = _tokenize(truth)
    if not p_tok and not t_tok:
        return 1.0
    if not p_tok or not t_tok:
        return 0.0
    common = p_tok & t_tok
    prec = len(common) / len(p_tok)
    rec  = len(common) / len(t_tok)
    if prec + rec < 1e-8:
        return 0.0
    return 2 * prec * rec / (prec + rec)

def list_token_f1(
    pred_list: List[str],
    truth_list: List[str],
) -> float:
    """
    Token-overlap F1 between two lists of strings.
    For each truth item, find the best token-overlap to any prediction (recall).
    For each prediction, find the best token-overlap to any truth (precision).
    Return the harmonic mean.
    """
    if not pred_list and not truth_list:
        return 1.0
    if not pred_list or not truth_list:
        return 0.0
    # Recall: for each truth, best match in predictions
    recalls = []
    for t in truth_list:
        best = max(token_overlap_score(p, t) for p in pred_list)
        recalls.append(best)
    recall = float(np.mean(recalls))
    # Precision: for each prediction, best match in truths
    precs = []
    for p in pred_list:
        best = max(token_overlap_score(p, t) for t in truth_list)
        precs.append(best)
    precision = float(np.mean(precs))
    if precision + recall < 1e-8:
        return 0.0
    return 2 * precision * recall / (precision + recall)

# ─────────────────────────────────────────────────────────────────────────────
# Semantic list scoring
# ─────────────────────────────────────────────────────────────────────────────
def semantic_precision_recall(
    pred_list: List[str],
    truth_list: List[str],
    engine: EmbeddingEngine,
    threshold: float = 0.40,
) -> Tuple[float, float]:
    """
    Returns (semantic_precision, semantic_recall).
    For precision: what fraction of predictions match some ground truth.
    For recall:    what fraction of truths are covered by some prediction.
    """
    if not pred_list and not truth_list:
        return 1.0, 1.0
    if not pred_list:
        return 0.0, 0.0
    if not truth_list:
        return 0.0, 1.0

    pred_embs = engine.encode_batch(pred_list)
    truth_embs = engine.encode_batch(truth_list)

    # Precision: for each prediction find max similarity to any truth
    prec_scores = []
    for pe in pred_embs:
        sims = [cosine_similarity(pe, te) for te in truth_embs]
        prec_scores.append(max(sims))
    precision = float(np.mean([1.0 if s >= threshold else s for s in prec_scores]))

    # Recall: for each truth find max similarity to any prediction
    rec_scores = []
    for te in truth_embs:
        sims = [cosine_similarity(te, pe) for pe in pred_embs]
        rec_scores.append(max(sims))
    recall = float(np.mean([1.0 if s >= threshold else s for s in rec_scores]))

    return precision, recall

def semantic_f1(
    pred_list: List[str],
    truth_list: List[str],
    engine: EmbeddingEngine,
    threshold: float = 0.40,
) -> float:
    p, r = semantic_precision_recall(pred_list, truth_list, engine, threshold)
    if p + r < 1e-8:
        return 0.0
    return 2 * p * r / (p + r)

def list_match_score(
    pred_list: List[str],
    truth_list: List[str],
    engine: EmbeddingEngine,
) -> float:
    """
    Three-tier scoring: exact overlap + token F1 + semantic F1.
    Token F1 provides partial credit without needing good embeddings.
    Semantic F1 adds embedding-level matching when available.
    """
    exact_jac = jaccard_similarity(set(pred_list), set(truth_list))
    tok_f1    = list_token_f1(pred_list, truth_list)
    sem_f1    = semantic_f1(pred_list, truth_list, engine)
    return 0.25 * exact_jac + 0.40 * tok_f1 + 0.35 * sem_f1

# ─────────────────────────────────────────────────────────────────────────────
# LLM client
# ─────────────────────────────────────────────────────────────────────────────
class LLMClient:
    """
    Thin async wrapper around OpenAI chat completions.
    Falls back gracefully if no API key is set.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.use_llm = os.getenv("USE_LLM", "true").lower() == "true"
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key) and self.use_llm

    def _get_client(self):
        if self._client is None and self.available:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("OpenAI client not available")
        return self._client

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        retries: int = 3,
    ) -> Optional[str]:
        client = self._get_client()
        if client is None:
            return None
        
        for attempt in range(retries):
            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.debug(f"Chat attempt {attempt + 1} failed: {e}")
                if attempt == retries - 1:
                    return None
                await asyncio.sleep(0.5)
        return None

    async def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> Optional[dict]:
        raw = await self.chat(system_prompt, user_prompt, temperature, max_tokens)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.debug("Failed to parse JSON from LLM response")
            return None

import asyncio

# Singletons
_llm_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

def get_embedding_engine() -> EmbeddingEngine:
    return EmbeddingEngine.get_instance()

# ─────────────────────────────────────────────────────────────────────────────
# Text helpers
# ─────────────────────────────────────────────────────────────────────────────
def normalize_attack_type(raw: str) -> str:
    """Lower-case and strip attack type string."""
    from schemas import ATTACK_TYPES
    raw = raw.strip().lower()
    # Direct match
    if raw in ATTACK_TYPES:
        return raw
    # Fuzzy match via containment
    for a in ATTACK_TYPES:
        if a in raw or raw in a:
            return a
    return raw

def truncate(text: str, max_chars: int = 3000) -> str:
    return text[:max_chars] if len(text) > max_chars else text

def extract_ips(log_line: str) -> List[str]:
    return re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", log_line)

def extract_users(log_line: str) -> List[str]:
    patterns = [
        r"for (\w+) from",
        r"user[=: ](\w+)",
        r"session opened for user (\w+)",
    ]
    users = []
    for p in patterns:
        users.extend(re.findall(p, log_line, re.IGNORECASE))
    return list(set(users))
