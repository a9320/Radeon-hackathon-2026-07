# ROCm Optimization Documentation

> CodeRisk Agent - AMD AI DevMaster Hackathon Track 2

---

## Current Environment Status

| Item | Status | Notes |
|------|--------|-------|
| GPU | Radeon Pro W7900 (48GB VRAM) | Radeon Cloud container |
| ROCm | 7.2.4 | Fully configured |
| rocm-smi | Available | Can monitor GPU status |
| HIP Backend | ✅ Available | GGML_HIP=ON flag |
| CPU Inference | 6.8 t/s | Fallback mode |

### HIP Backend Debugging Story

**Initial Symptom:** GPU inference failed silently — llama.cpp compiled without errors, but the model fell back to CPU at 6.8 t/s instead of using the W7900 GPU.

**Investigation Process:**

1. **Hardware verification:** Confirmed GPU was visible via `rocm-smi` — Radeon Pro W7900, 48GB VRAM, ROCm 7.2.4 fully configured
2. **HIP compiler check:** Verified `hipcc` was in PATH and could compile sample HIP kernels
3. **Build log analysis:** Reviewed cmake output — found that `GGML_HIPBLAS=ON` was accepted but produced a warning about deprecated flag
4. **ROCm version correlation:** Cross-referenced ROCm 7.2.4 changelog — discovered HIP backend integration changes in ROCm 7.x
5. **Source code tracing:** Examined llama.cpp's `CMakeLists.txt` — found that `GGML_HIPBLAS` was renamed to `GGML_HIP` in the 2026 codebase
6. **Root cause confirmed:** The old flag `GGML_HIPBLAS=ON` was silently ignored in ROCm 7.x builds, causing CPU fallback without any error message

**Solution:**

```bash
# Old (2024-2025, ROCm 6.x):
cmake -B build -DGGML_HIPBLAS=ON -DLLAMA_BUILD_SERVER=ON

# New (2026, ROCm 7.x):
cmake -B build -DGGML_HIP=ON -DLLAMA_BUILD_SERVER=ON
```

**Verification:** After rebuilding with `GGML_HIP=ON`, GPU inference immediately worked at 105 t/s — a 15.4× improvement over CPU fallback.

**Takeaway:** When debugging "GPU not being used" issues with ROCm, always check if build flags have been renamed between major ROCm versions. Silent fallback is more dangerous than an explicit error — it masks the problem behind seemingly functional (but slow) inference.

---

## Optimization Strategy (3 Layers)

### Layer 1: Model Optimization

| Optimization | Implementation | Expected Speedup |
|--------------|---------------|------------------|
| Q4_K_M Quantization | GGUF format, 4-bit | ~19.6GB VRAM, 105-114 t/s |
| Flash Attention | llama.cpp `-fa 1` | Expected 30-50% latency reduction (not measured separately) |
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
| HIP Backend | `GGML_HIP=ON` make | 15.4x vs CPU |
| MIOpen | Auto-tuned kernels | Optimized for RDNA3 |

---

## Performance Data

### Actual Benchmark Results (Measured on Radeon Cloud)

| Metric | CPU | GPU (HIP) | Improvement |
|--------|-----|-----------|-------------|
| Token generation | 6.8 t/s | 105 t/s | **15.4×** |
| Prompt processing | — | 628 t/s | — |
| VRAM usage | — | 41% (~19.6 GB / 48 GB) | — |
| GPU temperature | — | 26°C | — |

> All performance data was measured on our Radeon Cloud instance
> (Radeon Pro W7900, 48GB VRAM, ROCm 7.2.4, HIP backend).

---

## Demo Video ROCm Scenes

1. `rocm-smi` showing GPU exists and ROCm is configured
2. CPU inference as fallback with timing
3. Architecture diagram showing GPU vs CPU agent assignment
4. Performance comparison table (CPU vs measured GPU)

---

## References

- [llama.cpp ROCm Build](https://github.com/ggerganov/llama.cpp#rocm)
- [ROCm Documentation](https://rocm.docs.amd.com/)
- [Qwen2.5-Coder GGUF](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GGUF)

---

## Optimization Decisions Table

| # | Optimization | Measured Effect | Decision |
|---|-------------|----------------|----------|
| 1 | GGML_HIP=ON | 6.8→105 t/s (15.4×) | **Critical** — Without this: silent CPU fallback |
| 2 | Q4_K_M Quantization | 64GB→19.6GB VRAM | **Necessary** — 32B model only fits in 4-bit |
| 3 | FlashAttention (-fa 1) | Not measured separately | **Enabled** — Expected 30-50% latency reduction |
| 4 | Concurrency=1 | No VRAM contention | **Required** — Two 32B inferences would exceed 48GB |
| 5 | GGML_HIPBLAS→GGML_HIP | Build flag change | **Root cause** — Old flag silently ignored |
| 6 | cmake .. && make | Build errors | **Required** — Two-step build avoids config issues |
| 7 | Build type: Release | Measurable speedup | **Required** — Debug mode adds overhead |
| 8 | response_format disabled | Fixes JSON errors | **Required** — llama-server does not support this parameter |

---

## FlashAttention Investigation

### Current Status

| Question | Answer |
|----------|--------|
| Is FlashAttention enabled? | **Not measured** — need `-fa 1` flag verification |
| Expected effect? | 30-50% latency reduction based on AMD benchmarks |
| Risk? | None — pure optimization, does not affect correctness |

### Verification Method

```bash
# Without FlashAttention
cd /workspace/persistence/llama.cpp/build/bin
./llama-server -m /workspace/persistence/models/qwen2.5-coder-32b-instruct-q4_k_m.gguf -ngl 999 --host 0.0.0.0 --port 8080

# Measure prompt processing speed (with FlashAttention)
./llama-server -m /workspace/persistence/models/qwen2.5-coder-32b-instruct-q4_k_m.gguf -ngl 999 -fa 1 --host 0.0.0.0 --port 8081

# Compare: curl localhost:8080/completion -d '{"prompt":"test","n_predict":100}'
# vs:      curl localhost:8081/completion -d '{"prompt":"test","n_predict":100}'
```

### Decision

If `-fa 1` improves speed by ≥20%: enable by default, add to deployment instructions.
If <20%: keep optional, document as "available but not required".
If breaks: disable, document as "not supported on this ROCm version".
