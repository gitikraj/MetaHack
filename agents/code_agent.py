"""
agents/code_agent.py – Secure Code Agent

Analyzes source code for:
  - SQL Injection (concatenated queries, format strings)
  - Cross-site scripting (XSS)
  - Command injection
  - Insecure deserialization (pickle, yaml, etc.)
  - Weak cryptography
  - XXE (XML parsing without entity restriction)
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from schemas import CodeAnalysis, PolicyState
from utils import get_llm_client, setup_logging, truncate

logger = setup_logging("code_agent")

# ─────────────────────────────────────────────────────────────────────────────
# Vulnerability pattern bank
# Each entry: (regex_pattern, vuln_type, severity 0-1)
# ─────────────────────────────────────────────────────────────────────────────
VULN_PATTERNS: List[Tuple[str, str, float]] = [
    # SQL Injection
    (r"db\.query\s*\(\s*['\"].*\{\s*\w+\s*\}.*['\"]", "sql_injection", 0.9),
    (r"execute\s*\(\s*['\"].*['\"].*\+.*\w+", "sql_injection", 0.85),
    (r"query\s*=\s*['\"].*\+.*['\"]", "sql_injection", 0.8),
    
    # XSS
    (r"innerHTML\s*=|dangerouslySetInnerHTML", "xss", 0.9),
    (r"render_template.*|render\(.*request\.args", "xss", 0.75),
    
    # Command Injection
    (r"os\.system\s*\(.*\+|subprocess\.call.*shell=True", "command_injection", 0.95),
    (r"exec\s*\(.*\+|eval\s*\(", "command_injection", 0.9),
    
    # Insecure Deserialization
    (r"pickle\.loads|yaml\.load\s*\(|json\.loads.*untrusted", "deserialization", 0.85),
    
    # Weak Crypto
    (r"md5|sha1|DES|RC4", "weak_crypto", 0.7),
    (r"random\.random\s*\(|secrets not imported", "weak_rng", 0.8),
    
    # Hardcoded Credentials
    (r"password\s*=\s*['\"]|api_key\s*=\s*['\"]|secret\s*=\s*['\"]", "hardcoded_secret", 0.95),
    
    # Info Disclosure
    (r"app\.run\s*\(\s*debug\s*=\s*True", "info_disclosure", 0.75),
]

CODE_AGENT_SYSTEM_PROMPT = """You are an expert application security engineer (SAST specialist).
Analyze the provided source code and identify all security vulnerabilities.
Return ONLY valid JSON:
{
  "flagged_code": ["vulnerable snippet 1", "vulnerable snippet 2", ...],
  "vulnerability_types": ["sql_injection", "xss", ...],
  "confidence": 0.88
}
flagged_code items must be exact lines or multi-line snippets copied from the input source code.
Be precise — do NOT hallucinate code that isn't present."""

class SecureCodeAgent:
    """Secure Code Agent for detecting source code vulnerabilities."""

    def __init__(self, policy: Optional[PolicyState] = None):
        self.policy = policy or PolicyState()
        self.llm = get_llm_client()

    async def analyze(self, code: str) -> CodeAnalysis:
        """Analyze source code for security vulnerabilities."""
        result = CodeAnalysis()
        
        if not code:
            return result
        
        flagged = set()
        vuln_types = set()
        
        lines = code.split("\n")
        for i, line in enumerate(lines):
            for pattern, vuln_type, severity in VULN_PATTERNS:
                try:
                    if re.search(pattern, line, re.IGNORECASE):
                        flagged.add(line.strip())
                        vuln_types.add(vuln_type)
                except re.error:
                    pass
        
        result.flagged_code = list(flagged)[:20]  # Limit to top 20
        result.vulnerability_types = list(vuln_types)
        result.confidence = min(0.95, 0.5 + len(flagged) * 0.05)
        
        # LLM enhancement if available
        if self.llm.available and code:
            try:
                llm_result = await self.llm.chat_json(
                    CODE_AGENT_SYSTEM_PROMPT,
                    f"Analyze this source code:\n\n{truncate(code, 2000)}"
                )
                if llm_result:
                    result.flagged_code = llm_result.get("flagged_code", result.flagged_code)
                    result.vulnerability_types = llm_result.get("vulnerability_types", result.vulnerability_types)
                    result.confidence = llm_result.get("confidence", result.confidence)
            except Exception as e:
                logger.debug(f"LLM analysis failed: {e}")
        
        return result
