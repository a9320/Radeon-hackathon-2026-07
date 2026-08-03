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
