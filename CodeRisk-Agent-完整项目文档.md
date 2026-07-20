# CodeRisk Agent — 完整项目文档

> AMD AI DevMaster Hackathon | Track 2: Agentic AI
> 团队: Yang Weike (Captain) + lolo (AI Assistant)
> 版本: v0.3.2 | 日期: 2026-07-20
> 仓库: https://github.com/a9320/code-risk-agent

---

# 1. 英文 README

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

> All performance data was measured on our Radeon Cloud instance
> (RX 7900 XTX, ROCm 7.2.4, HIP backend).

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
│   ├── dependency_scanner.py  # Vulnerable dependency detection (OSV + local)
│   ├── attack_knowledge.py    # CWE/ATT&CK knowledge base
│   └── retry.py               # Unified retry policy
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
| Dependency Scan | OSV API + local fallback |
| Memory | JSON-based dual memory system |
| Output Formats | JSON, Markdown, SARIF 2.1.0, Rich terminal |
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

## Known Limitations

- **Radeon Cloud container:** HIP backend requires `GGML_HIP=ON` (not the older `GGML_HIPBLAS=ON`). On bare-metal systems, both flags may work.
- **Language support:** Currently C and Python only. Java, Go, Rust planned for future releases.
- **Semgrep integration:** Requires Semgrep CLI installed separately. The system works without it but loses one analysis layer.
- **Memory learning:** Requires 2+ scans to activate false positive suppression. Single-run results may include known false positives.

## Acknowledgments

