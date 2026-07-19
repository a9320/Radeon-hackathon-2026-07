"""Dependency Scanner Module

Inspired by Vuls - scans project dependencies for known vulnerabilities.
Checks requirements.txt, package.json, pyproject.toml for outdated/vulnerable packages.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()

# Known vulnerable package versions (simplified - in production use OSV/NVD API)
VULNERABLE_PACKAGES = {
    # Python
    "django": {
        "vulnerable_below": "4.2.0",
        "cwe": "CWE-89",
        "description": "Old Django versions have SQL injection vulnerabilities",
    },
    "flask": {
        "vulnerable_below": "2.3.0",
        "cwe": "CWE-79",
        "description": "Old Flask versions have XSS vulnerabilities",
    },
    "requests": {
        "vulnerable_below": "2.31.0",
        "cwe": "CWE-295",
        "description": "Old requests versions have certificate verification issues",
    },
    "pyyaml": {
        "vulnerable_below": "6.0",
        "cwe": "CWE-502",
        "description": "Old PyYAML versions allow arbitrary code execution via yaml.load()",
    },
    "pillow": {
        "vulnerable_below": "10.0.0",
        "cwe": "CWE-120",
        "description": "Old Pillow versions have buffer overflow vulnerabilities",
    },
    "cryptography": {
        "vulnerable_below": "41.0.0",
        "cwe": "CWE-327",
        "description": "Old cryptography versions have weak algorithm support",
    },
    # JavaScript
    "lodash": {
        "vulnerable_below": "4.17.21",
        "cwe": "CWE-1321",
        "description": "Old lodash versions have prototype pollution vulnerability",
    },
    "express": {
        "vulnerable_below": "4.18.0",
        "cwe": "CWE-1321",
        "description": "Old Express versions have open redirect vulnerabilities",
    },
    "axios": {
        "vulnerable_below": "1.6.0",
        "cwe": "CWE-918",
        "description": "Old Axios versions have SSRF vulnerability",
    },
}


def _parse_version(version_str: str) -> tuple[int, ...]:
    """Parse version string to tuple for comparison."""
    # Remove leading ^, ~, >=, <=, ==, !=, etc.
    cleaned = re.sub(r'^[><=!~^]+', '', version_str.strip())
    parts = []
    for p in cleaned.split('.'):
        try:
            parts.append(int(p))
        except ValueError:
            break
    return tuple(parts) if parts else (0,)


def _version_below(current: str, threshold: str) -> bool:
    """Check if current version is below threshold."""
    return _parse_version(current) < _parse_version(threshold)


def scan_requirements_txt(file_path: Path) -> list[dict]:
    """Scan Python requirements.txt for vulnerable packages."""
    findings = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings

    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        # Parse package==version or package>=version
        match = re.match(r'^([a-zA-Z0-9_-]+)\s*[><=!~]+\s*([0-9][0-9.]*)', line)
        if match:
            pkg_name = match.group(1).lower()
            version = match.group(2)
            if pkg_name in VULNERABLE_PACKAGES:
                vuln = VULNERABLE_PACKAGES[pkg_name]
                if _version_below(version, vuln["vulnerable_below"]):
                    findings.append({
                        "package": pkg_name,
                        "version": version,
                        "cwe": vuln["cwe"],
                        "description": vuln["description"],
                        "fix": f"Upgrade {pkg_name} to >= {vuln['vulnerable_below']}",
                    })

    return findings


def scan_package_json(file_path: Path) -> list[dict]:
    """Scan Node.js package.json for vulnerable packages."""
    findings = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        data = json.loads(content)
    except Exception:
        return findings

    deps = {}
    deps.update(data.get("dependencies", {}))
    deps.update(data.get("devDependencies", {}))

    for pkg_name, version in deps.items():
        pkg_lower = pkg_name.lower()
        if pkg_lower in VULNERABLE_PACKAGES:
            vuln = VULNERABLE_PACKAGES[pkg_lower]
            # Extract version number from semver range
            clean_version = re.sub(r'^[><=!~^]+', '', version.strip())
            if clean_version and _version_below(clean_version, vuln["vulnerable_below"]):
                findings.append({
                    "package": pkg_name,
                    "version": version,
                    "cwe": vuln["cwe"],
                    "description": vuln["description"],
                    "fix": f"Upgrade {pkg_name} to >= {vuln['vulnerable_below']}",
                })

    return findings


def scan_project_dependencies(project_path: Path) -> list[dict]:
    """Scan a project directory for dependency vulnerabilities."""
    all_findings = []

    # Check requirements.txt
    req_file = project_path / "requirements.txt"
    if req_file.exists():
        findings = scan_requirements_txt(req_file)
        for f in findings:
            f["file"] = str(req_file)
        all_findings.extend(findings)

    # Check pyproject.toml (simplified)
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            # Extract dependencies section
            deps_match = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if deps_match:
                for line in deps_match.group(1).split("\n"):
                    match = re.match(r'^\s*"([a-zA-Z0-9_-]+)[><=!~]*([0-9][0-9.]*)', line)
                    if match:
                        pkg_name = match.group(1).lower()
                        version = match.group(2)
                        if pkg_name in VULNERABLE_PACKAGES:
                            vuln = VULNERABLE_PACKAGES[pkg_name]
                            if _version_below(version, vuln["vulnerable_below"]):
                                all_findings.append({
                                    "package": pkg_name,
                                    "version": version,
                                    "cwe": vuln["cwe"],
                                    "description": vuln["description"],
                                    "fix": f"Upgrade {pkg_name} to >= {vuln['vulnerable_below']}",
                                    "file": str(pyproject),
                                })
        except Exception:
            pass

    # Check package.json
    pkg_json = project_path / "package.json"
    if pkg_json.exists():
        findings = scan_package_json(pkg_json)
        for f in findings:
            f["file"] = str(pkg_json)
        all_findings.extend(findings)

    return all_findings
