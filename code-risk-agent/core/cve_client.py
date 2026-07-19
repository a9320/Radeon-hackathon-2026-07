"""CodeRisk Agent - CVE/NVD Client

Queries NVD (National Vulnerability Database) for CVE information.
Used by DeepVerifier for knowledge-base cross-validation.
"""

from __future__ import annotations

import time
from typing import Optional

import httpx
from rich.console import Console

console = Console()

NVD_API_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"
REQUEST_TIMEOUT = 15
RATE_LIMIT_DELAY = 1.0  # NVD rate limit: 5 requests/30s without API key


class CVEClient:
    """Query NVD for CVE information by CWE ID or keyword."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._client = httpx.Client(timeout=REQUEST_TIMEOUT)
        self._cache: dict[str, list[dict]] = {}  # Simple in-memory cache
        self._last_request_time = 0.0

    def query_by_cwe(
        self,
        cwe_id: str,
        max_results: int = 5,
    ) -> list[dict]:
        """Query CVEs associated with a CWE ID.

        Args:
            cwe_id: CWE identifier, e.g. "CWE-120"
            max_results: Maximum number of CVEs to return

        Returns:
            List of CVE summaries with id, description, severity, references
        """
        # Check cache
        cache_key = f"{cwe_id}:{max_results}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Rate limiting
        self._rate_limit()

        params = {
            "cweId": cwe_id,
            "resultsPerPage": max_results,
        }
        if self.api_key:
            params["apiKey"] = self.api_key

        try:
            resp = self._client.get(NVD_API_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            console.print(f"[dim]CVE query failed for {cwe_id}: {e}[/]")
            return []

        vulnerabilities = data.get("vulnerabilities", [])
        results = []

        for vuln in vulnerabilities:
            cve = vuln.get("cve", {})
            cve_id = cve.get("id", "unknown")

            # Extract description
            descriptions = cve.get("descriptions", [])
            desc_en = ""
            for d in descriptions:
                if d.get("lang") == "en":
                    desc_en = d.get("value", "")
                    break

            # Extract severity from CVSS
            metrics = cve.get("metrics", {})
            severity = "unknown"
            cvss_score = 0.0

            # Try CVSS v3.1 first, then v3.0, then v2.0
            for version_key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                version_metrics = metrics.get(version_key, [])
                if version_metrics:
                    cvss_data = version_metrics[0].get("cvssData", {})
                    cvss_score = cvss_data.get("baseScore", 0.0)
                    severity = cvss_data.get("baseSeverity", "unknown").lower()
                    break

            # Extract references
            references = []
            for ref in cve.get("references", [])[:3]:
                references.append(ref.get("url", ""))

            results.append({
                "cve_id": cve_id,
                "description": desc_en[:300],
                "severity": severity,
                "cvss_score": cvss_score,
                "references": references,
            })

        # Cache results
        self._cache[cache_key] = results
        return results

    def has_known_exploits(self, cwe_id: str) -> bool:
        """Check if a CWE has known exploitable CVEs (quick check)."""
        results = self.query_by_cwe(cwe_id, max_results=3)
        # If any CVE has high/critical severity, consider it exploitable
        return any(
            r["severity"] in ("high", "critical") and r["cvss_score"] >= 7.0
            for r in results
        )

    def get_cve_summary(self, cwe_id: str) -> str:
        """Get a brief summary of CVEs for a CWE (for report inclusion)."""
        results = self.query_by_cwe(cwe_id, max_results=3)
        if not results:
            return f"No CVE data found for {cwe_id}"

        summaries = []
        for r in results:
            summaries.append(
                f"{r['cve_id']} ({r['severity']}, CVSS {r['cvss_score']}): "
                f"{r['description'][:100]}..."
            )
        return " | ".join(summaries)

    def _rate_limit(self):
        """Respect NVD rate limits."""
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.monotonic()

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
