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
- **Detection methods:** Regex patterns + Semgrep rules

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
| Static Analysis | Regex + Semgrep |
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
