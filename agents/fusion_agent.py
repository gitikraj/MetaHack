"""
agents/fusion_agent.py – Threat Fusion Agent

Correlates findings from LogAgent, ReqAgent, and CodeAgent via:
  1. Rule-based indicator-to-attack-type mapping
  2. Voting mechanism across agents
  3. Debate framework for conflicting interpretations
  4. Optional LLM classification

The agent produces a final attack_type prediction along with confidence,
reasoning, and full debate transcript.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from schemas import (
    ATTACK_TYPES,
    AgentDebateRound,
    CodeAnalysis,
    FusionResult,
    LogAnalysis,
    PolicyState,
    RequirementsAnalysis,
)
from utils import get_embedding_engine, get_llm_client, setup_logging

logger = setup_logging("fusion_agent")

# ─────────────────────────────────────────────────────────────────────────────
# Indicator → Attack-type vote weights
# ─────────────────────────────────────────────────────────────────────────────
INDICATOR_ATTACK_MAP: Dict[str, Dict[str, float]] = {
    # Log indicators
    "brute_force": {"credential stuffing": 0.8, "ransomware": 0.2},
    "privilege_escalation": {"privilege escalation": 0.9, "lateral movement": 0.3},
    "malware_execution": {"remote code execution": 0.8, "botnet abuse": 0.5},
    "lateral_movement": {"lateral movement": 0.9, "insider threat": 0.2},
    "exfiltration": {"data exfiltration": 0.9, "insider threat": 0.4},
    
    # Code indicators
    "sql_injection": {"sql injection": 0.95, "remote code execution": 0.3},
    "command_injection": {"remote code execution": 0.9, "ransomware": 0.2},
    "xss": {"remote code execution": 0.5},
    "hardcoded_secret": {"credential stuffing": 0.6, "insider threat": 0.3},
    "deserialization": {"remote code execution": 0.8},
    
    # Requirements indicators
    "vulnerable_dependency": {"remote code execution": 0.7, "supply chain compromise": 0.8},
    "outdated_packages": {"supply chain compromise": 0.6, "remote code execution": 0.4},
}

ATTACK_SIMILARITY: Dict[Tuple[str, str], float] = {
    ("credential stuffing", "phishing compromise"): 0.6,
    ("sql injection", "remote code execution"): 0.45,
    ("ransomware", "lateral movement"): 0.4,
}

FUSION_SYSTEM_PROMPT = """You are a senior threat intelligence analyst.
You will receive security findings from three specialized agents.
Your task: correlate the evidence and determine the most likely attack type.

Respond ONLY in valid JSON:
{
  "attack_type": "one of the allowed labels",
  "confidence": 0.85,
  "reasoning": "Explain why you chose this attack type based on the evidence",
  "alternative_hypotheses": [{"type": "...", "confidence": 0.3}]
}

Allowed attack types (use EXACTLY):
credential stuffing, ransomware, insider threat, sql injection,
remote code execution, privilege escalation, supply chain compromise,
phishing compromise, data exfiltration, botnet abuse, crypto miner, lateral movement"""

class ThreatFusionAgent:
    """Threat Fusion Agent for correlating multi-agent findings."""

    def __init__(self, policy: Optional[PolicyState] = None):
        self.policy = policy or PolicyState()
        self.llm = get_llm_client()
        self.engine = get_embedding_engine()

    async def fuse(
        self,
        log_analysis: LogAnalysis,
        code_analysis: CodeAnalysis,
        req_analysis: RequirementsAnalysis,
    ) -> FusionResult:
        """Fuse all agent analyses into a final attack type prediction."""
        
        # Build voting scores from indicators
        votes: Dict[str, float] = defaultdict(float)
        
        for indicator, categories in log_analysis.indicators.items():
            if indicator in INDICATOR_ATTACK_MAP:
                for attack_type, weight in INDICATOR_ATTACK_MAP[indicator].items():
                    votes[attack_type] += weight * (log_analysis.confidence or 0.5)
        
        for vuln_type in code_analysis.vulnerability_types:
            if vuln_type in INDICATOR_ATTACK_MAP:
                for attack_type, weight in INDICATOR_ATTACK_MAP[vuln_type].items():
                    votes[attack_type] += weight * (code_analysis.confidence or 0.5)
        
        for risk_cat in req_analysis.risk_categories:
            if risk_cat in INDICATOR_ATTACK_MAP:
                for attack_type, weight in INDICATOR_ATTACK_MAP[risk_cat].items():
                    votes[attack_type] += weight * (req_analysis.confidence or 0.5)
        
        # Determine top prediction
        if votes:
            best_attack = max(votes, key=votes.get)
            confidence = votes[best_attack] / max(1.0, sum(votes.values()))
        else:
            best_attack = "ransomware"  # Default
            confidence = 0.3
        
        result = FusionResult(
            attack_type=best_attack,
            confidence=min(0.95, max(0.1, confidence)),
            reasoning=f"Voted {best_attack} based on {sum(1 for v in votes if v)} attack indicators"
        )
        
        # LLM refinement if available
        if self.llm.available:
            try:
                evidence = f"""Log findings:
flagged_logs: {log_analysis.flagged_logs[:5]}
indicators: {list(log_analysis.indicators.keys())}

Code findings:
flagged_code: {code_analysis.flagged_code[:5]}
vulnerability_types: {code_analysis.vulnerability_types}

Requirements findings:
flagged_requirements: {req_analysis.flagged_requirements[:5]}
risk_categories: {req_analysis.risk_categories}

Rule-based prediction: {best_attack}
Confidence threshold: {self.policy.confidence_threshold}
Fusion temperature: {self.policy.fusion_temperature}"""
                
                llm_result = await self.llm.chat_json(FUSION_SYSTEM_PROMPT, evidence)
                if llm_result:
                    result.attack_type = llm_result.get("attack_type", result.attack_type)
                    result.confidence = llm_result.get("confidence", result.confidence)
                    result.reasoning = llm_result.get("reasoning", result.reasoning)
            except Exception as e:
                logger.debug(f"LLM fusion failed: {e}")
        
        return result
