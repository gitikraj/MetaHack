"""
agents/log_agent.py – Log Intelligence Agent

Analyzes raw log lines for:
  - Repeated failed logins / brute-force / credential stuffing
  - Impossible travel (same user, multiple distant IPs)
  - Privilege escalation patterns
  - Malware traces (reverse shells, encoded payloads, droppers)
  - Exfiltration indicators (large outbound, DNS tunneling)
  - Lateral movement (internal SSH/RDP hops, PSExec, WMI)
  - Command execution traces
  - Known-bad IP activity
"""
from __future__ import annotations

import asyncio
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from schemas import LogAnalysis, PolicyState
from utils import get_embedding_engine, get_llm_client, setup_logging, truncate

logger = setup_logging("log_agent")

# ─────────────────────────────────────────────────────────────────────────────
# Regex pattern bank keyed by indicator category
# ─────────────────────────────────────────────────────────────────────────────
PATTERN_BANK: Dict[str, List[str]] = {
    "failed_login": [
        r"[Ff]ailed password for (?:invalid user )?(\S+) from ([\d.]+)",
        r"authentication failure.*user=(\S+).*rhost=([\d.]+)",
        r"Failed password for invalid user (\S+) from ([\d.]+)",
        r"[Aa]ccess [Dd]enied.*user[=: ](\S+)",
    ],
    "brute_force": [
        r"[Tt]oo many authentication failures",
        r"[Rr]ate [Ll]imit exceeded",
        r"rate[ -]limit.*exceeded",
    ],
    "privilege_escalation": [
        r"sudo.*COMMAND",
        r"sudo:.*successful",
        r"[Pp]rivilege escalation",
        r"exec \/bin\/bash",
    ],
    "malware_execution": [
        r"reverse shell|nc -l|bash -i",
        r"exec.*curl|wget.*\|",
        r"base64|decode|payload",
        r"cmd\.exe|powershell.*-nop",
    ],
    "lateral_movement": [
        r"ssh.*rhost|ssh.*from.*port",
        r"\\\\\\\\[\d.]+\\\\",  # UNC path
        r"psexec|wmic|winrm",
        r"rdp|3389",
    ],
    "exfiltration": [
        r"data.*send|transfer|upload",
        r"bytes sent.*\d{6,}",
        r"dns.*query.*txt",
    ],
}

LOG_AGENT_SYSTEM_PROMPT = """You are an elite SOC analyst specializing in log forensics.
Analyze the provided log lines and identify suspicious or malicious activity.
Return ONLY valid JSON with this exact structure:
{
  "flagged_logs": ["exact log line 1", "exact log line 2", ...],
  "reasoning": "brief explanation of findings",
  "indicators": {"category": ["indicator1", "indicator2"], ...},
  "confidence": 0.75
}
flagged_logs must be exact substrings or copies of lines from the input.
Do NOT fabricate log lines."""

class LogIntelligenceAgent:
    """Log Intelligence Agent for detecting malicious patterns."""

    def __init__(self, policy: Optional[PolicyState] = None):
        self.policy = policy or PolicyState()
        self.llm = get_llm_client()
        self.engine = get_embedding_engine()

    async def analyze(self, logs: List[str]) -> LogAnalysis:
        """Analyze logs for suspicious patterns."""
        result = LogAnalysis()
        
        if not logs:
            return result
        
        # Rule-based detection
        flagged = set()
        indicators = defaultdict(list)
        
        for log in logs:
            for category, patterns in PATTERN_BANK.items():
                for pattern in patterns:
                    try:
                        if re.search(pattern, log):
                            flagged.add(log)
                            indicators[category].append(log[:50])
                            break
                    except re.error:
                        pass
        
        result.flagged_logs = list(flagged)[:20]  # Limit to top 20
        result.indicators = dict(indicators)
        result.confidence = min(0.95, 0.5 + len(flagged) * 0.05)
        
        # LLM enhancement if available
        if self.llm.available and logs:
            try:
                log_sample = "\n".join(logs[:30])
                llm_result = await self.llm.chat_json(
                    LOG_AGENT_SYSTEM_PROMPT,
                    f"Analyze these log lines:\n\n{truncate(log_sample, 2000)}"
                )
                if llm_result:
                    result.flagged_logs = llm_result.get("flagged_logs", result.flagged_logs)
                    result.reasoning = llm_result.get("reasoning", "")
                    result.confidence = llm_result.get("confidence", result.confidence)
            except Exception as e:
                logger.debug(f"LLM analysis failed: {e}")
        
        return result
