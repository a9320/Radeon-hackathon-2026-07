# CodeRisk Agent 🛡️

**AI-Powered Code Security Analysis — Running Entirely on Your Local AMD GPU**

> Semgrep finds known patterns. CodeRisk Agent understands logic, traces attack paths, and provides exploitability evidence — with LLM inference running entirely on your local AMD GPU. All vulnerability knowledge bases (CWE, CVE, OSV) are bundled locally. No external API calls at runtime.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![ROCm](https://img.shields.io/badge/ROCm-7.2-red.svg)](https://rocm.docs.amd.com/)

---

## Why CodeRisk Agent?

Enterprises need AI-powered code security, but **cannot upload source code to cloud services**. Compliance (HIPAA, GDPR), intellectual property, and corporate policy all prohibit it.

CodeRisk Agent solves this: **deep AI analysis running 100% locally on AMD Radeon GPUs**. Code never leaves the machine.

| Feature | Semgrep | Cloud AI (Copilot) | **CodeRisk Agent** |
|---------|---------|--------------------|--------------------|
| Local execution | ✅ | ❌ | ✅ |
| Understands code logic | ❌ | ✅ | ✅ |
| CVE/NVD integration | ❌ | ❌ | ✅ |
| Self-learning memory | ❌ | ❌ | ✅ |
| Evidence chain | Pattern only | Black box | **Full traceability** |

---

## Architecture

![Architecture Diagram](docs/architecture-diagram.png)


```
User uploads code
        ↓
┌───────────────────┐
│    Orchestrator    │  State machine: INIT → PARSE → ANALYZE → VERIFY → REPORT
└───────┬───────────┘
        ↓
┌───────┴────────┐
│                │
↓                ↓
Agent 1         Agent 2          ← Parallel execution
Static Analyzer  Semantic Analyzer
(CPU + tools)    (GPU + LLM)
│                │
└───────┬────────┘
        ↓
    ┌───┴───┐
    │ Self- │  ← Agent 3 flags missed risks, triggers re-analysis
    │Reflect│
    └───┬───┘
        ↓
    Agent 3                     ← Triple cross-validation
    Deep Verifier               (Tool + Knowledge Base + Local CVE DB)
    (GPU + LLM + Local DB)
        ↓
    Agent 4                     ← Structured reports
    Report Generator            (JSON + Markdown + Terminal)
        ↓
  ┌─────────────┐
  │ Memory Layer │  Correct memory + Error memory
  │  (JSON)      │  "Learns" from every scan
  └─────────────┘
```

### The 4 Agents

| Agent | Role | Compute | What It Does |
|-------|------|---------|--------------|
| **Agent 1: Static Analyzer** | Pattern matching | CPU | 27 detection rules (buffer overflow, format string, double free, command injection, etc.) |
| **Agent 2: Semantic Analyzer** | LLM-driven analysis | GPU | Validates findings, discovers missed vulnerabilities, generates attack scenarios |
| **Agent 3: Deep Verifier** | Triple cross-validation | GPU + CPU | CWE knowledge base + local CVE database + self-reflection loop |
| **Agent 4: Report Generator** | Output formatting | CPU | JSON, Markdown, Rich terminal with CWE/CVE clickable links |

### What Makes It Different

- **Triple Cross-Validation** — Tool confirmation + CWE knowledge base + local CVE database query
- **Self-Reflection Loop** — Agent 3 asks "Did we miss anything?" and re-analyzes
- **Dual Memory** — Correct patterns boost confidence; error patterns suppress false positives
- **Evidence Chain** — Every risk has source code snippet, CWE classification, and reasoning

---

## Quick Start

### Prerequisites

- Python 3.10+
- AMD GPU with ROCm (optional, for GPU acceleration)
- Semgrep (optional, for enhanced static analysis)

### Installation

```bash
git clone https://github.com/a9320/code-risk-agent.git
cd code-risk-agent
pip install -e .
```

### Configuration

```bash
cp .env.example .env
# Edit .env to configure LLM backend
```

Two backends are supported:

| Backend | Use Case | Config |
|---------|----------|--------|
| `local_llama_cpp` | Local GPU inference (recommended) | Set `LOCAL_MODEL_PATH` to GGUF file |
| `local_http` | Local llama-server | Set `LOCAL_HTTP_URL` |

### Data Preparation (One-Time Setup)

Build local vulnerability databases before first use:

```bash
# Download NVD CVE data → data/vuln_db.sqlite (~10-50MB)
python scripts/download_cve_data.py --years 2023 2024 2025 2026

# Download OSV dependency vulnerability data → data/osv/ (~100MB)
python scripts/download_osv_data.py
```

> These scripts download public vulnerability data from NVD and OSV bulk feeds. No API keys required. Data is stored locally — no network calls at runtime.

### Usage

```bash
# Analyze a directory
code-risk analyze ./src/

# Analyze a single file
code-risk analyze vulnerable.c

# Quick demo (no LLM, fast)
code-risk demo

# Show configuration
code-risk info
```

### Options

```bash
code-risk analyze <path> [options]

Options:
  --no-ai                   Disable LLM semantic analysis (fast, CPU-only)
  --semgrep-config <rules>  Semgrep rules (default: p/default)
  --output <format>         Output: terminal|json|md|all (default: terminal)
```

---

## Example Output

```
═══════════════════════════════════════════════════════════
  CodeRisk Agent — Analysis Report
═══════════════════════════════════════════════════════════

  Files analyzed: 5
  Total risks:    47
  Analysis time:  2 min (GPU inference)

  ┌─────────┬──────────┬──────────────────────────────┐
  │ Severity│ CWE      │ Title                        │
  ├─────────┼──────────┼──────────────────────────────┤
  │ CRITICAL│ CWE-120  │ Buffer overflow: strcpy()    │
  │ CRITICAL│ CWE-78   │ Command injection: system()  │
  │ HIGH    │ CWE-415  │ Double free detected         │
  │ HIGH    │ CWE-502  │ Unsafe deserialization       │
  │ MEDIUM  │ CWE-476  │ NULL pointer dereference     │
  └─────────┴──────────┴──────────────────────────────┘

  Each risk includes:
  ✓ Source code evidence with line numbers
  ✓ CWE classification with MITRE link
  ✓ CVE references with NVD link
  ✓ Concrete fix suggestion
═══════════════════════════════════════════════════════════
```

---

## ROCm GPU Acceleration

CodeRisk Agent is optimized for AMD Radeon GPUs via ROCm/HIP.

### Performance

> All performance data was measured on our Radeon Cloud instance
> (Radeon Pro W7900, 48GB VRAM, ROCm 7.2.4, HIP backend).

| Metric | CPU | AMD GPU (HIP) | Speedup |
|--------|-----|---------------|---------|
| Token generation | 6.8 t/s | 105 t/s | **15.4×** |
| Prompt processing | ~40 t/s | 628 t/s | **15.7×** |
| VRAM usage | — | 41% (~19.6 GB / 48 GB) | — |

### Build llama.cpp with ROCm

```bash
# Clone and build with HIP backend
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
ROCM_PATH=/opt/rocm cmake -B build -DGGML_HIP=ON -DLLAMA_BUILD_SERVER=ON
cmake --build build --config Release -j$(nproc)

# Download Qwen2.5-Coder-32B-Instruct GGUF
huggingface-cli download Qwen/Qwen2.5-Coder-32B-Instruct-GGUF \
  qwen2.5-coder-32b-instruct-q4_k_m.gguf --local-dir models/

# Run inference
./build/bin/llama-server -m models/qwen2.5-coder-32b-instruct-q4_k_m.gguf -ngl 999 -fa 1
```

> **Key discovery:** The HIP backend flag changed from `GGML_HIPBLAS=ON` (2024-2025) to `GGML_HIP=ON` (2026). This was the root cause of initial GPU inference failures.

---

## Project Structure

```
code-risk-agent/
├── main.py                    # CLI entry point
├── orchestrator.py            # State machine pipeline
├── agents/
│   ├── static_analyzer.py     # Agent 1: Pattern matching (27 rules, C + Python)
│   ├── semantic_analyzer.py   # Agent 2: LLM-driven analysis
│   ├── deep_verifier.py       # Agent 3: Triple cross-validation
│   └── report_generator.py    # Agent 4: Output formatting
├── core/
│   ├── models.py              # Data models (Risk, CodeFile, etc.)
│   ├── llm_client.py          # Unified LLM client (2 local backends)
│   ├── memory.py              # Dual memory system
│   ├── cve_client.py          # Local CVE database client (SQLite)
│   ├── semgrep_runner.py      # Semgrep integration
│   ├── taint_analyzer.py      # Data flow tracking
│   ├── dependency_scanner.py  # Vulnerable dependency detection (local OSV data)
│   ├── attack_knowledge.py    # CWE/ATT&CK knowledge base
│   └── retry.py               # Unified retry policy
├── tests/
│   ├── test_static_analyzer.py
│   ├── test_cve_client.py
│   ├── test_llm_client.py
│   ├── test_memory.py
│   ├── test_schemas.py
│   └── test_cases/
│       ├── buffer_overflow.c
│       ├── command_injection.c
│       ├── memory_issues.c
│       ├── code_injection.py
│       └── sql_injection.py
├── docs/
│   ├── project-specification.md
│   ├── architecture-review.md
│   ├── module-analysis.md
│   ├── rocm-optimization.md
│   ├── demo-video-script.md
│   └── submission-checklist.md
├── data/                          # Local vulnerability databases
│   ├── vuln_db.sqlite             # CVE data (built by download_cve_data.py)
│   └── osv/
│       └── index.json             # OSV data (built by download_osv_data.py)
├── scripts/
│   ├── run_demo.sh
│   ├── download_cve_data.py       # NVD CVE database builder
│   └── download_osv_data.py       # OSV vulnerability data builder
├── pyproject.toml
└── .env.example
```

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

51 unit tests covering buffer overflow, command injection, code injection, deserialization, and safe code detection.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12 |
| LLM | Qwen2.5-Coder-32B-Instruct (GGUF Q4_K_M) |
| LLM Runtime | llama.cpp with HIP backend |
| Static Analysis | Regex + Semgrep |
| CVE Database | Local SQLite (pre-downloaded from NVD) |
| Dependency Scan | Local OSV data + fallback dictionary |
| Memory | JSON-based dual memory system |
| Output Formats | JSON, Markdown, SARIF 2.1.0, Rich terminal |
| CLI | Rich terminal UI |
| GPU | AMD Radeon Pro W7900 (48GB) + ROCm 7.2.4 |

---

## Team

| Member | Role |
|--------|------|
| **Yang Weike** | Captain / Product / Security Testing |
| **lolo** | Full-stack Development / Architecture |

---

## License

MIT

---

## Runtime Network Policy

CodeRisk Agent performs **zero external network requests** at runtime. All inference, data lookups, and analysis happen locally.

URLs that appear in analysis reports (CWE references, CVE links, MITRE ATT&CK links) are **clickable reference links** for the user's convenience — they open in the user's browser and are never called by the system itself.

| Data Source | How It's Accessed |
|-------------|------------------|
| LLM inference | Local GGUF model via llama.cpp (HIP backend) |
| CVE data | Local SQLite database (`data/vuln_db.sqlite`) |
| OSV data | Local JSON index (`data/osv/index.json`) |
| CWE/ATT&CK knowledge | Local Python dictionaries |
| Report URLs (CWE/CVE/MITRE) | Reference links only — opened by user, not by system |

---

## Known Limitations

- **Radeon Cloud container:** HIP backend requires `GGML_HIP=ON` (not the older `GGML_HIPBLAS=ON`). On bare-metal systems, both flags may work.
- **Language support:** Currently C and Python only. Java, Go, Rust planned for future releases.
- **Taint analysis:** Single-function variable tracking only. Cross-function data flow requires Call Graph (planned).
- **Memory learning:** Requires 2+ scans to activate false positive suppression. Single-run results may include known false positives.
- **Semgrep integration:** Requires Semgrep CLI installed separately. The system works without it but loses one analysis layer.

## Acknowledgments

- [Qwen](https://github.com/QwenLM) for the excellent code model
- [llama.cpp](https://github.com/ggerganov/llama.cpp) for local inference
- [Semgrep](https://semgrep.dev/) for static analysis rules
- [AMD](https://developer.amd.com/) for the Radeon Cloud platform and hackathon
