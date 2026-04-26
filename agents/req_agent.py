"""
agents/req_agent.py – Requirements Security Agent

Analyzes requirements.txt, Dockerfiles, and configuration strings for:
  - Outdated / CVE-vulnerable packages
  - Missing security headers / MFA
  - Unencrypted credentials in config
  - Supply-chain dependency risks
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from schemas import PolicyState, RequirementsAnalysis
from utils import get_llm_client, setup_logging, truncate

logger = setup_logging("req_agent")

# ─────────────────────────────────────────────────────────────────────────────
# Known vulnerable package versions (representative, not exhaustive)
# ─────────────────────────────────────────────────────────────────────────────
VULNERABLE_PACKAGES: Dict[str, Dict[str, str]] = {
    "django": {"max_safe": "3.2.0", "cve": "CVE-2021-23336", "risk": "SQL injection via QuerySet"},
    "flask": {"max_safe": "1.1.0", "cve": "CVE-2018-1000656", "risk": "JSON encoder DoS"},
    "jinja2": {"max_safe": "2.11.0", "cve": "CVE-2020-28493", "risk": "SSTI via __class__"},
    "requests": {"max_safe": "2.15.0", "cve": "CVE-2018-18074", "risk": "Header injection via reverse proxy"},
    "pillow": {"max_safe": "6.2.0", "cve": "CVE-2019-16865", "risk": "Buffer overflow in image parsing"},
    "numpy": {"max_safe": "1.16.0", "cve": "CVE-2019-6446", "risk": "Pickle arbitrary code execution"},
    "struts2": {"max_safe": "2.5.30", "cve": "CVE-2023-50164", "risk": "Path traversal / file upload RCE"},
}

CONFIG_RISK_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
    "hardcoded_secrets": [
        (r"password\s*[:=]\s*['\"].*['\"]", "Hardcoded password in config"),
        (r"api[_-]?key\s*[:=]\s*['\"].*['\"]", "Hardcoded API key"),
        (r"secret\s*[:=]\s*['\"].*['\"]", "Hardcoded secret"),
    ],
    "security_configs": [
        (r"ssl.*false|verify.*false|insecure.*true", "Insecure SSL/TLS settings"),
        (r"debug\s*[:=]\s*true|DEBUG\s*=\s*True", "Debug mode enabled in production"),
    ],
}

def _version_tuple(ver_str: str) -> Tuple[int, ...]:
    parts = re.split(r"[.\-]", ver_str)
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            break
    return tuple(result)

REQ_AGENT_SYSTEM_PROMPT = """You are a senior cloud-security and DevSecOps engineer.
Analyze the provided requirements / configuration text for security issues.
Return ONLY valid JSON:
{
  "flagged_requirements": ["exact line 1", "exact line 2", ...],
  "risk_categories": ["vulnerable_dependency", "hardcoded_secret", ...],
  "confidence": 0.85
}
flagged_requirements must be exact lines copied from the input."""

class RequirementsSecurityAgent:
    """Requirements Security Agent for detecting vulnerable dependencies."""

    def __init__(self, policy: Optional[PolicyState] = None):
        self.policy = policy or PolicyState()
        self.llm = get_llm_client()

    async def analyze(self, requirements: str) -> RequirementsAnalysis:
        """Analyze requirements/config for security issues."""
        result = RequirementsAnalysis()
        
        if not requirements:
            return result
        
        flagged = set()
        risk_categories = set()
        
        # Check for vulnerable packages
        for line in requirements.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Parse package==version
            match = re.match(r"(\w+)[>=<~!=]+([0-9.]+)", line)
            if match:
                pkg_name = match.group(1).lower()
                version = match.group(2)
                
                if pkg_name in VULNERABLE_PACKAGES:
                    max_safe = VULNERABLE_PACKAGES[pkg_name]["max_safe"]
                    if _version_tuple(version) < _version_tuple(max_safe):
                        flagged.add(line)
                        risk_categories.add("vulnerable_dependency")
            
            # Check for hardcoded secrets
            for pattern, risk in CONFIG_RISK_PATTERNS["hardcoded_secrets"]:
                if re.search(pattern, line, re.IGNORECASE):
                    flagged.add(line)
                    risk_categories.add("hardcoded_secret")
            
            # Check for insecure settings
            for pattern, risk in CONFIG_RISK_PATTERNS["security_configs"]:
                if re.search(pattern, line, re.IGNORECASE):
                    flagged.add(line)
                    risk_categories.add("insecure_config")
        
        result.flagged_requirements = list(flagged)[:20]
        result.risk_categories = list(risk_categories)
        result.confidence = min(0.95, 0.5 + len(flagged) * 0.1)
        
        # LLM enhancement if available
        if self.llm.available:
            try:
                llm_result = await self.llm.chat_json(
                    REQ_AGENT_SYSTEM_PROMPT,
                    f"Analyze this requirements file:\n\n{truncate(requirements, 2000)}"
                )
                if llm_result:
                    result.flagged_requirements = llm_result.get("flagged_requirements", result.flagged_requirements)
                    result.risk_categories = llm_result.get("risk_categories", result.risk_categories)
                    result.confidence = llm_result.get("confidence", result.confidence)
            except Exception as e:
                logger.debug(f"LLM analysis failed: {e}")
        
        return result
