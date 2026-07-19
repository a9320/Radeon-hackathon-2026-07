"""Agent 2: Semantic Analyzer (LLM-driven)

Takes risks from Agent 1 (static) + Agent 3 (semgrep),
uses LLM to verify, deduplicate, and enrich with deeper analysis.
"""

from __future__ import annotations

import json
from typing import Optional

from rich.console import Console

from core.llm_client import LLMClient
from core.models import (
    CodeFile,
    Confidence,
    Evidence,
    Language,
    Risk,
    Severity,
)

console = Console()

SYSTEM_PROMPT = """You are a senior code security auditor. Given:
1. Source code of a file
2. A list of risks found by static analysis

Your tasks:
- VALIDATE each risk: is it a real vulnerability or a false positive?
- ENRICH: provide attack scenario and impact for confirmed risks
- MERGE duplicates: if multiple risks describe the same issue, merge them
- ADD missed risks: if you spot vulnerabilities the static analyzer missed

Output JSON format:
{
  "validated_risks": [
    {
      "id": "RISK-001",
      "is_true_positive": true,
      "attack_scenario": "...",
      "impact": "...",
      "adjusted_severity": "critical|high|medium|low|info",
      "notes": "..."
    }
  ],
  "new_risks": [
    {
      "title": "...",
      "description": "...",
      "severity": "critical|high|medium|low",
      "cwe_id": "CWE-xxx",
      "line_start": 10,
      "line_end": 10,
      "attack_scenario": "...",
      "suggestion": "..."
    }
  ]
}"""


class SemanticAnalyzer:
    """LLM-driven semantic code analyzer."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def analyze(
        self,
        code_file: CodeFile,
        existing_risks: list[Risk],
    ) -> list[Risk]:
        """Verify and enrich existing risks using LLM."""
        if not existing_risks:
            # No risks to validate, but we can still ask LLM to find new ones
            return self._scan_for_new_risks(code_file)

        prompt = self._build_prompt(code_file, existing_risks)

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=4096,
            )
        except Exception as e:
            console.print(f"[yellow]Semantic analysis failed: {e}[/]")
            return existing_risks

        return self._merge_results(existing_risks, response, code_file)

    def _build_prompt(self, code_file: CodeFile, risks: list[Risk]) -> str:
        """Build the analysis prompt."""
        risk_summaries = []
        for r in risks:
            risk_summaries.append(
                f"- {r.id}: [{r.severity.value}] {r.title}\n"
                f"  CWE: {r.cwe_id or 'N/A'} | Lines: {r.line_start}-{r.line_end}\n"
                f"  Desc: {r.description}"
            )

        return f"""## Source File: {code_file.path}
Language: {code_file.language.value}

```{code_file.language.value}
{code_file.content}
```

## Risks Found by Static Analysis
{chr(10).join(risk_summaries)}

Please validate each risk and identify any missed vulnerabilities."""

    def _merge_results(
        self,
        existing_risks: list[Risk],
        llm_response: dict,
        code_file: CodeFile,
    ) -> list[Risk]:
        """Merge LLM validation results with existing risks."""
        validated = llm_response.get("validated_risks", [])
        new_risks_raw = llm_response.get("new_risks", [])

        # Update existing risks based on validation
        risk_map = {r.id: r for r in existing_risks}
        merged: list[Risk] = []

        for v in validated:
            risk_id = v.get("id", "")
            if risk_id not in risk_map:
                continue

            risk = risk_map[risk_id]

            # If LLM says it's a false positive, downgrade to INFO
            if not v.get("is_true_positive", True):
                risk = risk.model_copy(update={
                    "severity": Severity.INFO,
                    "confidence": Confidence.LOW,
                    "description": risk.description + " [LLM: likely false positive]",
                })
            else:
                # Enrich with attack scenario
                scenario = v.get("attack_scenario", "")
                impact = v.get("impact", "")
                notes = v.get("notes", "")
                if scenario or impact or notes:
                    enrichment = []
                    if scenario:
                        enrichment.append(f"Attack: {scenario}")
                    if impact:
                        enrichment.append(f"Impact: {impact}")
                    if notes:
                        enrichment.append(f"Notes: {notes}")
                    risk = risk.model_copy(update={
                        "description": risk.description + " | " + " | ".join(enrichment),
                    })

                # Adjust severity if LLM suggests different
                adj_sev = v.get("adjusted_severity", "").lower()
                if adj_sev and adj_sev in [s.value for s in Severity]:
                    new_sev = Severity(adj_sev)
                    if new_sev != risk.severity:
                        risk = risk.model_copy(update={"severity": new_sev})

            merged.append(risk)

        # Add risks that LLM didn't validate (keep as-is)
        validated_ids = {v.get("id") for v in validated}
        for risk in existing_risks:
            if risk.id not in validated_ids:
                merged.append(risk)

        # Add new risks found by LLM
        counter = len(merged)
        for nr in new_risks_raw:
            counter += 1
            sev_str = nr.get("severity", "medium").lower()
            sev = Severity(sev_str) if sev_str in [s.value for s in Severity] else Severity.MEDIUM

            merged.append(Risk(
                id=f"RISK-{counter:03d}",
                title=nr.get("title", "LLM-detected risk"),
                description=nr.get("description", ""),
                severity=sev,
                confidence=Confidence.MEDIUM,
                cwe_id=nr.get("cwe_id"),
                language=code_file.language,
                file_path=code_file.path,
                line_start=nr.get("line_start", 0),
                line_end=nr.get("line_end", 0),
                evidence=[Evidence(
                    source="ai",
                    snippet="",
                    line_start=nr.get("line_start", 0),
                    line_end=nr.get("line_end", 0),
                    reasoning=f"LLM analysis: {nr.get('attack_scenario', 'detected by semantic analysis')}",
                )],
                suggestion=nr.get("suggestion", "Review this code section."),
            ))

        return merged

    def _scan_for_new_risks(self, code_file: CodeFile) -> list[Risk]:
        """Ask LLM to find risks when no static risks exist."""
        prompt = f"""## Source File: {code_file.path}
Language: {code_file.language.value}

```{code_file.language.value}
{code_file.content}
```

No risks were found by static analysis. Please scan for any security vulnerabilities.

Output JSON:
{{
  "new_risks": [
    {{
      "title": "...",
      "description": "...",
      "severity": "critical|high|medium|low",
      "cwe_id": "CWE-xxx",
      "line_start": 10,
      "line_end": 10,
      "attack_scenario": "...",
      "suggestion": "..."
    }}
  ]
}}"""

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2048,
            )
            return self._merge_results([], response, code_file)
        except Exception as e:
            console.print(f"[yellow]LLM scan failed: {e}[/]")
            return []
