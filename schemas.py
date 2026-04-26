"""
schemas.py – Pydantic v2 data models for the CyberMultiAgent platform.
Every inter-agent contract, evaluation result, and policy state is typed here.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

# ─────────────────────────────────────────────────────────────────────────────
# Attack taxonomy
# ─────────────────────────────────────────────────────────────────────────────
ATTACK_TYPES: List[str] = [
    "credential stuffing",
    "ransomware",
    "insider threat",
    "sql injection",
    "remote code execution",
    "privilege escalation",
    "supply chain compromise",
    "phishing compromise",
    "data exfiltration",
    "botnet abuse",
    "crypto miner",
    "lateral movement",
]

# ─────────────────────────────────────────────────────────────────────────────
# Input case structures
# ─────────────────────────────────────────────────────────────────────────────
class KnownTruth(BaseModel):
    attack_type: str
    flagged_logs: List[str] = Field(default_factory=list)
    flagged_code: List[str] = Field(default_factory=list)
    flagged_requirements: List[str] = Field(default_factory=list)

    @field_validator("attack_type")
    @classmethod
    def validate_attack_type(cls, v: str) -> str:
        if v not in ATTACK_TYPES:
            raise ValueError(f"Invalid attack type: {v}. Must be one of {ATTACK_TYPES}")
        return v

class IncidentCase(BaseModel):
    case_id: str = Field(default_factory=lambda: f"case_{uuid.uuid4().hex[:8]}")
    logs: List[str]
    requirements: str
    code: str
    known_truth: KnownTruth

# ─────────────────────────────────────────────────────────────────────────────
# Per-agent outputs
# ─────────────────────────────────────────────────────────────────────────────
class LogAnalysis(BaseModel):
    flagged_logs: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reasoning: str = ""
    indicators: Dict[str, List[str]] = Field(default_factory=dict)

class RequirementsAnalysis(BaseModel):
    flagged_requirements: List[str] = Field(default_factory=list)
    risk_categories: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

class CodeAnalysis(BaseModel):
    flagged_code: List[str] = Field(default_factory=list)
    vulnerability_types: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# Cross-agent debate
# ─────────────────────────────────────────────────────────────────────────────
class AgentDebateRound(BaseModel):
    agent: str
    claim: str
    confidence: float
    supporting_evidence: List[str] = Field(default_factory=list)

class FusionResult(BaseModel):
    attack_type: str
    confidence: float = 0.5
    reasoning: str = ""
    debate_rounds: List[AgentDebateRound] = Field(default_factory=list)
    alternative_hypotheses: List[Dict[str, Any]] = Field(default_factory=list)

# ─────────────────────────────────────────────────────────────────────────────
# Aggregated prediction (solver output)
# ─────────────────────────────────────────────────────────────────────────────
class AgentPrediction(BaseModel):
    case_id: str
    flagged_logs: List[str] = Field(default_factory=list)
    flagged_code: List[str] = Field(default_factory=list)
    flagged_requirements: List[str] = Field(default_factory=list)
    attack_type: str = ""
    confidence: float = 0.5
    reasoning: str = ""
    per_agent_confidence: Dict[str, float] = Field(default_factory=dict)
    log_analysis: Optional[LogAnalysis] = None
    req_analysis: Optional[RequirementsAnalysis] = None
    code_analysis: Optional[CodeAnalysis] = None
    fusion_result: Optional[FusionResult] = None

# ─────────────────────────────────────────────────────────────────────────────
# Evaluation
# ─────────────────────────────────────────────────────────────────────────────
class EvaluationScores(BaseModel):
    logs_score: float = 0.0
    code_score: float = 0.0
    requirements_score: float = 0.0
    attack_type_score: float = 0.0
    final_score: float = 0.0

    def compute_final(self) -> float:
        self.final_score = round(
            0.30 * self.logs_score +
            0.25 * self.code_score +
            0.20 * self.requirements_score +
            0.25 * self.attack_type_score,
            4
        )
        return self.final_score

class PenaltyBreakdown(BaseModel):
    missed_logs: float = 0.0
    missed_code: float = 0.0
    missed_requirements: float = 0.0
    false_positives: float = 0.0
    wrong_type: float = 0.0
    total_penalty: float = 0.0

    def compute_total(self) -> float:
        self.total_penalty = round(
            0.25 * self.false_positives +
            0.25 * self.wrong_type,
            4
        )
        return self.total_penalty

class EvaluationResult(BaseModel):
    case_id: str
    scores: EvaluationScores
    penalties: PenaltyBreakdown
    reward: float
    missed_findings: Dict[str, List[str]] = Field(default_factory=dict)
    false_positives_detail: Dict[str, List[str]] = Field(default_factory=dict)
    correct_attack: bool = False

# ─────────────────────────────────────────────────────────────────────────────
# RL Critic output
# ─────────────────────────────────────────────────────────────────────────────
class CriticOutput(BaseModel):
    case_id: str
    mistakes: Dict[str, Any] = Field(default_factory=dict)
    reward: float
    policy_update: str
    parameter_adjustments: Dict[str, float] = Field(default_factory=dict)
    memory_updated: bool = False
    self_reflection: str = ""

# ─────────────────────────────────────────────────────────────────────────────
# Policy / RL state
# ─────────────────────────────────────────────────────────────────────────────
class PolicyState(BaseModel):
    log_sensitivity: float = 1.0      # Multiplier for log pattern thresholds
    code_sensitivity: float = 1.0     # Multiplier for code pattern thresholds
    req_sensitivity: float = 1.0      # Multiplier for requirements checks
    fusion_temperature: float = 1.0   # Softmax temperature for fusion voting
    confidence_threshold: float = 0.4  # Minimum confidence to flag an item
    brute_force_window: int = 5       # Seconds window for brute force detection
    min_failed_logins: int = 4        # Threshold for brute force
    iteration: int = 0
    cumulative_reward: float = 0.0
    episode_rewards: List[float] = Field(default_factory=list)

    def as_vector(self) -> List[float]:
        return [
            self.log_sensitivity,
            self.code_sensitivity,
            self.req_sensitivity,
            self.fusion_temperature,
            self.confidence_threshold,
        ]

    def update_from_vector(self, vec: List[float]) -> None:
        self.log_sensitivity = float(vec[0])
        self.code_sensitivity = float(vec[1])
        self.req_sensitivity = float(vec[2])
        self.fusion_temperature = float(vec[3])
        self.confidence_threshold = float(vec[4])

# ─────────────────────────────────────────────────────────────────────────────
# Benchmark / dashboard metrics
# ─────────────────────────────────────────────────────────────────────────────
class BenchmarkMetrics(BaseModel):
    total_cases: int = 0
    mean_reward: float = 0.0
    mean_final_score: float = 0.0
    attack_type_accuracy: float = 0.0
    mean_logs_score: float = 0.0
    mean_code_score: float = 0.0
    mean_requirements_score: float = 0.0
    per_attack_scores: Dict[str, List[float]] = Field(default_factory=dict)
    improvement_over_baseline: float = 0.0
    all_rewards: List[float] = Field(default_factory=list)
    all_final_scores: List[float] = Field(default_factory=list)
