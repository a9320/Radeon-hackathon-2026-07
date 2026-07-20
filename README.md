# CodeRisk Agent 🛡️

**AI-Powered Code Security Analysis — Running Entirely on Your Local AMD GPU**

> Semgrep finds known patterns. CodeRisk Agent understands logic, traces attack paths, and provides exploitability evidence — all without sending your code to the cloud.

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
    Deep Verifier               (Tool + Knowledge Base + CVE)
    (GPU + LLM + NVD API)
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
| **Agent 1: Static Analyzer** | Pattern matching | CPU | 11 CWE rules (buffer overflow, format string, double free, command injection, etc.) |
| **Agent 2: Semantic Analyzer** | LLM-driven analysis | GPU | Validates findings, discovers missed vulnerabilities, generates attack scenarios |
| **Agent 3: Deep Verifier** | Triple cross-validation | GPU + CPU | CWE knowledge base + live CVE/NVD lookup + self-reflection loop |
| **Agent 4: Report Generator** | Output formatting | CPU | JSON, Markdown, Rich terminal with CWE/CVE clickable links |

### What Makes It Different

- **Triple Cross-Validation** — Tool confirmation + CWE knowledge base + live NVD query
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

Three backends are supported:

| Backend | Use Case | Config |
|---------|----------|--------|
| `local_llama_cpp` | Local GPU inference (recommended) | Set `LOCAL_MODEL_PATH` to GGUF file |
| `local_http` | Local llama-server | Set `LOCAL_HTTP_URL` |
| `shared_api` | Radeon Cloud shared API | Set `SHARED_API_KEY` |

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
  Total risks:    25
  Analysis time:  18 min (GPU inference)

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

| Metric | CPU | AMD GPU (HIP) | Speedup |
|--------|-----|---------------|---------|
| Token generation | 6.8 t/s | 105 t/s | **15.4×** |
| Prompt processing | — | 628 t/s | — |
| VRAM usage | — | 24% (~5 GB) | — |

### Build llama.cpp with ROCm

```bash
# Clone and build with HIP backend
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
ROCM_PATH=/opt/rocm cmake -B build -DGGML_HIP=ON -DLLAMA_BUILD_SERVER=ON
cmake --build build --config Release -j$(nproc)

# Download Qwen2.5-Coder-7B-Instruct GGUF
huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct-GGUF \
  qwen2.5-coder-7b-instruct-q4_k_m.gguf --local-dir models/

# Run inference
./build/bin/llama-server -m models/qwen2.5-coder-7b-instruct-q4_k_m.gguf -ngl 999 -fa 1
```

> **Key discovery:** The HIP backend flag changed from `GGML_HIPBLAS=ON` (2024-2025) to `GGML_HIP=ON` (2026). This was the root cause of initial GPU inference failures.

---

## Project Structure

```
code-risk-agent/
├── main.py                    # CLI entry point
├── orchestrator.py            # State machine pipeline
├── agents/
│   ├── static_analyzer.py     # Agent 1: Pattern matching (11 CWE rules)
│   ├── semantic_analyzer.py   # Agent 2: LLM-driven analysis
│   ├── deep_verifier.py       # Agent 3: Triple cross-validation
│   └── report_generator.py    # Agent 4: Output formatting
├── core/
│   ├── models.py              # Data models (Risk, CodeFile, etc.)
│   ├── llm_client.py          # Unified LLM client (3 backends)
│   ├── memory.py              # Dual memory system
│   ├── cve_client.py          # NVD API client
│   ├── semgrep_runner.py      # Semgrep integration
│   ├── taint_analyzer.py      # Data flow tracking
│   ├── dependency_scanner.py  # Vulnerable dependency detection
│   └── attack_knowledge.py    # CWE/ATT&CK knowledge base
├── tests/
│   └── test_static_analyzer.py
├── docs/
│   ├── project-specification.md
│   ├── rocm-optimization.md
│   ├── demo-video-script.md
│   └── submission-checklist.md
├── scripts/
│   └── run_demo.sh
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

13 unit tests covering buffer overflow, command injection, code injection, deserialization, and safe code detection.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12 |
| LLM | Qwen2.5-Coder-7B-Instruct (GGUF Q4_K_M) |
| LLM Runtime | llama.cpp with HIP backend |
| Static Analysis | Regex + Tree-sitter + Semgrep |
| CVE Database | NVD API (National Vulnerability Database) |
| Memory | JSON-based dual memory system |
| CLI | Rich terminal UI |
| GPU | AMD Radeon RX 7900 XTX + ROCm 7.2.4 |

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

## Acknowledgments

- [Qwen](https://github.com/QwenLM) for the excellent code model
- [llama.cpp](https://github.com/ggerganov/llama.cpp) for local inference
- [Semgrep](https://semgrep.dev/) for static analysis rules
- [AMD](https://developer.amd.com/) for the Radeon Cloud platform and hackathon