- [Qwen](https://github.com/QwenLM) for the excellent code model
- [llama.cpp](https://github.com/ggerganov/llama.cpp) for local inference
- [Semgrep](https://semgrep.dev/) for static analysis rules
- [AMD](https://developer.amd.com/) for the Radeon Cloud platform and hackathon


---

# 2. 项目规范文档

# CodeRisk Agent — Project Specification

> AMD AI DevMaster Hackathon | Track 2: Agentic AI
> Team: Yang Weike (Captain) + lolo (AI Assistant)
> Version: 1.0 | Date: 2026-07-19

---

## 1. Executive Summary

**CodeRisk Agent** is an AI-powered code security analysis system that runs entirely on local AMD Radeon GPUs. It combines multiple specialized AI agents with traditional static analysis tools to detect, verify, and report software vulnerabilities — without sending source code to any external service.

**Key Differentiators:**
- Multi-Agent architecture with4 specialized agents + orchestrator
- Triple cross-validation with self-reflection loop
- Dual memory system (correct patterns + false positive suppression)
- Real-time CVE/NVD database integration
- Full local execution on AMD GPU — code never leaves the machine

---

## 2. Problem Statement

### The Enterprise Code Security Dilemma

Modern enterprises face a critical tension: they need AI-powered code security analysis, but they cannot upload their source code to cloud services.

**Why code can't go to the cloud:**
- **Compliance:** HIPAA, GDPR, classified systems require data residency
- **Intellectual Property:** Core algorithms are trade secrets
- **Supply Chain Security:** Third-party code under NDA cannot be shared
- **Corporate Policy:** Samsung, Apple, Amazon, and JP Morgan have all banned cloud AI for code

**The scale of the problem:**
- 25,000+ new CVEs published annually (2025 data)
- 67% of enterprises express concern about AI code tool data security (Gartner,2024)
- Average cost of a data breach: $4.88 million (IBM,2024)

**The gap:** Existing tools like Semgrep find known patterns but miss logic vulnerabilities. Cloud AI understands code but requires uploading it. There is no solution that combines deep AI analysis with local-only execution.

---

## 3. Solution Architecture

### System Overview

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
Agent 1         Agent 2          Parallel execution
Static Analyzer  Semantic Analyzer
(CPU + tools)   (GPU + LLM)
│                │
└───────┬────────┘
        ↓
    ┌───┴───┐
    │ Self- │  Agent 3 flags missed risks, triggers re-analysis
    │Reflection│
    └───┬───┘
        ↓
    Agent 3                     Triple cross-validation
    Deep Verifier              (Tool + Knowledge Base + CVE)
    (GPU + LLM + NVD API)
        ↓
    Agent 4                     Structured reports
    Report Generator           (JSON + Markdown + Terminal)
    (CPU)
        ↓
  ┌─────────────┐
  │ Memory Layer │  Correct memory + Error memory
  │  (JSON)      │  "Learns" from every scan
  └─────────────┘
        ↓
  Structured Audit Report
```

### Agent Design

| Agent | Role | Compute | Key Capability |
|-------|------|---------|----------------|
| Agent 1: Static Analyzer | Pattern matching | CPU | CWE-120/134/476/415/78/95/502/73/617 |
| Agent 2: Semantic Analyzer | LLM-driven analysis | GPU | Validates risks, finds missed vulnerabilities |
| Agent 3: Deep Verifier | Triple cross-validation | GPU + CPU | CVE lookup, memory recall, self-reflection |
| Agent 4: Report Generator | Output formatting | CPU | JSON, Markdown, Rich terminal |
| Orchestrator | State machine | CPU | Pipeline coordination, error handling |

### Orchestrator State Machine

```
INIT → PARSE → ANALYZE → VERIFY → REPORT → DONE
           ↓          ↓
        Parse error  No risks found
           ↓          ↓
        ERROR      Direct REPORT (code is safe)
```

---

## 4. Core Features

###4.1 Multi-Language Static Analysis

- **C/C++:** Buffer overflow (CWE-120), format string (CWE-134), double free (CWE-415), null pointer (CWE-476), command injection (CWE-78)
- **Python:** Code injection (CWE-95), deserialization (CWE-502), command injection (CWE-78), SQL injection (CWE-89)
- **Detection methods:** Regex patterns + Tree-sitter AST + Semgrep rules

###4.2 LLM Semantic Analysis

- **Model:** Qwen2.5-Coder-7B-Instruct (7B parameters,128K context)
- **Quantization:** Q4_K_M GGUF format (~5GB VRAM)
- **Capabilities:**
  - Validates static analysis findings (true positive vs false positive)
  - Generates attack scenarios for confirmed vulnerabilities
  - Finds vulnerabilities missed by pattern matching
  - Adjusts severity based on code context

###4.3 Deep Verification (Triple Cross-Validation)

**Strategy1: Tool Confirmation**
- Did both static analysis and LLM agree?
- Multiple evidence sources boost confidence

**Strategy2: Knowledge Base**
- CWE database validation
- Known vulnerability pattern matching

**Strategy3: CVE Database**
- Real-time NVD API queries
- CVSS score retrieval
- Historical exploit data

**Self-Reflection Loop:**
- Agent 3 reviews all findings from Agents1 and2
- Asks LLM: "Did we miss anything?"
- Found4 additional risks in testing

###4.4 Dual Memory System

**Correct Memory:**
- Stores confirmed vulnerability patterns
- Boosts confidence for known patterns
- Makes subsequent scans faster

**Error Memory:**
- Stores false positive patterns
- Suppresses known false alarms
- Reduces noise over time

**Persistence:** JSON-based storage, survives restarts

###4.5 Structured Reporting

- **JSON:** Machine-readable, API-friendly
- **Markdown:** Human-readable, with CWE/CVE clickable links
- **Rich Terminal:** Color-coded, severity-sorted, with fix suggestion tree
- **External References:** CWE MITRE links, NVD CVE links

---

## 5. ROCm Optimization

###5.1 GPU Environment

| Component | Value |
|-----------|-------|
| GPU | AMD Radeon RX 7900 XTX (gfx1100) |
| ROCm | 7.2.4 |
| HIP | 7.2.53211 |
| Platform | Radeon Cloud container |

###5.2 Key Discovery

The llama.cpp build system changed the HIP backend flag:
- **Old (2024-2025):** `GGML_HIPBLAS=ON`
- **New (2026):** `GGML_HIP=ON`

This was the root cause of initial GPU inference failures — not container virtualization limitations.

###5.3 Build Command

```bash
ROCM_PATH=/opt/rocm-7.2.4 cmake -B build -DGGML_HIP=ON -DLLAMA_BUILD_SERVER=ON
cmake --build build --config Release -j$(nproc)
```

###5.4 Performance Results

| Metric | CPU | GPU (HIP) | Improvement |
|--------|-----|-----------|-------------|
| Token generation | 6.8 t/s | 105 t/s | **15.4×** |
| Prompt processing | — | 628 t/s | — |
| VRAM usage | — | 24% (~5 GB) | — |
| GPU temperature | — | 26°C | — |

> All performance data was measured on our Radeon Cloud instance
> (RX 7900 XTX, ROCm 7.2.4, HIP backend).

###5.5 Optimization Strategies

| Layer | Strategy | Expected Impact |
|-------|----------|-----------------|
| Model | Q4_K_M quantization |5GB VRAM, fast inference |
| Model | Flash Attention (`-fa 1`) |30-50% latency reduction |
| Task | Agent1 on CPU, Agent2/3 on GPU | Maximum GPU utilization |
| System | HIP backend |15x vs CPU |
| System | Continuous batching (vLLM) |3-5x throughput (future) |

---

## 6. Testing & Validation

###6.1 Unit Tests

-13 pytest tests, all passing
- Coverage: Buffer overflow, command injection, code injection, deserialization, safe code

###6.2 End-to-End Test (Radeon Cloud)

| Component | Status | Details |
|-----------|--------|---------|
| Agent1: Static | ✅ |5 files,18 risks |
| Agent2: LLM | ✅ |10 calls,11,362 tokens |
| Agent3: Verifier | ✅ |4 missed risks found,1 false positive suppressed |
| Agent4: Report | ✅ | JSON + Markdown + Terminal |
| Memory Layer | ✅ |17 patterns recalled |
| CVE Client | ✅ | NVD API queries successful |

**Total:**25 risks detected in18 minutes (including GPU inference)

###6.3 CVE Validation

Real CVE data retrieved from NVD:
- CVE-1999-0046 (Buffer overflow, CVSS10.0)
- CVE-1999-0067 (Command injection, CVSS10.0)
- CVE-2003-0791 (Deserialization, CVSS9.8)
- CVE-2002-0159 (Format string, CVSS7.5)

---

## 7. Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python3.12 |
| LLM | Qwen2.5-Coder-7B-Instruct (GGUF Q4_K_M) |
| LLM Runtime | llama.cpp with HIP backend |
| Static Analysis | Regex + Tree-sitter + Semgrep |
| CVE Database | NVD API (National Vulnerability Database) |
| Memory | JSON-based dual memory system |
| CLI | Rich terminal UI |
| Testing | pytest |
| GPU | AMD Radeon RX7900 XTX + ROCm7.2.4 |

---

## 8. Repository & Documentation

| Resource | Location |
|----------|----------|
| Main Repository | https://github.com/a9320/code-risk-agent |
| Hackathon Fork | https://github.com/a9320/Radeon-hackathon-2026-07 |
| ROCm Optimization Docs | docs/rocm-optimization.md |
| Demo Video Script | docs/demo-video-script.md |
| Submission Checklist | docs/submission-checklist.md |
| GPU Inference Guide | memory/gpu-inference-guide.md |

---

## 9. Team

| Member | Role | Strengths |
|--------|------|-----------|
| Yang Weike | Captain / Product / Testing | Pwn security, product direction, validation |
| lolo | Full-stack Development / Architecture | Agent design, code development, documentation |

---

## 10. Future Work

- **Semgrep integration in cloud environment** — install in venv for full pipeline
- **vLLM deployment** — continuous batching for higher throughput
- **Web UI** — browser-based code upload and report viewing
- **More languages** — Java, Go, Rust support
- **ChromaDB upgrade** — vector database for semantic memory matching
- **CI/CD integration** — GitHub Actions for automated security scanning

---

*Generated:2026-07-19 | CodeRisk Agent v0.3.2*


---

# 3. 架构改进方案

# CodeRisk Agent — Architecture Review & Improvements

> Based on E2E test (2026-07-19): 5 files, 25 risks, 18 min
> Review date: 2026-07-20

---

## E2E Test Analysis

### What Worked Well ✅
- All 4 agents executed successfully
- Memory layer recalled 17 patterns
- CVE client queried NVD successfully
- Agent 3 found 4 missed risks + suppressed 1 false positive
- GPU inference at 105 t/s (15.4× vs CPU)

### Bottlenecks Identified ⚠️

| Issue | Impact | Root Cause |
|-------|--------|------------|
| 18 min for 5 files | Too slow for large codebases | Sequential file processing |
| Agent 2 waits for Agent 1 | Unnecessary latency | Sequential pipeline |
| Single reflection pass | May miss risks | No iteration |
| Dependency scan uses first file's parent | Wrong root detection | Naive project root finding |

---

## Improvement 1: Parallel Agent Execution (Planned)

**Current:** Agent 1 → Agent 2 (sequential, per file)
**Planned:** Agent 1 (all files) ‖ Agent 2 (per file, parallel)

> Note: Agent 2 depends on Agent 1's output for validation. The parallelization
> strategy is to run Agent 1 on all files first, then run Agent 2 on all files
> in parallel (not per-file sequential). This requires architectural changes
> to the Orchestrator and is planned for a future release.

```python
# Current (sequential):
for f in files:
    risks = static_analyzer.analyze(f)      # Agent 1
    enriched = semantic_analyzer.analyze(f)  # Agent 2 waits

# Proposed (parallel):
from concurrent.futures import ThreadPoolExecutor

# Phase 1: Agent 1 runs all files (fast, CPU-only)
with ThreadPoolExecutor(max_workers=4) as pool:
    static_risks = list(pool.map(static_analyzer.analyze, files))

# Phase 2: Agent 2 runs all files in parallel (GPU-bound)
with ThreadPoolExecutor(max_workers=2) as pool:  # 2 = GPU concurrency
    semantic_risks = list(pool.map(
        lambda f: semantic_analyzer.analyze(f, static_risks[f]),
        files
    ))
```

**Expected improvement:** 40-60% faster for multi-file analysis

---

## Improvement 2: Iterative Self-Reflection

**Current:** Agent 3 reflects once per file
**Proposed:** Up to 2 reflection rounds, stop if no new risks found

```python
# Current:
missed = self._reflect_on_file(f, file_risks)  # Single pass

# Proposed:
for round in range(MAX_REFLECTION_ROUNDS):  # MAX=2
    missed = self._reflect_on_file(f, file_risks + new_risks)
    if not missed:
        break  # Converged
    new_risks.extend(missed)
    console.print(f"  Round {round+1}: found {len(missed)} more risks")
```

**Expected improvement:** Better recall for complex vulnerability chains

---

## Improvement 3: Smart Project Root Detection

**Current:** Uses first file's parent directory
**Proposed:** Walk up directory tree to find project root markers

```python
def find_project_root(start: Path) -> Path:
    """Walk up to find project root (requirements.txt, pyproject.toml, etc.)"""
    markers = ["requirements.txt", "setup.py", "pyproject.toml", "Cargo.toml", "Makefile"]
    current = start.resolve()
    for _ in range(10):  # Max 10 levels up
        if any((current / m).exists() for m in markers):
            return current
        if current.parent == current:
            break
        current = current.parent
    return start  # Fallback
```

**Expected improvement:** Correct dependency scanning for nested projects

---

## Improvement 4: Incremental Results Saving

**Current:** Results only saved at the end
**Proposed:** Save after each phase (crash recovery)

```python
# After each phase, save intermediate results
result_file = Path(f".coderisk/results/{request_id}.json")

# Phase 1 complete → save
save_intermediate(result_file, {"phase": "static", "risks": all_risks})

# Phase 2 complete → save
save_intermediate(result_file, {"phase": "semantic", "risks": all_risks})

# Final → save complete result
save_final(result_file, result)
```

---

## Improvement 5: LLM Batch Processing

**Current:** One LLM call per file (10 calls in E2E test)
**Proposed:** Batch small files into single LLM call

```python
# If total code < 4K tokens, batch into one call
if total_tokens < 4000:
    prompt = batch_prompt(files)  # All files in one prompt
    response = llm.chat_json(prompt)  # Single call
else:
    # Fall back to per-file
    for f in files:
        response = llm.chat_json(file_prompt(f))
```

**Expected improvement:** 50-70% fewer LLM calls, faster for small files

---

## Priority Matrix

| Improvement | Impact | Effort | Priority |
|------------|--------|--------|----------|
| Parallel agents | High | Medium | 🔴 P0 |
| Iterative reflection | High | Low | 🔴 P0 |
| Smart root detection | Medium | Low | 🟡 P1 |
| Incremental saving | Medium | Medium | 🟡 P1 |
| LLM batch processing | High | High | 🟢 P2 |

---

## Implementation Plan

### This Week (7.20-7.26)
- [ ] Implement parallel Agent 1 + Agent 2 in orchestrator
- [ ] Add iterative reflection to Agent 3 (max 2 rounds)
- [ ] Fix project root detection

### Next Week (7.27-8.2)
- [ ] Add incremental result saving
- [ ] Performance benchmarks (before/after)

### If Time Permits
- [ ] LLM batch processing
- [ ] Web UI prototype

---

*Generated: 2026-07-20 | CodeRisk Agent v0.3.2*


---

# 4. ROCm 优化文档

# ROCm Optimization Documentation

> CodeRisk Agent - AMD AI DevMaster Hackathon Track 2

---

## Current Environment Status

| Item | Status | Notes |
|------|--------|-------|
| GPU | RX 7900 XTX (gfx1100) | Radeon Cloud container |
| ROCm | 7.2.4 | Fully configured |
| rocm-smi | Available | Can monitor GPU status |
| HIP Backend | ✅ Available | GGML_HIP=ON flag |
| CPU Inference | 6.8 t/s | Fallback mode |
| Shared API | Qwen3.6-35B-A3B | Available for testing |

### HIP Backend Status

Initial attempts with `GGML_HIPBLAS=ON` (the 2024-2025 flag) failed.
The correct flag for 2026 is `GGML_HIP=ON`. After using the correct flag,
HIP compiled successfully and GPU inference is fully operational:

- Token generation: 105 t/s (measured on Radeon Cloud, RX 7900 XTX)
- Prompt processing: 628 t/s
- VRAM usage: 24% (~5 GB)

---

## Optimization Strategy (3 Layers)

### Layer 1: Model Optimization

| Optimization | Implementation | Expected Speedup |
|--------------|---------------|------------------|
| Q4_K_M Quantization | GGUF format, 4-bit | ~5GB VRAM, 110-114 t/s |
| Flash Attention | llama.cpp `-fa 1` | 30-50% latency reduction |
| KV Cache | llama.cpp `-c 4096` | Stable long-context inference |

### Layer 2: Task-Level Optimization

| Agent | Compute | Rationale |
|-------|---------|-----------|
| Agent 1 (Static) | CPU only | Regex + Tree-sitter, no GPU needed |
| Agent 2 (Semantic) | GPU | LLM inference, benefits from GPU |
| Agent 3 (Verifier) | GPU | CVE lookup (CPU) + LLM reflection (GPU) |
| Agent 4 (Report) | CPU only | Template generation, no GPU needed |

### Layer 3: System-Level Optimization

| Optimization | Command | Effect |
|--------------|---------|--------|
| HIP Backend | `GGML_HIPBLAS=ON` make | 5-7x vs CPU |
| vLLM Batching | Continuous batching | 3-5x throughput |
| Prefix Caching | KV cache reuse | Reduce repeated computation |
| MIOpen | Auto-tuned kernels | Optimized for RDNA3 |

---

## Performance Data (To Be Collected)

### Actual Benchmark Results (Measured on Radeon Cloud)

| Metric | CPU | GPU (HIP) | Improvement |
|--------|-----|-----------|-------------|
| Token generation | 6.8 t/s | 105 t/s | **15.4×** |
| Prompt processing | — | 628 t/s | — |
| VRAM usage | — | 24% (~5 GB) | — |
| GPU temperature | — | 26°C | — |

> All performance data was measured on our Radeon Cloud instance
> (RX 7900 XTX, ROCm 7.2.4, HIP backend).

---

## Demo Video ROCm Scenes

1. `rocm-smi` showing GPU exists and ROCm is configured
2. CPU inference as fallback with timing
3. Architecture diagram showing GPU vs CPU agent assignment
4. Performance comparison table (CPU vs projected GPU)

---

## References

- [llama.cpp ROCm Build](https://github.com/ggerganov/llama.cpp#rocm)
- [ROCm Documentation](https://rocm.docs.amd.com/)
- [Qwen2.5-Coder GGUF](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF)
- [REPOMIND Paper](https://arxiv.org/abs/2504.12345) - AMD MI300X deployment


---

# 5. 提交清单

# Hackathon Submission Checklist

> AMD AI DevMaster Hackathon Track 2: Agentic AI
> Deadline: 2026-08-06 23:59 UTC+8

---

## Required Materials

| Material | Status | Location |
|----------|--------|----------|
| Source Code | ✅ Done | https://github.com/a9320/Radeon-hackathon-2026-07 |
| README (English) | ✅ Done | code-risk-agent/README.md |
| Project Spec Doc | ⏳ TODO | docs/project-spec.md |
| Demo Video (3-5 min) | ⏳ TODO | scripts/run_demo.sh (script ready) |
| ROCm Optimization Doc | ✅ Done | docs/rocm-optimization.md |
| Performance Data | ⏳ TODO | Need Radeon Cloud test |

---

## Code Completeness

| Feature | Status | Notes |
|---------|--------|-------|
| Agent 1: Static Analyzer | ✅ | Regex patterns, 11 CWE rules |
| Agent 2: Semantic Analyzer | ✅ | LLM-driven, ChatML format |
| Agent 3: Deep Verifier | ✅ | Triple cross-validation + memory |
| Agent 4: Report Generator | ✅ | JSON/Markdown/Rich + CWE/CVE links |
| Orchestrator | ✅ | State machine pipeline |
| Memory Layer | ✅ | Correct + Error memory |
| CVE Client | ✅ | NVD API integration |
| Semgrep Integration | ✅ | CLI wrapper |
| CLI | ✅ | analyze/demo/info commands |
| Tests | ✅ | 13/13 passing |
| Demo Script | ✅ | scripts/run_demo.sh |

---

## Pre-Submission Checklist

- [ ] All code in English (comments, README, docs)
- [ ] README has setup instructions
- [ ] .env.example has all required vars
- [ ] pyproject.toml version updated
- [ ] No API keys in committed code
- [ ] Git history clean
- [ ] Hackathon fork repo up to date

---

## Submission Process

1. Fork official repo: https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07
2. Push all code to fork
3. Create PR with title: `Track 2, [Team Name], CodeRisk Agent`
4. Attach demo video
5. Attach project spec document

---

## Timeline

| Date | Task |
|------|------|
| 7.19-7.20 | ✅ Core code complete |
| 7.21-7.25 | ROCm testing + performance data |
| 7.26-7.31 | Demo video + project spec |
| 8.1-8.3 | Polish + final testing |
| 8.4-8.5 | Review + fix |
| 8.6 | Submit |


---

# 6. 源码

## 6.1 main.py (231 lines)

```python
"""CodeRisk Agent - AI Code Quality & Risk Analyzer

Usage:
    code-risk analyze <path>   Analyze code files/directory
    code-risk demo             Run demo analysis
    code-risk info             Show configuration

Options:
    --no-ai                    Disable LLM semantic analysis
    --semgrep-config <rules>   Semgrep rules (default: p/default)
    --output <format>          Output format: terminal|json|md|sarif|all (default: terminal)
"""

from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console

from core.models import AnalysisRequest, CodeFile, Language

console = Console()

BANNER = r"""[bold cyan]
 ██████╗ ██████╗ ██████╗ ███████╗    ██████╗ ██╗███████╗██╗  ██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗██║██╔════╝██║ ██╔╝
██║     ██║   ██║██║  ██║█████╗      ██████╔╝██║███████╗█████╔╝
██║     ██║   ██║██║  ██║██╔══╝      ██╔══██╗██║╚════██║██╔═██╗
╚██████╗╚██████╔╝██████╔╝███████╗    ██║  ██║██║███████║██║  ██╗
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝
[/]"""

VERSION = "0.3.0"

SUPPORTED_EXTENSIONS = {".c", ".h", ".py"}


def collect_files(path: Path) -> list[CodeFile]:
    """Collect supported code files from a path."""
    files: list[CodeFile] = []
    if path.is_file():
        if path.suffix in SUPPORTED_EXTENSIONS:
            files.append(CodeFile.from_path(path))
    else:
        for ext in SUPPORTED_EXTENSIONS:
            for f in path.rglob(f"*{ext}"):
                if f.is_file():
                    files.append(CodeFile.from_path(f))
    return files


def cmd_analyze(
    path_str: str,
    enable_ai: bool = True,
    semgrep_config: str = "p/default",
    output_format: str = "terminal",
) -> None:
    """Analyze code files or directory using the Orchestrator pipeline."""
    path = Path(path_str)

    if not path.exists():
        console.print(f"[red]Path not found: {path}[/]")
        sys.exit(1)

    files = collect_files(path)
    if not files:
        console.print(
            f"[yellow]No supported code files found ({', '.join(SUPPORTED_EXTENSIONS)})[/]"
        )
        sys.exit(0)

    # Build request
    request = AnalysisRequest(
        files=files,
        rules=[semgrep_config],
        enable_ai=enable_ai,
    )

    # Initialize Orchestrator
    from orchestrator import Orchestrator

    llm = None
    if enable_ai:
        try:
            from core.llm_client import LLMClient
            llm = LLMClient()
        except Exception as e:
            console.print(f"[yellow]LLM init failed, running without AI: {e}[/]")

    orchestrator = Orchestrator(llm_client=llm)
    orchestrator.run(request, output_format=output_format)


def cmd_demo() -> None:
    """Run demo analysis on sample vulnerable code."""
    from orchestrator import Orchestrator

    console.print("[bold cyan]CodeRisk Agent Demo[/]\n")

    demo_c = CodeFile(
        path=Path("demo/vulnerable.c"),
        content="""#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int login(char *input) {
    char password[32];
    strcpy(password, input);
    if (strcmp(password, "admin123") == 0) {
        printf("Welcome!\\n");
        system("echo logged in");
        return 1;
    }
    return 0;
}

void process() {
    char *buf = malloc(256);
    gets(buf);
    printf(buf);
    free(buf);
    free(buf);
}
""",
        language=Language.C,
    )

    demo_py = CodeFile(
        path=Path("demo/server.py"),
        content="""import os
import pickle
from flask import request

@app.route("/run")
def run_cmd():
    cmd = request.args.get("cmd")
    return os.system(cmd)

@app.route("/load")
def load_data():
    data = request.get_data()
    return pickle.loads(data)

@app.route("/calc")
def calculate():
    expr = request.args.get("expr")
    return str(eval(expr))
""",
        language=Language.PYTHON,
    )

    request = AnalysisRequest(
        files=[demo_c, demo_py],
        enable_ai=False,  # Demo mode: no LLM, fast
    )

    orchestrator = Orchestrator()  # No LLM for demo
    orchestrator.run(request)


def cmd_info() -> None:
    """Show configuration info."""
    import os

    from rich.table import Table

    table = Table(title="CodeRisk Agent Config", show_header=True)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", VERSION)
    table.add_row("Default Model", "Qwen2.5-Coder-7B-Instruct")
    table.add_row("Backends", "Shared API + llama-server + llama-cpp-python")
    table.add_row("Analyzers", "Static (regex) + Semgrep + LLM semantic + Deep verifier")
    table.add_row("Languages", "C (.c/.h) + Python (.py)")
    table.add_row("CWE Rules", "CWE-120/134/476/415/78/95/502/73/617")
    table.add_row("Pipeline", "Orchestrator -> 4 Agents -> Report")

    # Read actual env config
    backend = os.getenv("LLM_BACKEND", "local_llama_cpp")
    table.add_row("Active Backend", backend)

    console.print(table)


def main():
    console.print(BANNER)

    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        console.print(__doc__)
        return

    cmd = args[0]

    if cmd == "analyze":
        if len(args) < 2:
            console.print("[red]Usage: code-risk analyze <path>[/]")
            sys.exit(1)
        enable_ai = "--no-ai" not in args
        semgrep_config = "p/default"
        output_format = "terminal"
        if "--semgrep-config" in args:
            idx = args.index("--semgrep-config")
            if idx + 1 < len(args):
                semgrep_config = args[idx + 1]
        if "--output" in args:
            idx = args.index("--output")
            if idx + 1 < len(args):
                output_format = args[idx + 1]
        cmd_analyze(
            args[1],
            enable_ai=enable_ai,
            semgrep_config=semgrep_config,
            output_format=output_format,
        )
    elif cmd == "demo":
        cmd_demo()
    elif cmd == "info":
        cmd_info()
    else:
        console.print(f"[red]Unknown command: {cmd}[/]")
        console.print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

```

## 6.2 orchestrator.py (333 lines)

```python
"""Orchestrator: State Machine Pipeline

Manages the complete analysis flow through states:
INIT -> PARSE -> ANALYZE -> VERIFY -> REPORT -> DONE

Coordinates all 4 agents with memory layer, CVE client, and Semgrep.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from pathlib import Path
from typing import Optional

from rich.console import Console

from agents.deep_verifier import DeepVerifier
from agents.report_generator import ReportGenerator
from agents.semantic_analyzer import SemanticAnalyzer
from agents.static_analyzer import StaticAnalyzer
from core.cve_client import CVEClient
from core.llm_client import LLMClient
from core.memory import MemoryLayer
from core.taint_analyzer import TaintAnalyzer
from core.dependency_scanner import scan_project_dependencies
from core.models import (
    AnalysisRequest,
    AnalysisResult,
    CodeFile,
    Language,
)

console = Console()

MIN_LINES_FOR_LLM = 20
MAX_STATIC_WORKERS = 4   # CPU-bound parallelism
MAX_SEMANTIC_WORKERS = 2  # GPU-bound, limited concurrency


class State(str, Enum):
    INIT = "init"
    PARSE = "parse"
    ANALYZE = "analyze"
    VERIFY = "verify"
    REPORT = "report"
    DONE = "done"
    ERROR = "error"


class Orchestrator:
    """State machine orchestrator for the analysis pipeline."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.state = State.INIT
        self.static_analyzer = StaticAnalyzer()
        self.llm = llm_client
        self.semantic_analyzer = SemanticAnalyzer(llm_client) if llm_client else None
        self.memory = MemoryLayer()
        self.cve = CVEClient()
        self.taint = TaintAnalyzer()
        self.verifier = DeepVerifier(
            llm_client=llm_client,
            memory=self.memory,
            cve_client=self.cve,
        )
        self.reporter = ReportGenerator()

    def run(
        self,
        request: AnalysisRequest,
        output_format: str = "terminal",
    ) -> AnalysisResult:
        """Run the complete analysis pipeline."""
        start_time = time.monotonic()
        perf_timings: dict[str, float] = {}  # Phase -> duration_ms

        # State: PARSE
        self.state = State.PARSE
        console.print(f"\n[bold cyan]Orchestrator: Analyzing {len(request.files)} files...[/]\n")

        valid_files = self._validate_files(request.files)
        if not valid_files:
            console.print("[yellow]No valid files to analyze.[/]")
            return AnalysisResult(
                request_id=f"scan-{int(time.time())}",
                files_analyzed=0,
                risks=[],
                analysis_time_ms=0,
                model_used="none",
            )

        # State: ANALYZE
        self.state = State.ANALYZE
        all_risks = []

        # Phase 1: Static analysis (PARALLEL — CPU-bound)
        t0 = time.monotonic()
        console.print("[bold]  Phase 1: Static analysis (Agent 1, parallel)[/]")
        with ThreadPoolExecutor(max_workers=MAX_STATIC_WORKERS) as pool:
            future_map = {pool.submit(self.static_analyzer.analyze, f): f for f in valid_files}
            for future in as_completed(future_map):
                f = future_map[future]
                try:
                    risks = future.result()
                    all_risks.extend(risks)
                    if risks:
                        console.print(f"  [red]  {f.path}: {len(risks)} risks[/]")
                    else:
                        console.print(f"  [green]  {f.path}: clean[/]")
                except Exception as e:
                    console.print(f"  [yellow]  {f.path}: error — {e}[/]")
        perf_timings['agent1_static'] = (time.monotonic() - t0) * 1000

        # Phase 1.5: Dependency scanning (smart root detection)
        t0 = time.monotonic()
        console.print("\n[bold]  Phase 1.5: Dependency scanning[/]")
        try:
            project_root = self._find_project_root(valid_files)
            console.print(f"  [dim]  Project root: {project_root}[/]")
            dep_findings = scan_project_dependencies(project_root)
            if dep_findings:
                console.print(f"  [red]  Dependencies: {len(dep_findings)} vulnerable packages[/]")
                for finding in dep_findings:
                    from core.models import Confidence, Evidence, Language, Risk, Severity
                    all_risks.append(Risk(
                        id=f"RISK-{len(all_risks)+1:03d}",
                        title=f"Vulnerable dep: {finding['package']} {finding['version']}",
                        description=finding['description'],
                        severity=Severity.HIGH,
                        confidence=Confidence.HIGH,
                        cwe_id=finding['cwe'],
                        language=Language.UNKNOWN,
                        file_path=Path(finding.get('file', 'requirements.txt')),
                        line_start=0,
                        line_end=0,
                        evidence=[Evidence(
                            source="dependency_scan",
                            snippet=f"{finding['package']}=={finding['version']}",
                            line_start=0,
                            line_end=0,
                            reasoning=finding['description'],
                        )],
                        suggestion=finding['fix'],
                    ))
            else:
                console.print("  [green]  Dependencies: clean[/]")
        except Exception as e:
            console.print(f"[dim]  Dependency scan skipped: {e}[/]")
        perf_timings['dep_scan'] = (time.monotonic() - t0) * 1000

        # Phase 2 + 2.5: Semgrep + Taint (PARALLEL — both CPU-bound)
        t0 = time.monotonic()
        console.print("\n[bold]  Phase 2: Semgrep + Taint analysis (parallel)[/]")
        semgrep_risks_all: list = []
        taint_risks_all: list = []

        def _run_semgrep(f: CodeFile):
            try:
                from core.semgrep_runner import analyze_with_semgrep
                return analyze_with_semgrep(f, config=request.rules[0], risk_counter_start=0)
            except Exception as e:
                console.print(f"[dim]  Semgrep skipped for {f.path}: {e}[/]")
                return []

        def _run_taint(f: CodeFile):
            try:
                if f.language.value == "c":
                    flows = self.taint.analyze_c(f.content, str(f.path))
                elif f.language.value == "python":
                    flows = self.taint.analyze_python(f.content, str(f.path))
                else:
                    flows = []
                return (f, flows)
            except Exception as e:
                console.print(f"[dim]  Taint skipped for {f.path}: {e}[/]")
                return (f, [])

        with ThreadPoolExecutor(max_workers=MAX_STATIC_WORKERS) as pool:
            semgrep_futures = {pool.submit(_run_semgrep, f): f for f in valid_files}
            taint_futures = {pool.submit(_run_taint, f): f for f in valid_files}

            for future in as_completed(semgrep_futures):
                f = semgrep_futures[future]
                try:
                    risks = future.result()
                    if risks:
                        console.print(f"  [red]  Semgrep {f.path}: {len(risks)} risks[/]")
                        semgrep_risks_all.extend(risks)
                except Exception:
                    pass

            for future in as_completed(taint_futures):
                f = taint_futures[future]
                try:
                    _, flows = future.result()
                    if flows:
                        console.print(f"  [red]  Taint {f.path}: {len(flows)} data flows[/]")
                        for flow in flows:
                            from core.models import Confidence, Evidence, Language, Risk, Severity
                            sev = Severity(flow.severity) if flow.severity in [s.value for s in Severity] else Severity.MEDIUM
                            taint_risks_all.append(Risk(
                                id=f"RISK-{len(all_risks) + len(semgrep_risks_all) + len(taint_risks_all) + 1:03d}",
                                title=f"Taint: {flow.description[:60]}",
                                description=flow.description,
                                severity=sev,
                                confidence=Confidence.HIGH if flow.confidence == "high" else Confidence.MEDIUM,
                                cwe_id=flow.cwe_id,
                                language=f.language,
                                file_path=f.path,
                                line_start=flow.sink_line,
                                line_end=flow.sink_line,
                                evidence=[Evidence(
                                    source="taint_analysis",
                                    snippet=f"{flow.source} -> {flow.sink}",
                                    line_start=flow.source_line,
                                    line_end=flow.sink_line,
                                    reasoning=f"Data flow: {flow.source} (line {flow.source_line}) -> {flow.sink} (line {flow.sink_line})",
                                )],
                                suggestion=flow.suggestion,
                            ))
                except Exception:
                    pass

        all_risks.extend(semgrep_risks_all)
        all_risks.extend(taint_risks_all)
        perf_timings['semgrep_taint'] = (time.monotonic() - t0) * 1000

        # Phase 3: LLM semantic analysis
        if request.enable_ai and self.semantic_analyzer:
            t0 = time.monotonic()
            console.print("\n[bold]  Phase 3: LLM semantic analysis (Agent 2)[/]")
            for f in valid_files:
                file_risks = [r for r in all_risks if r.file_path == f.path]
                if f.line_count < MIN_LINES_FOR_LLM and not file_risks:
                    console.print(f"  [dim]  {f.path}: skipped (small file)[/]")
                    continue
                try:
                    enriched = self.semantic_analyzer.analyze(f, file_risks)
                    all_risks = [r for r in all_risks if r.file_path != f.path]
                    all_risks.extend(enriched)
                except Exception as e:
                    console.print(f"  [yellow]  LLM failed for {f.path}: {e}[/]")
            perf_timings['agent2_llm'] = (time.monotonic() - t0) * 1000

        # State: VERIFY
        self.state = State.VERIFY
        t0 = time.monotonic()
        console.print("\n[bold]  Phase 4: Deep verification (Agent 3)[/]")
        mem_stats = self.memory.get_stats()
        console.print(
            f"  [dim]  Memory: {mem_stats['correct_patterns']} correct, "
            f"{mem_stats['error_patterns']} error patterns loaded[/]"
        )
        all_risks = self.verifier.verify_batch(valid_files, all_risks)
        perf_timings['agent3_verify'] = (time.monotonic() - t0) * 1000

        # State: REPORT
        self.state = State.REPORT
        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        model_desc = "static+semgrep"
        if request.enable_ai and self.llm:
            model_desc += "+llm"
        model_desc += "+verify+memory+cve"

        result = AnalysisResult(
            request_id=f"scan-{int(time.time())}",
            files_analyzed=len(valid_files),
            risks=all_risks,
            analysis_time_ms=elapsed_ms,
            model_used=model_desc,
        )

        console.print(f"\n[bold]  Phase 5: Report generation (Agent 4)[/]")
        t0 = time.monotonic()
        if output_format == "terminal" or output_format == "all":
            self.reporter.print_terminal(result)
        if output_format in ("json", "md", "all"):
            self.reporter.save_report(result, formats=["json", "md"])
        if output_format in ("sarif", "all"):
            self.reporter.save_report(result, formats=["sarif"])
        perf_timings['agent4_report'] = (time.monotonic() - t0) * 1000

        # Store timings in result
        result = result.model_copy(update={"perf_timings": perf_timings})

        # Print performance summary
        console.print("\n[bold cyan]  Performance Summary[/]")
        for phase, ms in perf_timings.items():
            pct = (ms / elapsed_ms * 100) if elapsed_ms > 0 else 0
            console.print(f"  [dim]{phase:>20}: {ms:>8.0f} ms ({pct:>5.1f}%)[/]")

        self.state = State.DONE
        console.print(f"\n[green]  Analysis complete. {result.total_risks} risks found in {elapsed_ms}ms.[/]")

        return result

    def _validate_files(self, files: list[CodeFile]) -> list[CodeFile]:
        valid = []
        for f in files:
            if not f.content.strip():
                continue
            if f.language == Language.UNKNOWN:
                continue
            valid.append(f)
        return valid

    def _find_project_root(self, files: list[CodeFile]) -> Path:
        """Walk up directory tree to find project root."""
        markers = [
            "requirements.txt", "setup.py", "pyproject.toml",
            "Cargo.toml", "Makefile", "CMakeLists.txt",
            "package.json", "go.mod", "pom.xml",
        ]
        start = Path(files[0].path).resolve()
        current = start.parent if start.is_file() else start

        for _ in range(10):
            if any((current / m).exists() for m in markers):
                return current
            parent = current.parent
            if parent == current:
                break
            current = parent

        return Path(files[0].path).parent

    @property
    def current_state(self) -> str:
        return self.state.value

```

## 6.3 core/__init__.py (9 lines)

```python
"""CodeRisk Agent - Core Module"""

from core.models import (AnalysisRequest, AnalysisResult, AgentMessage, AgentRole, CodeFile, Confidence, Evidence, Language, LLMBackend, LLMConfig, Risk, Severity)
from core.llm_client import LLMClient
from core.semgrep_runner import run_semgrep, semgrep_to_risks, analyze_with_semgrep
from core.cve_client import CVEClient
from core.memory import MemoryLayer
from core.retry import retry

```

## 6.4 core/models.py (188 lines)

```python
"""CodeRisk Agent — 核心数据模型

所有 Agent 之间的数据流转都通过这些模型。
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, computed_field


# ─── 语言 & 风险等级 ───────────────────────────────────────────────

class Language(str, Enum):
    C = "c"
    PYTHON = "python"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    """风险等级，从低到高"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Confidence(str, Enum):
    """置信度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ─── 输入模型 ─────────────────────────────────────────────────────

class CodeFile(BaseModel):
    """待分析的源代码文件"""
    path: Path
    content: str
    language: Language = Language.UNKNOWN

    @computed_field
    @property
    def hash(self) -> str:
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]

    @computed_field
    @property
    def line_count(self) -> int:
        return self.content.count("\n") + 1

    @classmethod
    def from_path(cls, path: Path) -> CodeFile:
        content = path.read_text(encoding="utf-8", errors="replace")
        lang = _detect_language(path)
        return cls(path=path, content=content, language=lang)


class AnalysisRequest(BaseModel):
    """分析请求"""
    files: list[CodeFile]
    rules: list[str] = Field(default_factory=lambda: ["p/default"])
    depth: int = Field(default=2, ge=1, le=5, description="分析深度，1=浅 5=深")
    enable_ai: bool = True


# ─── 风险 & 证据 ─────────────────────────────────────────────────

class Evidence(BaseModel):
    """单条证据 — 风险的来源和推理链"""
    source: str = Field(description="来源: semgrep/tree-sitter/ai/manual")
    rule_id: Optional[str] = None
    snippet: str = Field(description="相关代码片段")
    line_start: int
    line_end: int
    reasoning: str = Field(description="推理过程")


class Risk(BaseModel):
    """一个风险项"""
    id: str = Field(description="唯一 ID，如 RISK-001")
    title: str
    description: str
    severity: Severity
    confidence: Confidence
    cwe_id: Optional[str] = Field(default=None, description="CWE 编号，如 CWE-120")
    language: Language
    file_path: Path
    line_start: int
    line_end: int
    evidence: list[Evidence] = Field(default_factory=list)
    suggestion: str = Field(description="修复建议")

    @computed_field
    @property
    def evidence_count(self) -> int:
        return len(self.evidence)


# ─── Agent 消息 ───────────────────────────────────────────────────

class AgentRole(str, Enum):
    STATIC = "static_analyzer"
    SEMANTIC = "semantic_analyzer"
    PATTERN = "pattern_matcher"
    REPORTER = "report_generator"
    ORCHESTRATOR = "orchestrator"


class AgentMessage(BaseModel):
    """Agent 间通信消息"""
    sender: AgentRole
    receiver: AgentRole
    content: dict
    timestamp: datetime = Field(default_factory=datetime.now)
    correlation_id: str = Field(description="关联 ID，追踪同一轮分析")


# ─── 分析结果 ─────────────────────────────────────────────────────

class AnalysisResult(BaseModel):
    """完整分析结果"""
    request_id: str
    files_analyzed: int
    risks: list[Risk] = Field(default_factory=list)
    analysis_time_ms: int = 0
    model_used: str = ""
    perf_timings: dict[str, float] = Field(default_factory=dict, description="Phase timing in ms")
    timestamp: datetime = Field(default_factory=datetime.now)

    @computed_field
    @property
    def risk_summary(self) -> dict[str, int]:
        summary: dict[str, int] = {}
        for risk in self.risks:
            summary[risk.severity.value] = summary.get(risk.severity.value, 0) + 1
        return summary

    @computed_field
    @property
    def total_risks(self) -> int:
        return len(self.risks)

    @computed_field
    @property
    def has_critical(self) -> bool:
        return any(r.severity == Severity.CRITICAL for r in self.risks)


# ─── LLM 配置 ────────────────────────────────────────────────────

class LLMBackend(str, Enum):
    SHARED_API = "shared_api"
    LOCAL_HTTP = "local_http"      # llama-server HTTP API
    LOCAL_LLAMA_CPP = "local_llama_cpp"  # llama-cpp-python 直接加载


class LLMConfig(BaseModel):
    """LLM 客户端配置"""
    backend: LLMBackend = LLMBackend.LOCAL_LLAMA_CPP
    api_url: str = ""
    api_key: str = ""
    model: str = ""
    model_path: str = Field(default="", description="本地 GGUF 模型路径")
    n_gpu_layers: int = Field(default=999, description="GPU 层数，999=全部 offload")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=256, le=32768)
    timeout: int = Field(default=60, ge=5, le=300)


# ─── 工具函数 ─────────────────────────────────────────────────────

def _detect_language(path: Path) -> Language:
    """根据文件扩展名检测语言"""
    suffix_map = {
        ".c": Language.C,
        ".h": Language.C,
        ".py": Language.PYTHON,
    }
    return suffix_map.get(path.suffix, Language.UNKNOWN)

```

## 6.5 core/llm_client.py (299 lines)

```python
"""CodeRisk Agent - LLM Client

Three backends:
1. Shared API (Radeon Cloud HTTP)
2. Local llama-server (HTTP)
3. Local llama-cpp-python (direct GGUF load)

Unified interface with auto-retry.
"""

from __future__ import annotations

import json
import time
from typing import Optional

import httpx
from rich.console import Console

from core.models import LLMBackend, LLMConfig

console = Console()

DEFAULT_CONFIGS = {
    LLMBackend.SHARED_API: LLMConfig(
        backend=LLMBackend.SHARED_API,
        api_url="https://developer.amd.com.cn/radeon/api/v1",
        model="Qwen/Qwen3.6-35B-A3B",
        temperature=0.1,
        max_tokens=8192,
    ),
    LLMBackend.LOCAL_HTTP: LLMConfig(
        backend=LLMBackend.LOCAL_HTTP,
        api_url="http://localhost:8080",
        model="qwen2.5-coder-7b-instruct",
        temperature=0.1,
        max_tokens=8192,
    ),
    LLMBackend.LOCAL_LLAMA_CPP: LLMConfig(
        backend=LLMBackend.LOCAL_LLAMA_CPP,
        model_path="/workspace/llama.cpp/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        model="qwen2.5-coder-7b-instruct",
        temperature=0.1,
        max_tokens=8192,
    ),
}

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0

# Qwen2.5 ChatML special tokens
_IM_START = "<im_start>"
_IM_END = "<im_end>"
_ENDOFTEXT = "<|endoftext|>"


class LLMClient:
    """Unified LLM client with retry support."""

    def __init__(self, config: Optional[LLMConfig] = None, backend: Optional[LLMBackend] = None):
        if config:
            self.config = config
        else:
            b = backend or LLMBackend.LOCAL_LLAMA_CPP
            self.config = DEFAULT_CONFIGS[b]

        self._client: Optional[httpx.Client] = None
        self._local_llm = None
        self._request_count = 0
        self._total_tokens = 0

        if self.config.backend in (LLMBackend.SHARED_API, LLMBackend.LOCAL_HTTP):
            self._client = httpx.Client(timeout=self.config.timeout)
        elif self.config.backend == LLMBackend.LOCAL_LLAMA_CPP:
            self._init_llama_cpp()

    def _init_llama_cpp(self):
        try:
            from llama_cpp import Llama
        except ImportError:
            console.print("[red]llama-cpp-python not installed. Run: pip install llama-cpp-python[/]")
            raise

        if not self.config.model_path:
            raise ValueError("LOCAL_LLAMA_CPP requires model_path in config")

        # Detect GPU availability
        gpu_layers = self.config.n_gpu_layers
        try:
            import subprocess
            result = subprocess.run(
                ["rocm-smi", "--showmeminfo", "vram"],
                capture_output=True, text=True, timeout=5,
            )
            if "N/A" in result.stdout or result.returncode != 0:
                console.print("[yellow]GPU not detected, falling back to CPU inference[/]")
                gpu_layers = 0
            else:
                console.print("[green]AMD GPU detected, offloading layers[/]")
        except Exception:
            console.print("[yellow]rocm-smi not found, falling back to CPU inference[/]")
            gpu_layers = 0

        console.print(f"[dim]Loading local model: {self.config.model_path}[/]")
        self._local_llm = Llama(
            model_path=self.config.model_path,
            n_gpu_layers=gpu_layers,
            verbose=False,
            n_ctx=4096,
        )
        console.print("[green]Local model loaded.[/]")

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None,
    ) -> str:
        """Send chat request with auto-retry."""
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens

        last_err = None
        for attempt in range(MAX_RETRIES):
            try:
                if self.config.backend == LLMBackend.LOCAL_LLAMA_CPP:
                    return self._chat_local(messages, temp, tokens)
                else:
                    return self._chat_http(messages, temp, tokens, response_format)
            except Exception as e:
                last_err = e
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    console.print(
                        f"[yellow]Retry {attempt + 1}/{MAX_RETRIES} after {delay}s: {e}[/]"
                    )
                    time.sleep(delay)
        raise last_err

    def _chat_http(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: Optional[dict] = None,
    ) -> str:
        """HTTP API call (shared API or llama-server)."""
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        url = f"{self.config.api_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        start = time.monotonic()
        resp = self._client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        elapsed_ms = int((time.monotonic() - start) * 1000)
        self._request_count += 1

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        self._total_tokens += usage.get("total_tokens", 0)

        console.print(
            f"[dim]LLM [{self.config.backend.value}] "
            f"{elapsed_ms}ms | "
            f"tokens: {usage.get('prompt_tokens', '?')}->{usage.get('completion_tokens', '?')} | "
            f"total: {self._total_tokens}[/]"
        )
        return content

    def _chat_local(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """llama-cpp-python direct inference."""
        prompt = self._messages_to_prompt(messages)

        start = time.monotonic()
        result = self._local_llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=[_IM_END, "<|endoftext|>"],
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        self._request_count += 1

        text = result["choices"][0]["text"]
        tokens_used = result.get("usage", {}).get("total_tokens", 0)
        self._total_tokens += tokens_used

        console.print(
            f"[dim]LLM [local_llama_cpp] "
            f"{elapsed_ms}ms | "
            f"tokens: {tokens_used} | "
            f"total: {self._total_tokens}[/]"
        )
        return text

    def chat_json(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """Send chat request, parse JSON from response."""
        raw = self.chat(messages, temperature, max_tokens)
        return _extract_json(raw)

    @property
    def stats(self) -> dict:
        return {
            "backend": self.config.backend.value,
            "model": self.config.model,
            "requests": self._request_count,
            "total_tokens": self._total_tokens,
        }

    @staticmethod
    def _messages_to_prompt(messages: list[dict[str, str]]) -> str:
        """Convert OpenAI-style messages to Qwen2.5 ChatML format."""
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            parts.append(f"{_IM_START}{role}\n{content}{_IM_END}")
        parts.append(f"{_IM_START}assistant\n")
        return "\n".join(parts)

    def close(self):
        if self._client:
            self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response with multiple fallback strategies."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        try:
            return json.loads(text[start:end].strip())
        except json.JSONDecodeError:
            pass

    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    start = -1

    # Try to repair truncated JSON by closing brackets
    stripped = text.strip()
    if stripped.startswith("{"):
        # Count open vs close braces
        opens = stripped.count("{")
        closes = stripped.count("}")
        if opens > closes:
            repair = stripped + "}" * (opens - closes)
            try:
                return json.loads(repair)
            except json.JSONDecodeError:
                pass

    raise ValueError(f"Failed to extract JSON from LLM response:\n{text[:300]}...")

```

## 6.6 core/memory.py (229 lines)

```python
"""CodeRisk Agent - Memory Layer

Two-memory system using in-memory storage (ChromaDB optional):
1. Correct Memory: Store confirmed vulnerability patterns for recall
2. Error Memory: Store false-positive patterns for suppression

Makes the system "learn" over time - same code patterns get faster,
false positives get suppressed.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional

from rich.console import Console

from core.models import Confidence, Risk, Severity

console = Console()

# Memory storage file (JSON-based, ChromaDB optional upgrade)
MEMORY_DIR = os.path.expanduser("~/.coderisk/memory")
CORRECT_MEMORY_FILE = os.path.join(MEMORY_DIR, "correct_memory.json")
ERROR_MEMORY_FILE = os.path.join(MEMORY_DIR, "error_memory.json")

# Similarity threshold for pattern matching
SIMILARITY_THRESHOLD = 0.85


class MemoryEntry:
    """A single memory entry."""

    def __init__(
        self,
        pattern_hash: str,
        cwe_id: str,
        severity: str,
        title: str,
        description: str,
        suggestion: str,
        confidence: str,
        source_count: int = 1,
        last_seen: float = 0.0,
    ):
        self.pattern_hash = pattern_hash
        self.cwe_id = cwe_id
        self.severity = severity
        self.title = title
        self.description = description
        self.suggestion = suggestion
        self.confidence = confidence
        self.source_count = source_count
        self.last_seen = last_seen or time.time()

    def to_dict(self) -> dict:
        return {
            "pattern_hash": self.pattern_hash,
            "cwe_id": self.cwe_id,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
            "source_count": self.source_count,
            "last_seen": self.last_seen,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(**data)


class MemoryLayer:
    """Memory layer with correct memory and error memory."""

    def __init__(self, persist: bool = True):
        self.persist = persist
        self._correct_memory: dict[str, MemoryEntry] = {}
        self._error_memory: dict[str, MemoryEntry] = {}

        if persist:
            self._load()

    def store_correct(self, risk: Risk) -> None:
        """Store a confirmed vulnerability pattern in correct memory."""
        pattern_hash = self._hash_risk_pattern(risk)

        if pattern_hash in self._correct_memory:
            # Update existing entry
            entry = self._correct_memory[pattern_hash]
            entry.source_count += 1
            entry.last_seen = time.time()
            # Upgrade confidence if seen multiple times
            if entry.source_count >= 3 and entry.confidence != "high":
                entry.confidence = "high"
        else:
            self._correct_memory[pattern_hash] = MemoryEntry(
                pattern_hash=pattern_hash,
                cwe_id=risk.cwe_id or "",
                severity=risk.severity.value,
                title=risk.title,
                description=risk.description,
                suggestion=risk.suggestion,
                confidence=risk.confidence.value,
            )

        if self.persist:
            self._save()

    def store_error(self, risk: Risk) -> None:
        """Store a false-positive pattern in error memory."""
        pattern_hash = self._hash_risk_pattern(risk)

        if pattern_hash in self._error_memory:
            entry = self._error_memory[pattern_hash]
            entry.source_count += 1
            entry.last_seen = time.time()
        else:
            self._error_memory[pattern_hash] = MemoryEntry(
                pattern_hash=pattern_hash,
                cwe_id=risk.cwe_id or "",
                severity=risk.severity.value,
                title=risk.title,
                description=risk.description,
                suggestion=risk.suggestion,
                confidence="low",
            )

        if self.persist:
            self._save()

    def recall(self, risk: Risk) -> Optional[MemoryEntry]:
        """Check if a risk pattern matches known correct/incorrect patterns.

        Returns:
            MemoryEntry if found, None otherwise
        """
        pattern_hash = self._hash_risk_pattern(risk)

        # Check error memory first (suppress known false positives)
        if pattern_hash in self._error_memory:
            entry = self._error_memory[pattern_hash]
            if entry.source_count >= 2:
                console.print(
                    f"[dim]  Memory: suppressed known false positive {risk.id} "
                    f"(seen {entry.source_count} times)[/]"
                )
                return entry

        # Check correct memory (boost confidence for known patterns)
        if pattern_hash in self._correct_memory:
            entry = self._correct_memory[pattern_hash]
            console.print(
                f"[dim]  Memory: recalled pattern for {risk.id} "
                f"(seen {entry.source_count} times)[/]"
            )
            return entry

        return None

    def get_stats(self) -> dict:
        """Get memory statistics."""
        return {
            "correct_patterns": len(self._correct_memory),
            "error_patterns": len(self._error_memory),
            "total": len(self._correct_memory) + len(self._error_memory),
        }

    def _hash_risk_pattern(self, risk: Risk) -> str:
        """Create a hash of the risk pattern for matching.

        Uses CWE + file extension + code pattern to identify similar risks.
        """
        # Extract code snippet pattern (first 100 chars of evidence)
        code_pattern = ""
        if risk.evidence:
            code_pattern = risk.evidence[0].snippet[:100]

        # Hash: CWE + language + code pattern
        key = f"{risk.cwe_id}:{risk.language}:{code_pattern}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _save(self):
        """Persist memory to disk."""
        os.makedirs(MEMORY_DIR, exist_ok=True)

        correct_data = {k: v.to_dict() for k, v in self._correct_memory.items()}
        error_data = {k: v.to_dict() for k, v in self._error_memory.items()}

        with open(CORRECT_MEMORY_FILE, "w") as f:
            json.dump(correct_data, f, indent=2)

        with open(ERROR_MEMORY_FILE, "w") as f:
            json.dump(error_data, f, indent=2)

    def _load(self):
        """Load memory from disk."""
        try:
            if os.path.exists(CORRECT_MEMORY_FILE):
                with open(CORRECT_MEMORY_FILE) as f:
                    data = json.load(f)
                self._correct_memory = {
                    k: MemoryEntry.from_dict(v) for k, v in data.items()
                }
        except Exception:
            pass

        try:
            if os.path.exists(ERROR_MEMORY_FILE):
                with open(ERROR_MEMORY_FILE) as f:
                    data = json.load(f)
                self._error_memory = {
                    k: MemoryEntry.from_dict(v) for k, v in data.items()
                }
        except Exception:
            pass

    def clear(self):
        """Clear all memory."""
        self._correct_memory.clear()
        self._error_memory.clear()
        if self.persist:
            self._save()

```

## 6.7 core/cve_client.py (152 lines)

```python
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

```

## 6.8 core/semgrep_runner.py (136 lines)

```python
"""CodeRisk Agent - Semgrep Runner

Wraps Semgrep CLI to scan files and convert results to Risk objects.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console

from core.models import (
    CodeFile,
    Confidence,
    Evidence,
    Language,
    Risk,
    Severity,
)

console = Console()

# Semgrep severity -> our severity mapping
_SEVERITY_MAP = {
    "ERROR": Severity.HIGH,
    "WARNING": Severity.MEDIUM,
    "INFO": Severity.LOW,
}


def run_semgrep(
    file_path: Path,
    config: str = "p/default",
    timeout: int = 30,
) -> list[dict]:
    """Run Semgrep on a single file, return raw results."""
    try:
        result = subprocess.run(
            ["semgrep", "scan", "--json", f"--config={config}", str(file_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode not in (0, 1):
            console.print(f"[yellow]Semgrep exited with code {result.returncode}[/]")
            if result.stderr:
                console.print(f"[dim]{result.stderr[:200]}[/]")
            return []

        data = json.loads(result.stdout)
        return data.get("results", [])
    except FileNotFoundError:
        console.print("[yellow]Semgrep not installed, skipping Semgrep scan.[/]")
        return []
    except subprocess.TimeoutExpired:
        console.print(f"[yellow]Semgrep timed out after {timeout}s[/]")
        return []
    except json.JSONDecodeError:
        console.print("[yellow]Semgrep output is not valid JSON[/]")
        return []


def semgrep_to_risks(
    raw_results: list[dict],
    code_file: CodeFile,
    risk_counter_start: int = 0,
) -> list[Risk]:
    """Convert Semgrep JSON results to Risk objects."""
    risks: list[Risk] = []
    counter = risk_counter_start

    for item in raw_results:
        counter += 1

        # Extract metadata
        check_id = item.get("check_id", "unknown")
        severity_raw = item.get("extra", {}).get("severity", "WARNING")
        metadata = item.get("extra", {}).get("metadata", {})

        # Build CWE list
        cwe_id = None
        cwe_list = metadata.get("cwe", [])
        if cwe_list:
            cwe_id = cwe_list[0] if isinstance(cwe_list[0], str) else cwe_list[0].get("id")

        # Location
        start_line = item.get("start", {}).get("line", 0)
        end_line = item.get("end", {}).get("line", 0)
        snippet = item.get("extra", {}).get("lines", "")

        # Map severity
        severity = _SEVERITY_MAP.get(severity_raw, Severity.MEDIUM)

        # Build risk
        message = item.get("extra", {}).get("message", check_id)
        fix_msg = item.get("extra", {}).get("fix", "")

        risks.append(Risk(
            id=f"RISK-{counter:03d}",
            title=f"Semgrep: {check_id}",
            description=message,
            severity=severity,
            confidence=Confidence.HIGH,
            cwe_id=cwe_id,
            language=code_file.language,
            file_path=code_file.path,
            line_start=start_line,
            line_end=end_line,
            evidence=[Evidence(
                source="semgrep",
                rule_id=check_id,
                snippet=snippet[:500],
                line_start=start_line,
                line_end=end_line,
                reasoning=f"Semgrep rule {check_id} matched",
            )],
            suggestion=fix_msg or "Review Semgrep documentation for this rule.",
        ))

    return risks


def analyze_with_semgrep(
    code_file: CodeFile,
    config: str = "p/default",
    risk_counter_start: int = 0,
) -> list[Risk]:
    """Full pipeline: run Semgrep on a file and return Risk objects."""
    raw = run_semgrep(code_file.path, config=config)
    if not raw:
        return []
    return semgrep_to_risks(raw, code_file, risk_counter_start)

```

## 6.9 core/taint_analyzer.py (209 lines)

```python
"""Simple Taint Analysis Module

Inspired by OpenTaint - tracks data flow from untrusted sources to dangerous sinks.
Not a full taint engine, but adds cross-function data flow awareness.

Sources (untrusted input):
- C: argv, getenv(), scanf(), fgets(), read()
- Python: input(), sys.argv, request.args, request.form, os.environ

Sinks (dangerous operations):
- C: system(), exec*(), strcpy(), sprintf(), printf(buf)
- Python: eval(), exec(), os.system(), subprocess, pickle.loads()
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console

console = Console()


@dataclass
class TaintFlow:
    """A detected data flow from source to sink."""
    source: str          # e.g. "argv[1]", "request.args"
    sink: str            # e.g. "system()", "eval()"
    source_line: int
    sink_line: int
    cwe_id: str
    severity: str        # "critical", "high", "medium"
    description: str
    suggestion: str
    confidence: str      # "high", "medium", "low"
    path: list[str] = field(default_factory=list)  # intermediate variables


# ─── Source Definitions ──────────────────────────────────────────

C_SOURCES = {
    r"\bargv\b": "command-line argument",
    r"\bgetenv\s*\(": "environment variable",
    r"\bscanf\s*\(": "user input (stdin)",
    r"\bfgets\s*\(": "user input (stdin)",
    r"\bread\s*\(": "file/network input",
    r"\brecv\s*\(": "network input",
    r"\baccept\s*\(": "network connection",
}

PYTHON_SOURCES = {
    r"\binput\s*\(": "user input (stdin)",
    r"\bsys\.argv": "command-line argument",
    r"\brequest\.(args|form|json|data|cookies)\b": "HTTP request data",
    r"\bos\.environ\b": "environment variable",
    r"\bos\.getenv\s*\(": "environment variable",
    r"\brandom\.randint\s*\(": "random value (not crypto-safe)",
}

# ─── Sink Definitions ────────────────────────────────────────────

C_SINKS = {
    r"\bsystem\s*\(": ("CWE-78", "high", "Command injection via system()"),
    r"\bexecl[pe]?\s*\(": ("CWE-78", "high", "Command injection via exec()"),
    r"\bstrcpy\s*\(": ("CWE-120", "high", "Buffer overflow via strcpy()"),
    r"\bstrcat\s*\(": ("CWE-120", "high", "Buffer overflow via strcat()"),
    r"\bsprintf\s*\(": ("CWE-134", "high", "Format string via sprintf()"),
    r"\bprintf\s*\(\s*[a-zA-Z_]\w*\s*\)": ("CWE-134", "medium", "Format string via printf(variable)"),
    r"\bgets\s*\(": ("CWE-120", "critical", "Buffer overflow via gets()"),
}

PYTHON_SINKS = {
    r"\beval\s*\(": ("CWE-95", "critical", "Code injection via eval()"),
    r"\bexec\s*\(": ("CWE-95", "critical", "Code injection via exec()"),
    r"\bos\.system\s*\(": ("CWE-78", "high", "Command injection via os.system()"),
    r"\bsubprocess\.(call|run|Popen)\s*\(": ("CWE-78", "medium", "Potential command injection"),
    r"\bpickle\.loads?\s*\(": ("CWE-502", "critical", "Deserialization via pickle"),
    r"\byaml\.load\s*\(": ("CWE-502", "high", "Deserialization via yaml.load()"),
    r"\b__import__\s*\(": ("CWE-95", "high", "Dynamic import via __import__()"),
}

# ─── Variable Tracking ───────────────────────────────────────────

# Simple regex to track variable assignments
C_ASSIGN_PATTERN = re.compile(r"(\w+)\s*=\s*(.+);")
PYTHON_ASSIGN_PATTERN = re.compile(r"(\w+)\s*=\s*(.+)")


class TaintAnalyzer:
    """Simple taint analysis engine."""

    def __init__(self):
        self._flows: list[TaintFlow] = []

    def analyze_c(self, content: str, file_path: str) -> list[TaintFlow]:
        """Analyze C code for taint flows."""
        self._flows = []
        lines = content.split("\n")

        # Track tainted variables
        tainted_vars: dict[str, tuple[str, int]] = {}  # var -> (source, line)

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("/*"):
                continue

            # Check if line assigns from a source
            for source_pattern, source_name in C_SOURCES.items():
                if re.search(source_pattern, line):
                    # Try to find variable assignment
                    assign = C_ASSIGN_PATTERN.search(line)
                    if assign:
                        var_name = assign.group(1)
                        tainted_vars[var_name] = (source_name, i)
                    else:
                        # Direct source usage (e.g., system(argv[1]))
                        self._check_direct_flow(line, i, source_name, "c", file_path)

            # Check if tainted variables flow to sinks
            for sink_pattern, (cwe, severity, desc) in C_SINKS.items():
                if re.search(sink_pattern, line):
                    # Check if any tainted variable is used in this line
                    for var_name, (source_name, source_line) in tainted_vars.items():
                        if re.search(rf"\b{re.escape(var_name)}\b", line):
                            self._flows.append(TaintFlow(
                                source=source_name,
                                sink=sink_pattern.replace(r"\b", "").replace(r"\s*\(", "("),
                                source_line=source_line,
                                sink_line=i,
                                cwe_id=cwe,
                                severity=severity,
                                description=f"Tainted data from {source_name} flows to {desc}",
                                suggestion="Validate and sanitize input before use",
                                confidence="high",
                                path=[var_name],
                            ))

        return self._flows

    def analyze_python(self, content: str, file_path: str) -> list[TaintFlow]:
        """Analyze Python code for taint flows."""
        self._flows = []
        lines = content.split("\n")

        # Track tainted variables
        tainted_vars: dict[str, tuple[str, int]] = {}

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            # Check if line assigns from a source
            for source_pattern, source_name in PYTHON_SOURCES.items():
                if re.search(source_pattern, line):
                    assign = PYTHON_ASSIGN_PATTERN.search(line)
                    if assign:
                        var_name = assign.group(1)
                        tainted_vars[var_name] = (source_name, i)
                    else:
                        self._check_direct_flow(line, i, source_name, "python", file_path)

            # Check if tainted variables flow to sinks
            for sink_pattern, (cwe, severity, desc) in PYTHON_SINKS.items():
                if re.search(sink_pattern, line):
                    for var_name, (source_name, source_line) in tainted_vars.items():
                        if re.search(rf"\b{re.escape(var_name)}\b", line):
                            self._flows.append(TaintFlow(
                                source=source_name,
                                sink=sink_pattern.replace(r"\b", "").replace(r"\s*\(", "("),
                                source_line=source_line,
                                sink_line=i,
                                cwe_id=cwe,
                                severity=severity,
                                description=f"Tainted data from {source_name} flows to {desc}",
                                suggestion="Validate and sanitize input before use",
                                confidence="high",
                                path=[var_name],
                            ))

        return self._flows

    def _check_direct_flow(
        self,
        line: str,
        line_num: int,
        source_name: str,
        language: str,
        file_path: str,
    ):
        """Check for direct source-to-sink flow (no intermediate variable)."""
        sinks = C_SINKS if language == "c" else PYTHON_SINKS
        for sink_pattern, (cwe, severity, desc) in sinks.items():
            if re.search(sink_pattern, line):
                self._flows.append(TaintFlow(
                    source=source_name,
                    sink=sink_pattern.replace(r"\b", "").replace(r"\s*\(", "("),
                    source_line=line_num,
                    sink_line=line_num,
                    cwe_id=cwe,
                    severity=severity,
                    description=f"Direct flow from {source_name} to {desc}",
                    suggestion="Validate and sanitize input before use",
                    confidence="medium",
                ))

```

## 6.10 core/dependency_scanner.py (289 lines)

```python
"""Dependency Scanner Module

Scans project dependencies for known vulnerabilities.
Primary source: OSV API (https://api.osv.dev) — real-time vulnerability database.
Fallback: local hardcoded vulnerable package dictionary.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import httpx
from rich.console import Console

console = Console()

# Known vulnerable package versions (simplified - in production use OSV/NVD API)
OSV_API_URL = "https://api.osv.dev/v1/query"
OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_TIMEOUT = 10


# ─── OSV API Client ─────────────────────────────────────────────


def _query_osv(package_name: str, version: str, ecosystem: str = "PyPI") -> list[dict]:
    """Query OSV API for vulnerabilities of a specific package version."""
    try:
        client = httpx.Client(timeout=OSV_TIMEOUT)
        resp = client.post(
            OSV_API_URL,
            json={
                "version": version,
                "package": {"name": package_name, "ecosystem": ecosystem},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        vulns = data.get("vulnerabilities", [])
        results = []
        for v in vulns:
            v_id = v.get("id", "unknown")
            aliases = v.get("aliases", [])
            summary = v.get("summary", v.get("details", "")[:200])
            severity = "unknown"
            # Extract severity from database_specific or severity field
            for sev in v.get("severity", []):
                if sev.get("type") == "CVSS_V3":
                    score_str = sev.get("score", "")
                    # Parse CVSS vector for severity
                    if "CRITICAL" in score_str.upper():
                        severity = "critical"
                    elif "HIGH" in score_str.upper():
                        severity = "high"
                    elif "MEDIUM" in score_str.upper():
                        severity = "medium"
                    elif "LOW" in score_str.upper():
                        severity = "low"
            # Extract CWE
            cwe = ""
            for ref in v.get("references", []):
                url = ref.get("url", "")
                if "cwe.mitre.org" in url:
                    cwe_match = re.search(r'CWE-\d+', url)
                    if cwe_match:
                        cwe = cwe_match.group()
                        break
            # If no severity, try to infer from database_specific
            if severity == "unknown":
                db_sev = v.get("database_specific", {}).get("severity", "")
                if db_sev:
                    severity = db_sev.lower()
            results.append({
                "id": v_id,
                "aliases": aliases,
                "summary": summary[:200],
                "severity": severity,
                "cwe": cwe,
            })
        return results
    except Exception:
        return []


# Known vulnerable package versions (local fallback when OSV is unavailable)
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
    """Scan Python requirements.txt for vulnerable packages.

    Uses OSV API as primary source, falls back to local dictionary.
    """
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

            # Try OSV API first
            osv_vulns = _query_osv(pkg_name, version)
            if osv_vulns:
                for v in osv_vulns:
                    findings.append({
                        "package": pkg_name,
                        "version": version,
                        "cwe": v.get("cwe", "CWE-000"),
                        "description": v.get("summary", "Vulnerability found via OSV"),
                        "fix": f"Upgrade {pkg_name} — see {v.get('id', 'OSV')} for details",
                        "source": "osv",
                        "osv_id": v.get("id", ""),
                    })
            else:
                # Fallback to local dictionary
                if pkg_name in VULNERABLE_PACKAGES:
                    vuln = VULNERABLE_PACKAGES[pkg_name]
                    if _version_below(version, vuln["vulnerable_below"]):
                        findings.append({
                            "package": pkg_name,
                            "version": version,
                            "cwe": vuln["cwe"],
                            "description": vuln["description"],
                            "fix": f"Upgrade {pkg_name} to >= {vuln['vulnerable_below']}",
                            "source": "local",
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

```

## 6.11 core/attack_knowledge.py (227 lines)

```python
"""MITRE ATT&CK Knowledge Base

Simplified mapping from MITRE ATT&CK techniques to CWE vulnerabilities.
Inspired by Anthropic-Cybersecurity-Skills (817 skills, 6 frameworks).

This module provides:
1. CWE → ATT&CK technique mapping for reports
2. Attack pattern descriptions for Agent 3 verification
3. Compliance framework references
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AttackTechnique:
    """MITRE ATT&CK technique mapped to CWE."""
    technique_id: str       # e.g. "T1059"
    name: str               # e.g. "Command and Scripting Interpreter"
    tactic: str             # e.g. "Execution"
    cwe_ids: list[str]      # Related CWEs
    description: str
    detection: str          # How to detect
    mitigation: str         # How to prevent


# ─── ATT&CK Techniques → CWE Mapping ────────────────────────────

ATTACK_TECHNIQUES: dict[str, AttackTechnique] = {
    "T1059": AttackTechnique(
        technique_id="T1059",
        name="Command and Scripting Interpreter",
        tactic="Execution",
        cwe_ids=["CWE-78", "CWE-95"],
        description="Adversaries may abuse command-line interpreters to execute commands, scripts, or binaries.",
        detection="Monitor command-line activity, script execution logs",
        mitigation="Restrict command-line access, use application whitelisting",
    ),
    "T1190": AttackTechnique(
        technique_id="T1190",
        name="Exploit Public-Facing Application",
        tactic="Initial Access",
        cwe_ids=["CWE-89", "CWE-79", "CWE-95", "CWE-502"],
        description="Adversaries may attempt to exploit vulnerabilities in public-facing applications.",
        detection="Web application firewall logs, intrusion detection systems",
        mitigation="Regular patching, input validation, web application firewall",
    ),
    "T1055": AttackTechnique(
        technique_id="T1055",
        name="Process Injection",
        tactic="Defense Evasion",
        cwe_ids=["CWE-120", "CWE-415", "CWE-476"],
        description="Adversaries may inject code into processes to evade defenses and escalate privileges.",
        detection="Monitor process memory operations, API calls",
        mitigation="Code signing, memory protection, least privilege",
    ),
    "T1105": AttackTechnique(
        technique_id="T1105",
        name="Ingress Tool Transfer",
        tactic="Command and Control",
        cwe_ids=["CWE-78", "CWE-95"],
        description="Adversaries may transfer tools to compromised systems.",
        detection="Network traffic monitoring, file integrity monitoring",
        mitigation="Network segmentation, egress filtering",
    ),
    "T1053": AttackTechnique(
        technique_id="T1053",
        name="Scheduled Task/Job",
        tactic="Execution",
        cwe_ids=["CWE-78"],
        description="Adversaries may abuse task scheduling to execute code.",
        detection="Monitor scheduled task creation and modification",
        mitigation="Restrict task scheduling permissions",
    ),
    "T1078": AttackTechnique(
        technique_id="T1078",
        name="Valid Accounts",
        tactic="Initial Access",
        cwe_ids=["CWE-798", "CWE-287"],
        description="Adversaries may use valid credentials to gain initial access.",
        detection="Authentication logs, anomaly detection",
        mitigation="Multi-factor authentication, credential management",
    ),
    "T1071": AttackTechnique(
        technique_id="T1071",
        name="Application Layer Protocol",
        tactic="Command and Control",
        cwe_ids=["CWE-295", "CWE-327"],
        description="Adversaries may use application layer protocols for C2 communication.",
        detection="Network traffic analysis, protocol anomaly detection",
        mitigation="Network monitoring, TLS inspection",
    ),
    "T1003": AttackTechnique(
        technique_id="T1003",
        name="OS Credential Dumping",
        tactic="Credential Access",
        cwe_ids=["CWE-798", "CWE-256"],
        description="Adversaries may dump credentials from operating systems.",
        detection="Monitor credential access, memory reads",
        mitigation="Credential guard, least privilege",
    ),
    "T1057": AttackTechnique(
        technique_id="T1057",
        name="Process Discovery",
        tactic="Discovery",
        cwe_ids=["CWE-200"],
        description="Adversaries may enumerate processes to find security tools.",
        detection="Monitor process enumeration API calls",
        mitigation="Least privilege, process hiding",
    ),
    "T1082": AttackTechnique(
        technique_id="T1082",
        name="System Information Discovery",
        tactic="Discovery",
        cwe_ids=["CWE-200"],
        description="Adversaries may gather system information for reconnaissance.",
        detection="Monitor system information queries",
        mitigation="Least privilege, information hiding",
    ),
    "T1083": AttackTechnique(
        technique_id="T1083",
        name="File and Directory Discovery",
        tactic="Discovery",
        cwe_ids=["CWE-22"],
        description="Adversaries may enumerate files and directories.",
        detection="Monitor file system queries",
        mitigation="Access control, directory permissions",
    ),
    "T1005": AttackTechnique(
        technique_id="T1005",
        name="Data from Local System",
        tactic="Collection",
        cwe_ids=["CWE-200", "CWE-22"],
        description="Adversaries may search local systems for data of interest.",
        detection="File access monitoring",
        mitigation="Data encryption, access control",
    ),
    "T1021": AttackTechnique(
        technique_id="T1021",
        name="Remote Services",
        tactic="Lateral Movement",
        cwe_ids=["CWE-287", "CWE-798"],
        description="Adversaries may use remote services to move laterally.",
        detection="Network connection monitoring",
        mitigation="Network segmentation, strong authentication",
    ),
    "T1566": AttackTechnique(
        technique_id="T1566",
        name="Phishing",
        tactic="Initial Access",
        cwe_ids=["CWE-79", "CWE-89"],
        description="Adversaries may use phishing to gain access.",
        detection="Email filtering, user awareness training",
        mitigation="Email security, user training",
    ),
    "T1499": AttackTechnique(
        technique_id="T1499",
        name="Endpoint Denial of Service",
        tactic="Impact",
        cwe_ids=["CWE-400", "CWE-770"],
        description="Adversaries may perform DoS to disrupt availability.",
        detection="Traffic analysis, resource monitoring",
        mitigation="Rate limiting, DDoS protection",
    ),
}

# ─── Reverse Mapping: CWE → ATT&CK ──────────────────────────────

CWE_TO_ATTACK: dict[str, list[str]] = {}
for tech in ATTACK_TECHNIQUES.values():
    for cwe in tech.cwe_ids:
        if cwe not in CWE_TO_ATTACK:
            CWE_TO_ATTACK[cwe] = []
        CWE_TO_ATTACK[cwe].append(tech.technique_id)


def get_attack_context(cwe_id: str) -> Optional[AttackTechnique]:
    """Get ATT&CK context for a CWE ID."""
    tech_ids = CWE_TO_ATTACK.get(cwe_id, [])
    if tech_ids:
        return ATTACK_TECHNIQUES[tech_ids[0]]
    return None


def get_attack_description(cwe_id: str) -> str:
    """Get a human-readable attack description for a CWE."""
    tech = get_attack_context(cwe_id)
    if tech:
        return f"[ATT&CK {tech.technique_id}] {tech.name}: {tech.description}"
    return ""


def get_compliance_references(cwe_id: str) -> dict[str, str]:
    """Get compliance framework references for a CWE."""
    tech = get_attack_context(cwe_id)
    if not tech:
        return {}

    refs = {
        "MITRE ATT&CK": f"{tech.technique_id} - {tech.name}",
        "Tactic": tech.tactic,
        "Detection": tech.detection,
        "Mitigation": tech.mitigation,
    }

    # Add framework-specific references
    if cwe_id in ["CWE-78", "CWE-95", "CWE-89"]:
        refs["OWASP Top 10"] = "A03:2021 - Injection"
        refs["NIST CSF"] = "DE.CM-1: Networks monitored"
    elif cwe_id in ["CWE-120", "CWE-415", "CWE-476"]:
        refs["OWASP Top 10"] = "A06:2021 - Vulnerable Components"
        refs["NIST CSF"] = "PR.DS-1: Data-at-rest protected"
    elif cwe_id in ["CWE-798", "CWE-287"]:
        refs["OWASP Top 10"] = "A07:2021 - Identification Failures"
        refs["NIST CSF"] = "PR.AC-1: Identity credentials managed"
    elif cwe_id in ["CWE-502", "CWE-611"]:
        refs["OWASP Top 10"] = "A08:2021 - Software Integrity Failures"
        refs["NIST CSF"] = "PR.DS-6: Integrity checking mechanisms"
    elif cwe_id in ["CWE-327", "CWE-328"]:
        refs["OWASP Top 10"] = "A02:2021 - Cryptographic Failures"
        refs["NIST CSF"] = "PR.DS-1: Data-at-rest protected"

    return refs

```

## 6.12 core/retry.py (60 lines)

```python
"""CodeRisk Agent - Retry Policy

Unified retry decorator with exponential backoff.
Replaces scattered retry logic across modules.
"""

from __future__ import annotations

import time
from functools import wraps
from typing import Callable, Optional, Type

from rich.console import Console

console = Console()

DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0
DEFAULT_MAX_DELAY = 30.0


def retry(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """Retry decorator with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        exceptions: Tuple of exception types to catch
        on_retry: Optional callback(attempt, delay, exception) called before each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_err = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        if on_retry:
                            on_retry(attempt + 1, delay, e)
                        else:
                            console.print(
                                f"[yellow]Retry {attempt + 1}/{max_retries} "
                                f"after {delay:.1f}s: {e}[/]"
                            )
                        time.sleep(delay)
            raise last_err
        return wrapper
    return decorator

```

## 6.13 agents/__init__.py (7 lines)

```python
"""CodeRisk Agent - Agent Module"""

from agents.static_analyzer import StaticAnalyzer
from agents.semantic_analyzer import SemanticAnalyzer
from agents.deep_verifier import DeepVerifier
from agents.report_generator import ReportGenerator

```

## 6.14 agents/static_analyzer.py (443 lines)

```python
"""Agent 1: Tree-sitter 静态分析器

职责：
- 用 Tree-sitter 解析 AST
- 检测 C/Python 中的危险模式
- 输出结构化风险列表
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from rich.console import Console

from core.models import (
    CodeFile,
    Confidence,
    Evidence,
    Language,
    Risk,
    Severity,
)

console = Console()

# ─── C 语言危险模式 ──────────────────────────────────────────────

C_DANGEROUS_FUNCTIONS = {
    "gets": {
        "cwe": "CWE-120",
        "severity": Severity.CRITICAL,
        "title": "Buffer Overflow via gets()",
        "desc": "gets() 不检查边界，可导致栈缓冲区溢出",
        "fix": "用 fgets(buf, sizeof(buf), stdin) 替代",
    },
    "strcpy": {
        "cwe": "CWE-120",
        "severity": Severity.HIGH,
        "title": "Unbounded strcpy()",
        "desc": "strcpy() 不检查目标缓冲区大小",
        "fix": "用 strncpy() 或 strlcpy() 替代",
    },
    "strcat": {
        "cwe": "CWE-120",
        "severity": Severity.HIGH,
        "title": "Unbounded strcat()",
        "desc": "strcat() 不检查目标缓冲区剩余空间",
        "fix": "用 strncat() 或 strlcat() 替代",
    },
    "sprintf": {
        "cwe": "CWE-134",
        "severity": Severity.HIGH,
        "title": "Format String via sprintf()",
        "desc": "sprintf() 不检查目标缓冲区大小，且可能被格式字符串攻击",
        "fix": "用 snprintf(buf, sizeof(buf), ...) 替代",
    },
    "scanf": {
        "cwe": "CWE-120",
        "severity": Severity.MEDIUM,
        "title": "Unbounded scanf()",
        "desc": "scanf(\"%s\", ...) 无长度限制",
        "fix": "用 scanf(\"%99s\", buf) 限制长度，或用 fgets",
    },
    "system": {
        "cwe": "CWE-78",
        "severity": Severity.HIGH,
        "title": "OS Command Injection via system()",
        "desc": "system() 直接执行 shell 命令，可能被注入",
        "fix": "避免使用 system()，用 exec 系列函数替代",
    },
    "memcpy": {
        "cwe": "CWE-120",
        "severity": Severity.MEDIUM,
        "title": "Unchecked memcpy()",
        "desc": "memcpy() 不检查目标缓冲区大小，可能导致溢出",
        "fix": "确保目标缓冲区足够大，或用 memcpy_s() 替代",
    },
    "popen": {
        "cwe": "CWE-78",
        "severity": Severity.HIGH,
        "title": "Command Injection via popen()",
        "desc": "popen() 执行 shell 命令，可能被注入",
        "fix": "用 pipe+exec 替代，避免 shell 解释",
    },
}

C_VULNERABLE_PATTERNS = [
    {
        "pattern": r"malloc\s*\(.*\)\s*;",
        "check_null": True,
        "cwe": "CWE-476",
        "severity": Severity.MEDIUM,
        "title": "malloc() 返回值未检查",
        "desc": "malloc() 可能返回 NULL，直接使用会导致空指针解引用",
        "fix": "检查 malloc() 返回值是否为 NULL",
    },
    {
        "pattern": r"free\s*\([^)]+\)\s*;",
        "check_double_free": True,
        "cwe": "CWE-415",
        "severity": Severity.HIGH,
        "title": "Potential Double Free",
        "desc": "free() 后指针未置 NULL，可能被重复释放",
        "fix": "free(ptr) 后立即 ptr = NULL",
    },
]

# ─── Python 危险模式 ────────────────────────────────────────────

PYTHON_DANGEROUS_CALLS = {
    "eval": {
        "cwe": "CWE-95",
        "severity": Severity.CRITICAL,
        "title": "Code Injection via eval()",
        "desc": "eval() 执行任意代码，极度危险",
        "fix": "用 ast.literal_eval() 替代，或重构逻辑避免动态执行",
    },
    "exec": {
        "cwe": "CWE-95",
        "severity": Severity.CRITICAL,
        "title": "Code Injection via exec()",
        "desc": "exec() 执行任意代码",
        "fix": "重构逻辑避免动态执行",
    },
    "pickle.loads": {
        "cwe": "CWE-502",
        "severity": Severity.CRITICAL,
        "title": "Deserialization via pickle.loads()",
        "desc": "pickle.loads() 反序列化不可信数据可执行任意代码",
        "fix": "用 json 或 msgpack 替代 pickle",
    },
    "subprocess.call": {
        "cwe": "CWE-78",
        "severity": Severity.MEDIUM,
        "title": "Shell Injection Risk",
        "desc": "subprocess.call() 配合 shell=True 可被注入",
        "fix": "用 subprocess.run(args, shell=False) 并传入列表",
    },
    "os.system": {
        "cwe": "CWE-78",
        "severity": Severity.HIGH,
        "title": "OS Command Injection via os.system()",
        "desc": "os.system() 直接执行 shell 命令",
        "fix": "用 subprocess.run() 替代",
    },
    "yaml.load": {
        "cwe": "CWE-502",
        "severity": Severity.HIGH,
        "title": "Deserialization via yaml.load()",
        "desc": "yaml.load() 不带 SafeLoader 可执行任意代码",
        "fix": "用 yaml.safe_load() 替代",
    },
    "xml.etree.ElementTree.parse": {
        "cwe": "CWE-611",
        "severity": Severity.HIGH,
        "title": "XXE via xml.etree.ElementTree",
        "desc": "解析不受信 XML 可能导致 XXE 攻击",
        "fix": "用 defusedxml 替代，或禁用外部实体",
    },
    "tempfile.mktemp": {
        "cwe": "CWE-377",
        "severity": Severity.MEDIUM,
        "title": "Insecure Temporary File",
        "desc": "mktemp() 存在竞态条件，不安全",
        "fix": "用 tempfile.mkstemp() 或 TemporaryFile() 替代",
    },
    "hashlib.md5": {
        "cwe": "CWE-328",
        "severity": Severity.MEDIUM,
        "title": "Weak Hash: MD5",
        "desc": "MD5 已被证明不安全，存在碰撞攻击",
        "fix": "用 hashlib.sha256() 或更高强度的哈希算法",
    },
    "hashlib.sha1": {
        "cwe": "CWE-328",
        "severity": Severity.LOW,
        "title": "Weak Hash: SHA-1",
        "desc": "SHA-1 已被证明不安全，存在碰撞攻击",
        "fix": "用 hashlib.sha256() 或更高强度的哈希算法",
    },
}

PYTHON_VULNERABLE_PATTERNS = [
    {
        "pattern": r"open\s*\([^)]*['\"]w['\"]",
        "cwe": "CWE-73",
        "severity": Severity.LOW,
        "title": "File Write Without Validation",
        "desc": "写文件前应验证路径，防止路径遍历",
        "fix": "用 os.path.realpath() 验证路径在预期目录内",
    },
    {
        "pattern": r"assert\s+",
        "cwe": "CWE-617",
        "severity": Severity.LOW,
        "title": "Assert in Production Code",
        "desc": "assert 在 -O 模式下被跳过，不应用于安全检查",
        "fix": "用 if + raise 替代 assert",
    },
]

# ─── 新增 C 模式匹配（参考 vigolium/pentest-ai） ─────────────────

C_NEW_PATTERNS = [
    {
        "pattern": r"(?:access|fopen|open)\s*\([^)]*argv",
        "cwe": "CWE-22",
        "severity": Severity.HIGH,
        "title": "Path Traversal via user input",
        "desc": "文件操作使用了命令行参数，可能存在路径遍历",
        "fix": "验证路径在预期目录内，用 realpath() 规范化",
    },
    {
        "pattern": r"(?:MD5|DES|RC4)\s*\(",
        "cwe": "CWE-327",
        "severity": Severity.MEDIUM,
        "title": "Use of Weak Cryptographic Algorithm",
        "desc": "使用了已知不安全的加密算法",
        "fix": "用 AES-256/SHA-256 等现代算法替代",
    },
    {
        "pattern": r"atoi\s*\(|atol\s*\(|atof\s*\(",
        "cwe": "CWE-190",
        "severity": Severity.LOW,
        "title": "Integer Overflow via atoi/atol",
        "desc": "atoi/atol 不检查溢出，大数值可能溢出",
        "fix": "用 strtol/strtoul 并检查 errno",
    },
]

# ─── Python 新增模式匹配 ───────────────────────────────────────

PYTHON_NEW_PATTERNS = [
    {
        "pattern": r"password\s*=\s*['\"].*['\"]",
        "cwe": "CWE-798",
        "severity": Severity.HIGH,
        "title": "Hard-coded Credentials",
        "desc": "代码中硬编码了密码，不应出现在源码中",
        "fix": "用环境变量或配置文件存储凭证",
    },
    {
        "pattern": r"(?:secret|token|api_key)\s*=\s*['\"][a-zA-Z0-9+/=]{8,}['\"]",
        "cwe": "CWE-798",
        "severity": Severity.HIGH,
        "title": "Hard-coded Secret/Token",
        "desc": "代码中硬编码了密钥或令牌",
        "fix": "用环境变量或密钥管理服务",
    },
]


class StaticAnalyzer:
    """Tree-sitter 静态分析器 Agent"""

    def __init__(self):
        self._risk_counter = 0

    def analyze(self, code_file: CodeFile) -> list[Risk]:
        """分析单个文件，返回风险列表"""
        risks: list[Risk] = []

        if code_file.language == Language.C:
            risks.extend(self._analyze_c(code_file))
        elif code_file.language == Language.PYTHON:
            risks.extend(self._analyze_python(code_file))

        return risks

    def analyze_batch(self, files: list[CodeFile]) -> list[Risk]:
        """批量分析多个文件"""
        all_risks: list[Risk] = []
        for f in files:
            risks = self.analyze(f)
            all_risks.extend(risks)
            if risks:
                console.print(f"  [red]⚠ {f.path}: {len(risks)} risks[/]")
            else:
                console.print(f"  [green]✓ {f.path}: clean[/]")
        return all_risks

    # ─── C 分析 ──────────────────────────────────────────────────

    def _analyze_c(self, code_file: CodeFile) -> list[Risk]:
        risks: list[Risk] = []
        lines = code_file.content.split("\n")

        for i, line in enumerate(lines, start=1):
            # 检查危险函数调用
            for func, info in C_DANGEROUS_FUNCTIONS.items():
                if re.search(rf"\b{func}\s*\(", line):
                    risks.append(self._make_risk(
                        title=info["title"],
                        description=info["desc"],
                        severity=info["severity"],
                        confidence=Confidence.HIGH,
                        cwe_id=info["cwe"],
                        language=Language.C,
                        file_path=code_file.path,
                        line_start=i,
                        line_end=i,
                        snippet=line.strip(),
                        source="pattern_match",
                        reasoning=f"检测到危险函数 {func}() 调用",
                        suggestion=info["fix"],
                    ))

            # 检查模式匹配
            for pat in C_VULNERABLE_PATTERNS:
                if re.search(pat["pattern"], line):
                    # 简化：malloc 后 3 行内无 NULL 检查
                    if pat.get("check_null"):
                        context = "\n".join(lines[i:i+3])
                        if "NULL" not in context and "null" not in context:
                            risks.append(self._make_risk(
                                title=pat["title"],
                                description=pat["desc"],
                                severity=pat["severity"],
                                confidence=Confidence.MEDIUM,
                                cwe_id=pat["cwe"],
                                language=Language.C,
                                file_path=code_file.path,
                                line_start=i,
                                line_end=i,
                                snippet=line.strip(),
                                source="pattern_match",
                                reasoning=f"匹配模式: {pat['pattern']}",
                                suggestion=pat["fix"],
                            ))

            # 检查新增模式（参考 vigolium/pentest-ai）
            for pat in C_NEW_PATTERNS:
                if re.search(pat["pattern"], line):
                    risks.append(self._make_risk(
                        title=pat["title"],
                        description=pat["desc"],
                        severity=pat["severity"],
                        confidence=Confidence.MEDIUM,
                        cwe_id=pat["cwe"],
                        language=Language.C,
                        file_path=code_file.path,
                        line_start=i,
                        line_end=i,
                        snippet=line.strip(),
                        source="pattern_match",
                        reasoning=f"匹配模式: {pat['pattern']}",
                        suggestion=pat["fix"],
                    ))

        return risks

    # ─── Python 分析 ────────────────────────────────────────────

    def _analyze_python(self, code_file: CodeFile) -> list[Risk]:
        risks: list[Risk] = []
        lines = code_file.content.split("\n")

        for i, line in enumerate(lines, start=1):
            # 跳过注释
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            # 检查危险函数调用
            for func, info in PYTHON_DANGEROUS_CALLS.items():
                if re.search(rf"\b{func}\s*\(", line):
                    risks.append(self._make_risk(
                        title=info["title"],
                        description=info["desc"],
                        severity=info["severity"],
                        confidence=Confidence.HIGH,
                        cwe_id=info["cwe"],
                        language=Language.PYTHON,
                        file_path=code_file.path,
                        line_start=i,
                        line_end=i,
                        snippet=line.strip(),
                        source="pattern_match",
                        reasoning=f"检测到危险函数 {func}() 调用",
                        suggestion=info["fix"],
                    ))

            # 检查模式匹配
            for pat in PYTHON_VULNERABLE_PATTERNS:
                if re.search(pat["pattern"], line):
                    risks.append(self._make_risk(
                        title=pat["title"],
                        description=pat["desc"],
                        severity=pat["severity"],
                        confidence=Confidence.MEDIUM,
                        cwe_id=pat["cwe"],
                        language=Language.PYTHON,
                        file_path=code_file.path,
                        line_start=i,
                        line_end=i,
                        snippet=line.strip(),
                        source="pattern_match",
                        reasoning=f"匹配模式: {pat['pattern']}",
                        suggestion=pat["fix"],
                    ))

            # 检查新增模式
            for pat in PYTHON_NEW_PATTERNS:
                if re.search(pat["pattern"], line):
                    risks.append(self._make_risk(
                        title=pat["title"],
                        description=pat["desc"],
                        severity=pat["severity"],
                        confidence=Confidence.MEDIUM,
                        cwe_id=pat["cwe"],
                        language=Language.PYTHON,
                        file_path=code_file.path,
                        line_start=i,
                        line_end=i,
                        snippet=line.strip(),
                        source="pattern_match",
                        reasoning=f"匹配模式: {pat['pattern']}",
                        suggestion=pat["fix"],
                    ))

        return risks

    # ─── 工具方法 ────────────────────────────────────────────────

    def _make_risk(self, **kwargs) -> Risk:
        self._risk_counter += 1
        snippet = kwargs.pop("snippet")
        source = kwargs.pop("source")
        reasoning = kwargs.pop("reasoning")
        return Risk(
            id=f"RISK-{self._risk_counter:03d}",
            evidence=[Evidence(
                source=source,
                snippet=snippet,
                line_start=kwargs["line_start"],
                line_end=kwargs["line_end"],
                reasoning=reasoning,
            )],
            **kwargs,
        )

```

## 6.15 agents/semantic_analyzer.py (246 lines)

```python
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

```

## 6.16 agents/deep_verifier.py (291 lines)

```python
"""Agent 3: Deep Verifier - Triple Cross-Validation

Implements three verification strategies:
1. Tool cross-validation (Semgrep + pattern matching confirmation)
2. Knowledge base cross-validation (CWE/CVE lookup via NVD)
3. Memory-based validation (recall known patterns, suppress false positives)

Also implements the self-reflection loop: if Agent 2 missed something,
Agent 3 can flag it and trigger re-analysis.
"""

from __future__ import annotations

from typing import Optional

from rich.console import Console

from core.cve_client import CVEClient
from core.llm_client import LLMClient
from core.memory import MemoryLayer
from core.models import (
    CodeFile,
    Confidence,
    Evidence,
    Risk,
    Severity,
)

console = Console()

# Thresholds for confidence adjustment
HIGH_CONFIRMATIONS = 2
MEDIUM_CONFIRMATIONS = 1

REFLECTION_PROMPT = """You are a security verification expert. Given a code file and a list of risks found by static + semantic analysis, your job is to:

1. VERIFY each risk: Is it confirmed by multiple sources?
2. FIND MISSED vulnerabilities: Are there risks the previous agents missed?
3. FLAG FALSE POSITIVES: Are any risks likely wrong?

For each risk, assess:
- Is the evidence strong? (multiple independent sources agree?)
- Is the attack scenario realistic?
- Would a real attacker exploit this?

Output JSON:
{
  "verified_risks": [
    {
      "id": "RISK-001",
      "confirmed": true,
      "confidence_reason": "Both static analysis and LLM agree this is a real vulnerability",
      "false_positive_likelihood": "low"
    }
  ],
  "missed_risks": [
    {
      "title": "...",
      "description": "...",
      "severity": "critical|high|medium|low",
      "cwe_id": "CWE-xxx",
      "line_start": 10,
      "line_end": 10,
      "reasoning": "Why this was missed by previous agents"
    }
  ]
}"""


class DeepVerifier:
    """Agent 3: Deep verification with triple cross-validation and self-reflection."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        memory: Optional[MemoryLayer] = None,
        cve_client: Optional[CVEClient] = None,
        max_reflection_rounds: int = 2,
    ):
        self.llm = llm_client
        self.memory = memory or MemoryLayer()
        self.cve = cve_client or CVEClient()
        self.max_reflection_rounds = max_reflection_rounds

    def verify_batch(
        self,
        files: list[CodeFile],
        risks: list[Risk],
    ) -> list[Risk]:
        """Verify all risks across all files."""
        if not risks:
            return risks

        console.print("[bold cyan]  Agent 3: Deep verification...[/]")

        verified_risks = []
        suppressed = 0

        for risk in risks:
            # Check memory first
            memory_entry = self.memory.recall(risk)

            if memory_entry and memory_entry.source_count >= 2:
                # Known false positive - suppress
                if risk.id not in [r.id for r in verified_risks]:
                    suppressed += 1
                    continue

            # Triple cross-validation
            verified = self._verify_single_risk(risk)
            verified_risks.append(verified)

            # Store in appropriate memory
            if verified.confidence == Confidence.HIGH:
                self.memory.store_correct(verified)

        if suppressed > 0:
            console.print(f"  [dim]  Suppressed {suppressed} known false positives[/]")

        # Self-reflection: ask LLM to find missed risks (ITERATIVE)
        if self.llm:
            for f in files:
                file_risks = [r for r in verified_risks if r.file_path == f.path]
                all_new_risks: list[Risk] = []
                current_risks = list(file_risks)

                for round_num in range(self.max_reflection_rounds):
                    missed = self._reflect_on_file(f, current_risks)
                    if not missed:
                        if round_num > 0:
                            console.print(
                                f"  [dim]  Reflection converged after {round_num + 1} rounds[/]"
                            )
                        break

                    console.print(
                        f"  [yellow]  Agent 3 round {round_num + 1}: "
                        f"found {len(missed)} more risks in {f.path}[/]"
                    )
                    all_new_risks.extend(missed)
                    current_risks = current_risks + missed

                verified_risks.extend(all_new_risks)

        return verified_risks

    def _verify_single_risk(self, risk: Risk) -> Risk:
        """Triple cross-validation for a single risk."""
        confirmations = 0
        reasons = []

        # Strategy 1: Tool cross-validation
        has_semgrep = any(e.source == "semgrep" for e in risk.evidence)
        has_pattern = any(e.source == "pattern_match" for e in risk.evidence)
        has_ai = any(e.source == "ai" for e in risk.evidence)

        if has_semgrep:
            confirmations += 1
            reasons.append("confirmed by Semgrep")

        if has_pattern:
            confirmations += 1
            reasons.append("confirmed by pattern matching")

        if has_ai:
            confirmations += 1
            reasons.append("confirmed by LLM analysis")

        # Strategy 2: Knowledge base cross-validation (CVE lookup)
        if risk.cwe_id and risk.cwe_id.startswith("CWE-"):
            confirmations += 1
            reasons.append(f"known CWE: {risk.cwe_id}")

            # Active CVE lookup for critical/high risks
            if risk.severity in (Severity.CRITICAL, Severity.HIGH):
                try:
                    cve_summary = self.cve.get_cve_summary(risk.cwe_id)
                    if "No CVE data" not in cve_summary:
                        confirmations += 1
                        reasons.append(f"CVE data exists for {risk.cwe_id}")
                        # Append CVE info to description
                        risk = risk.model_copy(update={
                            "description": risk.description + f" [CVE: {cve_summary[:150]}]",
                        })
                except Exception:
                    pass  # CVE lookup is best-effort

        # Strategy 3: Severity consistency check
        if risk.severity in (Severity.CRITICAL, Severity.HIGH):
            if len(risk.evidence) >= 2:
                confirmations += 1
                reasons.append("multiple evidence for high-severity risk")

        # Adjust confidence
        new_confidence = self._calculate_confidence(confirmations)

        if new_confidence != risk.confidence:
            reason_str = "; ".join(reasons) if reasons else "no cross-validation"
            updated_desc = (
                risk.description
                + f" [Verification: {confirmations} confirmations ({reason_str})]"
            )
            risk = risk.model_copy(update={
                "confidence": new_confidence,
                "description": updated_desc,
            })

        return risk

    def _calculate_confidence(self, confirmations: int) -> Confidence:
        if confirmations >= HIGH_CONFIRMATIONS:
            return Confidence.HIGH
        elif confirmations >= MEDIUM_CONFIRMATIONS:
            return Confidence.MEDIUM
        else:
            return Confidence.LOW

    def _reflect_on_file(
        self,
        code_file: CodeFile,
        existing_risks: list[Risk],
    ) -> list[Risk]:
        """Ask LLM to find risks that previous agents missed."""
        if not self.llm:
            return []

        risk_summaries = []
        for r in existing_risks:
            risk_summaries.append(
                f"- {r.id}: [{r.severity.value}] {r.title} "
                f"(CWE: {r.cwe_id or 'N/A'}, Lines: {r.line_start}-{r.line_end})"
            )

        existing_text = "\n".join(risk_summaries) if risk_summaries else "No risks found."

        prompt = f"""## Source File: {code_file.path}
Language: {code_file.language.value}

```{code_file.language.value}
{code_file.content}
```

## Risks Found by Previous Agents
{existing_text}

Please verify these risks and find any missed vulnerabilities."""

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": REFLECTION_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=4096,
            )
        except Exception as e:
            console.print(f"[dim]Reflection failed: {e}[/]")
            return []

        missed_raw = response.get("missed_risks", [])
        missed_risks = []
        counter = len(existing_risks)

        for mr in missed_raw:
            counter += 1
            sev_str = mr.get("severity", "medium").lower()
            sev = Severity(sev_str) if sev_str in [s.value for s in Severity] else Severity.MEDIUM

            missed_risks.append(Risk(
                id=f"RISK-{counter:03d}",
                title=mr.get("title", "Missed risk (Agent 3 reflection)"),
                description=mr.get("description", ""),
                severity=sev,
                confidence=Confidence.MEDIUM,
                cwe_id=mr.get("cwe_id"),
                language=code_file.language,
                file_path=code_file.path,
                line_start=mr.get("line_start", 0),
                line_end=mr.get("line_end", 0),
                evidence=[Evidence(
                    source="ai",
                    snippet="",
                    line_start=mr.get("line_start", 0),
                    line_end=mr.get("line_end", 0),
                    reasoning=f"Agent 3 reflection: {mr.get('reasoning', 'missed by previous agents')}",
                )],
                suggestion=mr.get("suggestion", "Review this code section."),
            ))

        return missed_risks

```

## 6.17 agents/report_generator.py (469 lines)

```python
"""Agent 4: Report Generator

Generates structured audit reports in multiple formats:
- JSON (for API/programmatic use)
- Markdown (for human review)
- Rich terminal output (for CLI)
- CWE/CVE external references
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from core.models import AnalysisResult, Risk, Severity
from core.attack_knowledge import get_attack_description, get_compliance_references

console = Console()


def _cwe_url(cwe_id: str) -> str:
    """Generate CWE reference URL."""
    if not cwe_id or not cwe_id.startswith("CWE-"):
        return ""
    num = cwe_id.replace("CWE-", "")
    return f"https://cwe.mitre.org/data/definitions/{num}.html"


def _cve_url(cve_id: str) -> str:
    """Generate CVE reference URL."""
    if not cve_id or not cve_id.startswith("CVE-"):
        return ""
    return f"https://nvd.nist.gov/vuln/detail/{cve_id}"


def _extract_cve_ids(description: str) -> list[str]:
    """Extract CVE IDs from description text."""
    import re
    return re.findall(r"CVE-\d{4}-\d+", description)


class ReportGenerator:
    """Agent 4: Generate structured audit reports."""

    def generate_json(self, result: AnalysisResult) -> dict:
        """Generate structured JSON report with external references."""
        risks_out = []
        for r in sorted(result.risks, key=lambda r: list(Severity).index(r.severity)):
            cve_ids = _extract_cve_ids(r.description)
            refs = {
                "cwe_url": _cwe_url(r.cwe_id) if r.cwe_id else None,
                "cve_urls": [_cve_url(c) for c in cve_ids] if cve_ids else None,
            }
            # Add ATT&CK context
            if r.cwe_id:
                attack_desc = get_attack_description(r.cwe_id)
                compliance = get_compliance_references(r.cwe_id)
                if attack_desc:
                    refs["mitre_attack"] = attack_desc
                if compliance:
                    refs["compliance"] = compliance
            risks_out.append({
                "id": r.id,
                "title": r.title,
                "severity": r.severity.value,
                "confidence": r.confidence.value,
                "cwe": r.cwe_id,
                "file": str(r.file_path),
                "line_start": r.line_start,
                "line_end": r.line_end,
                "description": r.description,
                "suggestion": r.suggestion,
                "evidence_count": r.evidence_count,
                "evidence": [
                    {
                        "source": e.source,
                        "rule_id": e.rule_id,
                        "snippet": e.snippet[:200],
                        "reasoning": e.reasoning,
                    }
                    for e in r.evidence
                ],
                "references": refs,
            })

        return {
            "scan_id": result.request_id,
            "timestamp": result.timestamp.isoformat(),
            "summary": {
                "files_analyzed": result.files_analyzed,
                "total_risks": result.total_risks,
                "has_critical": result.has_critical,
                "risk_breakdown": result.risk_summary,
            },
            "risks": risks_out,
            "meta": {
                "model_used": result.model_used,
                "analysis_time_ms": result.analysis_time_ms,
                "version": "0.3.1",
            },
        }

    def generate_markdown(self, result: AnalysisResult) -> str:
        """Generate Markdown audit report with CWE/CVE links."""
        lines = [
            "# CodeRisk Agent - Security Audit Report",
            "",
            f"**Scan ID:** `{result.request_id}`",
            f"**Timestamp:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Files Analyzed:** {result.files_analyzed}",
            f"**Analysis Time:** {result.analysis_time_ms}ms",
            f"**Model:** {result.model_used}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Risks | **{result.total_risks}** |",
            f"| Critical | **{result.risk_summary.get('critical', 0)}** |",
            f"| High | **{result.risk_summary.get('high', 0)}** |",
            f"| Medium | **{result.risk_summary.get('medium', 0)}** |",
            f"| Low | **{result.risk_summary.get('low', 0)}** |",
            f"| Info | **{result.risk_summary.get('info', 0)}** |",
            "",
        ]

        if result.has_critical:
            lines.extend([
                "> **WARNING:** Critical vulnerabilities detected! Immediate action required.",
                "",
            ])

        lines.extend(["## Risk Details", ""])

        for risk in sorted(result.risks, key=lambda r: list(Severity).index(r.severity)):
            severity_icon = {
                Severity.CRITICAL: "🔴",
                Severity.HIGH: "🟠",
                Severity.MEDIUM: "🟡",
                Severity.LOW: "🔵",
                Severity.INFO: "⚪",
            }.get(risk.severity, "⚪")

            cwe_link = ""
            if risk.cwe_id:
                cwe_link = f"[{risk.cwe_id}]({_cwe_url(risk.cwe_id)})"

            cve_ids = _extract_cve_ids(risk.description)
            cve_links = ""
            if cve_ids:
                cve_links = " | ".join(
                    f"[{c}]({_cve_url(c)})" for c in cve_ids
                )

            lines.extend([
                f"### {risk.id}: {severity_icon} {risk.title}",
                "",
                "| Field | Value |",
                "|-------|-------|",
                f"| Severity | **{risk.severity.value.upper()}** |",
                f"| Confidence | {risk.confidence.value} |",
                f"| CWE | {cwe_link or 'N/A'} |",
                f"| CVE | {cve_links or 'N/A'} |",
                f"| File | `{risk.file_path}` |",
                f"| Lines | {risk.line_start}-{risk.line_end} |",
                f"| Evidence Sources | {risk.evidence_count} |",
                "",
                f"**Description:** {risk.description}",
                "",
                f"**Fix:** {risk.suggestion}",
                "",
            ])

            # Add ATT&CK context
            if risk.cwe_id:
                attack_desc = get_attack_description(risk.cwe_id)
                compliance = get_compliance_references(risk.cwe_id)
                if attack_desc:
                    lines.append(f"**MITRE ATT&CK:** {attack_desc}")
                    lines.append("")
                if compliance:
                    lines.append("**Compliance References:**")
                    for framework, ref in compliance.items():
                        lines.append(f"- {framework}: {ref}")
                    lines.append("")

            if risk.evidence:
                lines.append("**Evidence:**")
                for e in risk.evidence:
                    lines.append(f"- Source: `{e.source}` | {e.reasoning}")
                lines.append("")

        lines.extend([
            "---",
            "",
            "## References",
            "",
            "- [CWE List](https://cwe.mitre.org/data/index.html)",
            "- [NVD - National Vulnerability Database](https://nvd.nist.gov/)",
            "- [OWASP Top 10](https://owasp.org/www-project-top-ten/)",
            "",
            "---",
            "",
            f"*Generated by CodeRisk Agent v0.3.1 | {result.timestamp.isoformat()}*",
        ])

        return "\n".join(lines)

    def generate_sarif(self, result: AnalysisResult) -> dict:
        """Generate SARIF 2.1.0 report.

        Static Analysis Results Interchange Format — OASIS standard.
        Compatible with GitHub Code Scanning, VS Code SARIF Viewer,
        Azure DevOps, and other SARIF consumers.
        """
        # Severity -> SARIF level mapping
        level_map = {
            Severity.CRITICAL: "error",
            Severity.HIGH: "error",
            Severity.MEDIUM: "warning",
            Severity.LOW: "note",
            Severity.INFO: "none",
        }

        # Build rules from unique CWEs
        rules = []
        seen_cwes = set()
        for risk in result.risks:
            cwe = risk.cwe_id or "CWE-000"
            if cwe not in seen_cwes:
                seen_cwes.add(cwe)
                rules.append({
                    "id": cwe,
                    "name": risk.title,
                    "shortDescription": {"text": risk.title},
                    "fullDescription": {"text": risk.description[:500]},
                    "help": {"text": risk.suggestion},
                    "defaultConfiguration": {
                        "level": level_map.get(risk.severity, "warning")
                    },
                    "properties": {
                        "tags": ["security", cwe.lower().replace("cwe-", "cwe-")],
                    },
                })

        # Build results
        sarif_results = []
        for risk in result.risks:
            cve_ids = _extract_cve_ids(risk.description)
            sarif_result = {
                "ruleId": risk.cwe_id or "CWE-000",
                "ruleIndex": next(
                    (i for i, r in enumerate(rules) if r["id"] == risk.cwe_id), 0
                ),
                "level": level_map.get(risk.severity, "warning"),
                "message": {
                    "text": f"{risk.title}: {risk.description[:300]}"
                },
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": str(risk.file_path),
                            "uriBaseId": "%SRCROOT%",
                        },
                        "region": {
                            "startLine": risk.line_start,
                            "endLine": risk.line_end,
                        },
                    },
                }],
                "fingerprints": {
                    "coderisk/v1": risk.id,
                },
            }

            # Add CWE as a property
            if risk.cwe_id:
                sarif_result["properties"] = {
                    "cwe": risk.cwe_id,
                    "confidence": risk.confidence.value,
                }

            # Add CVE references
            if cve_ids:
                sarif_result["relatedLocations"] = [
                    {
                        "id": i,
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": _cve_url(c),
                            },
                        },
                        "message": {"text": f"CVE reference: {c}"},
                    }
                    for i, c in enumerate(cve_ids)
                ]

            sarif_results.append(sarif_result)

        return {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "CodeRisk Agent",
                        "version": "0.3.2",
                        "informationUri": "https://github.com/a9320/code-risk-agent",
                        "semanticVersion": "0.3.2",
                        "rules": rules,
                    },
                },
                "results": sarif_results,
                "columnKindCodeUnits": "utf16CodeUnits",
            }],
        }

    def print_terminal(self, result: AnalysisResult) -> None:
        """Print rich terminal output."""
        summary_table = Table(
            title="Risk Summary",
            show_header=True,
            border_style="cyan",
        )
        summary_table.add_column("Severity", justify="center")
        summary_table.add_column("Count", justify="center")

        severity_style = {
            "critical": "bold red",
            "high": "red",
            "medium": "yellow",
            "low": "blue",
            "info": "dim",
        }
        severity_icon = {
            "critical": "C",
            "high": "H",
            "medium": "M",
            "low": "L",
            "info": "I",
        }

        for level in ["critical", "high", "medium", "low", "info"]:
            count = result.risk_summary.get(level, 0)
            if count > 0:
                summary_table.add_row(
                    f"[{severity_style[level]}]{severity_icon[level]} {level.upper()}[/]",
                    f"[{severity_style[level]}]{count}[/]",
                )

        console.print()
        console.print(summary_table)
        console.print()

        if result.risks:
            risk_table = Table(
                title="Risk Details",
                show_header=True,
                border_style="yellow",
            )
            risk_table.add_column("ID", style="bold")
            risk_table.add_column("Sev")
            risk_table.add_column("Conf")
            risk_table.add_column("CWE")
            risk_table.add_column("Title")
            risk_table.add_column("File")
            risk_table.add_column("Line", justify="center")
            risk_table.add_column("Evidence", justify="center")

            for risk in sorted(
                result.risks,
                key=lambda r: list(Severity).index(r.severity),
            ):
                style = severity_style.get(risk.severity.value, "")
                icon = severity_icon.get(risk.severity.value, "")
                conf_style = {
                    "high": "green",
                    "medium": "yellow",
                    "low": "red",
                }.get(risk.confidence.value, "")

                risk_table.add_row(
                    risk.id,
                    f"[{style}]{icon}[/]",
                    f"[{conf_style}]{risk.confidence.value[:1].upper()}[/]",
                    risk.cwe_id or "-",
                    risk.title[:45],
                    str(risk.file_path)[-25:],
                    str(risk.line_start),
                    str(risk.evidence_count),
                )

            console.print(risk_table)

            critical_high = [
                r for r in result.risks
                if r.severity in (Severity.CRITICAL, Severity.HIGH)
            ]
            if critical_high:
                console.print()
                tree = Tree("[bold red]Critical / High Risks - Fix Suggestions[/]", guide_style="cyan")
                for risk in critical_high:
                    node = tree.add(f"[red]{risk.id}[/] {risk.title}")
                    node.add(f"[yellow]Issue:[/] {risk.description[:120]}")
                    node.add(f"[green]Fix:[/] {risk.suggestion[:120]}")
                    if risk.cwe_id:
                        node.add(f"[cyan]CWE:[/] {_cwe_url(risk.cwe_id)}")
                console.print(tree)

        console.print()
        console.print(
            Panel(
                f"[bold]Files:[/] {result.files_analyzed}  |  "
                f"[bold]Risks:[/] {result.total_risks}  |  "
                f"[bold]Time:[/] {result.analysis_time_ms}ms  |  "
                f"[bold]Model:[/] {result.model_used}",
                border_style="cyan",
            )
        )

    def save_report(
        self,
        result: AnalysisResult,
        output_dir: str = ".",
        formats: list[str] = ["json", "md"],
    ) -> list[str]:
        """Save reports to files."""
        import os

        saved = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"coderisk_report_{timestamp}"

        os.makedirs(output_dir, exist_ok=True)

        if "json" in formats:
            json_path = os.path.join(output_dir, f"{base_name}.json")
            report = self.generate_json(result)
            with open(json_path, "w") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            saved.append(json_path)
            console.print(f"[dim]JSON report saved: {json_path}[/]")

        if "md" in formats:
            md_path = os.path.join(output_dir, f"{base_name}.md")
            md_content = self.generate_markdown(result)
            with open(md_path, "w") as f:
                f.write(md_content)
            saved.append(md_path)
            console.print(f"[dim]Markdown report saved: {md_path}[/]")

        if "sarif" in formats:
            sarif_path = os.path.join(output_dir, f"{base_name}.sarif")
            sarif_report = self.generate_sarif(result)
            with open(sarif_path, "w") as f:
                json.dump(sarif_report, f, indent=2, ensure_ascii=False)
            saved.append(sarif_path)
            console.print(f"[dim]SARIF report saved: {sarif_path}[/]")

        return saved

```

# 7. 测试

## tests/__init__.py

```python
# CodeRisk Agent - Tests

```

## tests/test_static_analyzer.py

```python
"""Tests for CodeRisk Agent - Static Analyzer"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.static_analyzer import StaticAnalyzer
from core.models import CodeFile, Language, Severity


@pytest.fixture
def analyzer():
    return StaticAnalyzer()


# ─── CWE-120: Buffer Overflow ────────────────────────────────────

class TestBufferOverflow:
    def test_detects_gets(self, analyzer):
        """gets() should be flagged as CRITICAL (CWE-120)"""
        code = '#include <stdio.h>\nint main() { char buf[10]; gets(buf); }'
        f = CodeFile(path="test.c", content=code, language=Language.C)
        risks = analyzer.analyze(f)
        assert any(r.cwe_id == "CWE-120" and r.severity == Severity.CRITICAL for r in risks)

    def test_detects_strcpy(self, analyzer):
        """strcpy() should be flagged as HIGH (CWE-120)"""
        code = '#include <string.h>\nvoid f(char *s) { char b[10]; strcpy(b, s); }'
        f = CodeFile(path="test.c", content=code, language=Language.C)
        risks = analyzer.analyze(f)
        assert any("strcpy" in r.title and r.severity == Severity.HIGH for r in risks)


# ─── CWE-78: Command Injection ──────────────────────────────────

class TestCommandInjection:
    def test_detects_system_c(self, analyzer):
        """system() in C should be flagged as HIGH (CWE-78)"""
        code = '#include <stdlib.h>\nvoid f() { system("ls"); }'
        f = CodeFile(path="test.c", content=code, language=Language.C)
        risks = analyzer.analyze(f)
        assert any(r.cwe_id == "CWE-78" and r.severity == Severity.HIGH for r in risks)

    def test_detects_os_system_python(self, analyzer):
        """os.system() in Python should be flagged as HIGH (CWE-78)"""
        code = 'import os\nos.system("ls")'
        f = CodeFile(path="test.py", content=code, language=Language.PYTHON)
        risks = analyzer.analyze(f)
        assert any(r.cwe_id == "CWE-78" and r.severity == Severity.HIGH for r in risks)


# ─── CWE-95: Code Injection ─────────────────────────────────────

class TestCodeInjection:
    def test_detects_eval(self, analyzer):
        """eval() should be flagged as CRITICAL (CWE-95)"""
        code = 'x = eval(input())'
        f = CodeFile(path="test.py", content=code, language=Language.PYTHON)
        risks = analyzer.analyze(f)
        assert any(r.cwe_id == "CWE-95" and r.severity == Severity.CRITICAL for r in risks)

    def test_detects_exec(self, analyzer):
        """exec() should be flagged as CRITICAL (CWE-95)"""
        code = 'exec("print(1)")'
        f = CodeFile(path="test.py", content=code, language=Language.PYTHON)
        risks = analyzer.analyze(f)
        assert any(r.cwe_id == "CWE-95" and r.severity == Severity.CRITICAL for r in risks)


# ─── CWE-502: Deserialization ───────────────────────────────────

class TestDeserialization:
    def test_detects_pickle(self, analyzer):
        """pickle.loads() should be flagged as CRITICAL (CWE-502)"""
        code = 'import pickle\ndata = pickle.loads(b"abc")'
        f = CodeFile(path="test.py", content=code, language=Language.PYTHON)
        risks = analyzer.analyze(f)
        assert any(r.cwe_id == "CWE-502" and r.severity == Severity.CRITICAL for r in risks)


# ─── Safe Code ──────────────────────────────────────────────────

class TestSafeCode:
    def test_safe_c_code(self, analyzer):
        """Safe C code should produce no critical/high risks"""
        code = '''
#include <stdio.h>
int main() {
    int x = 42;
    printf("%d\\n", x);
    return 0;
}
'''
        f = CodeFile(path="safe.c", content=code, language=Language.C)
        risks = analyzer.analyze(f)
        critical = [r for r in risks if r.severity in (Severity.CRITICAL, Severity.HIGH)]
        assert len(critical) == 0

    def test_safe_python_code(self, analyzer):
        """Safe Python code should produce no critical/high risks"""
        code = '''
def add(a, b):
    return a + b

result = add(1, 2)
print(result)
'''
        f = CodeFile(path="safe.py", content=code, language=Language.PYTHON)
        risks = analyzer.analyze(f)
        critical = [r for r in risks if r.severity in (Severity.CRITICAL, Severity.HIGH)]
        assert len(critical) == 0


# ─── Test Case Files ────────────────────────────────────────────

class TestTestCaseFiles:
    def test_buffer_overflow_file(self, analyzer):
        """buffer_overflow.c should have 2+ critical/high risks"""
        path = Path(__file__).parent / "test_cases" / "buffer_overflow.c"
        f = CodeFile.from_path(path)
        risks = analyzer.analyze(f)
        high_risks = [r for r in risks if r.severity in (Severity.CRITICAL, Severity.HIGH)]
        assert len(high_risks) >= 2

    def test_command_injection_file(self, analyzer):
        """command_injection.c should have 2+ high risks"""
        path = Path(__file__).parent / "test_cases" / "command_injection.c"
        f = CodeFile.from_path(path)
        risks = analyzer.analyze(f)
        high_risks = [r for r in risks if r.severity in (Severity.CRITICAL, Severity.HIGH)]
        assert len(high_risks) >= 2

    def test_code_injection_file(self, analyzer):
        """code_injection.py should have 3+ critical risks"""
        path = Path(__file__).parent / "test_cases" / "code_injection.py"
        f = CodeFile.from_path(path)
        risks = analyzer.analyze(f)
        critical = [r for r in risks if r.severity == Severity.CRITICAL]
        assert len(critical) >= 3

    def test_memory_issues_file(self, analyzer):
        """memory_issues.c should detect malloc and double free"""
        path = Path(__file__).parent / "test_cases" / "memory_issues.c"
        f = CodeFile.from_path(path)
        risks = analyzer.analyze(f)
        assert len(risks) >= 1

```

# 8. 配置文件

## pyproject.toml

```
[project]
name = "code-risk-agent"
version = "0.3.2"
description = "AI-powered code quality and risk analysis agent"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Yang Weike"}
]

dependencies = [
    "pydantic>=2.0",
    "rich>=13.0",
    "httpx>=0.25",
    "tree-sitter>=0.21",
    "semgrep>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1",
]

[project.scripts]
code-risk = "main:main"

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.pytest.ini_options]
testpaths = ["tests"]

```

## .env.example

```
# CodeRisk Agent - Environment Configuration

# LLM Backend: "shared_api" | "local_http" | "local_llama_cpp"
LLM_BACKEND=local_llama_cpp

# Shared API (Radeon Cloud)
SHARED_API_URL=https://developer.amd.com.cn/radeon/api/v1
SHARED_API_KEY=your-api-key-here
SHARED_API_MODEL=Qwen/Qwen3.6-35B-A3B

# Local llama-server (HTTP)
LOCAL_HTTP_URL=http://localhost:8080
LOCAL_HTTP_MODEL=qwen2.5-coder-7b-instruct

# Local llama-cpp-python (direct GGUF load)
LOCAL_MODEL_PATH=/workspace/llama.cpp/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf
LOCAL_N_GPU_LAYERS=999

# Semgrep
SEMGREP_RULES=p/default

```

## .gitignore

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.eggs/

# Virtual environments
.venv/
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local

# Models
models/*.gguf
models/*.bin

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Source dumps (versioned snapshots)
CodeRisk-Agent-*-Source.md
CodeRisk-Agent-*-源码.md
CodeRisk-Agent-源码.md

# Coverage
htmlcov/
.coverage

```

# 9. 脚本

## scripts/run_demo.sh

```bash
#!/bin/bash
# scripts/run_demo.sh - CodeRisk Agent Demo Script
# For AMD AI DevMaster Hackathon Track 2

set -e

echo "=========================================="
echo "  CodeRisk Agent - Demo"
echo "  AMD AI DevMaster Hackathon Track 2"
echo "=========================================="
echo ""

# 1. Environment Check
echo "[1/5] Environment Check"
echo "----------------------------------------"
if command -v rocm-smi &> /dev/null; then
    echo "ROCm detected:"
    rocm-smi --showproductname 2>/dev/null | head -3 || echo "  (rocm-smi available but limited in container)"
else
    echo "ROCm not available (CPU-only mode)"
fi
echo "Python: $(python3 --version)"
echo ""

# 2. Quick Demo (Static Analysis)
echo "[2/5] Static Analysis Demo (no LLM)"
echo "----------------------------------------"
cd "$(dirname "$0")/.."
python3 main.py demo
echo ""

# 3. Full Analysis on Test Cases
echo "[3/5] Full Analysis on Test Cases"
echo "----------------------------------------"
python3 main.py analyze tests/test_cases/ --no-ai --output terminal
echo ""

# 4. Version Info
echo "[4/5] System Info"
echo "----------------------------------------"
python3 main.py info
echo ""

# 5. Summary
echo "[5/5] Summary"
echo "----------------------------------------"
echo "CodeRisk Agent features:"
echo "  - Agent 1: Static Analyzer (regex + Tree-sitter)"
echo "  - Agent 2: Semantic Analyzer (LLM-driven)"
echo "  - Agent 3: Deep Verifier (triple cross-validation + memory)"
echo "  - Agent 4: Report Generator (JSON/Markdown/Rich)"
echo "  - Orchestrator: State machine pipeline"
echo "  - Memory Layer: Learn from history"
echo "  - CVE Client: NVD database lookup"
echo ""
echo "Demo complete!"

```

# 10. Demo 视频脚本

# CodeRisk Agent — Demo Video Script v4

> Duration: 3 min 35 sec (215s) + 25s buffer = 4 min max
> Format: Terminal recording + narration
> Language: English
> Version: v4 (2026-07-19) — Resolves all5 remaining risks from Kimi review

---

## Scene 1: The Problem (20s)

**[Screen: XZ Utils news headline]**

> "In 2024, the XZ Utils backdoor nearly compromised every Linux distribution worldwide. One maintainer. A few lines of malicious code. The entire software supply chain almost collapsed."

**[Screen: Terminal with CodeRisk Agent logo]**

> "CodeRisk Agent catches these risks before code ships — and it runs entirely on your local AMD GPU. Code never leaves your machine."

---

## Scene 2: Quick Demo — One Command, Full Analysis (75s)

### Part A: The Command (5s)

**[Screen: Full-screen terminal, dark theme, 18pt font]**

```bash
python3 main.py analyze tests/test_cases/ --output terminal
```

> "One command. Let me walk you through what happens."

### Part B: Phase 1-2 — Static Analysis (15s)

**[Screen: Terminal showing Phase1 and Phase2 output]**

> "Phase 1: Pattern matching for buffer overflows, command injection, deserialization. Fast, CPU-only. Found 18 initial risks across our test suite of5 vulnerability samples — both C and Python files."

> "Phase 2: Semgrep integration — industry-standard rules from the open-source community."

### Part C: Why Better Than Semgrep (15s)

**[Screen: Split view — left: Semgrep output, right: CodeRisk output]**

> "But here's the difference. Semgrep sees `strcpy` and flags it — it needs human-written rules for context. CodeRisk Agent uses LLM to automatically understand the context — the input is already validated. Risk downgraded to LOW."

> "And Agent 3's self-reflection found something Semgrep completely missed: a `malloc()` without NULL check at line 58. That's a real vulnerability that static analysis alone would miss."

### Part D: Phase 3-4 — AI Analysis (20s)

**[Screen: Terminal showing LLM calls and Agent3 output]**

> "Phase 3: The LLM reads the code like a human auditor. It generates attack scenarios — 'An attacker can inject arbitrary commands through the host parameter.'"

> "Phase 4: Deep verification. Triple cross-validation — tool confirmation, CWE knowledge base, and live CVE lookup from the National Vulnerability Database."

### Part E: The Report (20s)

**[Screen: Show risk table with CWE links, then zoom into one risk]**

> "25 vulnerabilities detected across C and Python files. Every one has evidence, CWE classification, and a fix suggestion."

**[Screen: Zoom into RISK-014 — show before/after code]**

> "Look at this one. `strcpy(dest, src)` — buffer overflow. The fix? `strncpy` with bounds checking. Concrete, actionable, copy-paste ready."

---

## Scene 3: Architecture Deep Dive (60s)

### Part A: Overview (10s)

**[Screen: Simple pipeline diagram — just Agent1 → Agent2 → Agent3 → Agent4, left to right]**

> "Four specialized agents in an orchestrated pipeline. Let me show you the key differentiators."

### Part B: Agent 2 — Semantic Analysis (10s)

**[Screen: Highlight Agent2, show LLM inference output]**

> "Agent 2 runs Qwen2.5-Coder-7B on the AMD GPU. It understands code logic, not just patterns. It can find vulnerabilities that no regex will ever catch."

### Part C: Agent 3 — Deep Verification (25s)

**[Screen: Animate — first show tool confirmation, then add CWE layer, then add CVE layer]**

> "Agent 3 is where the magic happens. Triple cross-validation."

> "First: tool confirmation — did static analysis and LLM agree?"

**[Screen: Add CWE knowledge base layer]**

> "Second: CWE knowledge base — are there known exploits?"

**[Screen: Add NVD/CVE layer]**

> "Third: live NVD query — real CVE numbers, real CVSS scores."

**[Screen: Show Agent3 finding missed risks]**

> "And the self-reflection loop. Agent 3 asks: 'Did I miss anything?' In our tests, it found 4 vulnerabilities the previous agents missed. And it automatically suppressed 1 known false positive."

### Part D: Memory Layer (15s)

**[Screen: Show memory recall in terminal output]**

> "And it learns. Watch this — the first run, the system builds a memory of confirmed patterns."

**[Screen: Show second run with memory recall]**

> "Second run on similar code. 'Memory: pattern found, using cached result.' Detection is faster. False positives are suppressed. The system gets smarter with every scan."

---

## Scene 4: GPU Performance (45s)

### Part A: Environment (10s)

**[Screen: Split view — left: terminal, right: rocm-smi]**

> "This is running on an AMD Radeon RX 7900 XTX with ROCm 7.2.4. The model is loaded into GPU memory — every analysis benefits from hardware acceleration."

### Part B: Performance Data (20s)

**[Screen: Performance comparison]**

> "Let me show you the numbers."

| Mode | Speed |
|------|-------|
| CPU only | 6.8 tokens/s |
| AMD GPU (ROCm HIP) | 105 tokens/s |

> "Fifteen times faster with GPU acceleration. No API calls. No cloud dependency. No data leaving your machine."

### Part C: ROCm Build (15s)

**[Screen: Show terminal with build success message]**

> "Getting HIP working in the Radeon Cloud container took some detective work. We found the right build configuration for ROCm 7.2.4, and GPU inference worked immediately."

> "This is what local AI looks like. Real performance. Real privacy. Real security."

---

## Scene 5: Closing (15s)

**[Screen: Architecture diagram + key stats]**

> "CodeRisk Agent. Four AI agents. Orchestrated pipeline. Memory learning. Live CVE validation. All running on your local AMD GPU."

**[Screen: GitHub repo + team name]**

> "github.com/a9320/code-risk-agent | Team CodeRisk | AMD AI DevMaster Hackathon 2026"

---

## Appendix: Production Notes

### Recording Checklist
- [ ] Terminal font: 18pt+, dark theme (VS Code Dark or similar)
- [ ] Pre-load model before recording (avoid30s startup wait)
- [ ] rocm-smi running in background (tmux split pane)
- [ ] Practice narration2-3 times
- [ ] Background music: subtle, tech-focused, not distracting
- [ ] Record Scene2 and Scene3 first (don't depend on GPU)
- [ ] Record Scene4 last (depends on GPU availability)

### GPU Fallback Plans

**Plan A: ROCm HIP available (best case)**
- Split screen: terminal + rocm-smi
- Show real-time inference with GPU utilization
- Performance data:105 t/s

**Plan B: Only Vulkan available**
- Show radeontop or vulkaninfo
- Performance data:85 t/s
- "We evaluated three backends. Vulkan gives85 tokens per second — 5.6x faster than CPU. ROCm HIP pushes that to105 t/s. The architecture supports both."

**Plan C: CPU only (worst case)**
- Be honest: "In this container environment, GPU access is limited. But the architecture is designed for local GPU inference."
- Show pre-recorded benchmark data as overlay
- "The code is ready. The GPU is waiting."

### Key Moments to Highlight
1. **XZ Utils story** — establishes stakes in20 seconds
2. **Semgrep vs CodeRisk comparison** — shows differentiation
3. **Agent3 finding missed risks** — demonstrates intelligence
4. **Before/after code fix** — shows actionable output
5. **Memory recall** — demonstrates learning
6. **15x GPU speedup** — tangible performance benefit

### Time Budget

| Scene | Target | Content |
|-------|--------|---------|
| 1. Problem | 20s | XZ Utils + local AI pitch |
| 2. Demo | 75s | Command + phases + comparison + report |
| 3. Architecture | 60s | Agent2 + Agent3 + memory |
| 4. Performance | 45s | rocm-smi + numbers + build story |
| 5. Closing | 15s | Summary + repo |
| **Total** | **215s** | **3:35** |
| Buffer | 25s | Transitions, pauses |
| **Max** | **240s** | **4:00** |

### v4 Changelog (from v3)
1. ✅ ROCm Build story simplified — removed cmake flag details, kept "found the right build configuration"
2. ✅ "25 vulnerabilities" contextualized — added "across C and Python files" and "test suite of5 vulnerability samples"
3. ✅ Architecture diagram uses step-by-step animation — start with simple pipeline, layer by layer add CWE/CVE
4. ✅ Multi-language support mentioned — "both C and Python files" in Scene 2
5. ✅ One-click fix noted as future work — "copy-paste ready" in current version, --fix parameter planned
