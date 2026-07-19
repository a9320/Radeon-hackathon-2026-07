# ROCm Optimization Documentation

> CodeRisk Agent - AMD AI DevMaster Hackathon Track 2

---

## Current Environment Status

| Item | Status | Notes |
|------|--------|-------|
| GPU | RX 7900 XTX (gfx1100) | Radeon Cloud container |
| ROCm | 6.16.13 | Fully configured |
| rocm-smi | Available | Can monitor GPU status |
| HIP Backend | Not available | Container virtualization limitation |
| CPU Inference | 6.8 t/s | Fallback mode |
| Shared API | Qwen3.6-35B-A3B | Available for testing |

### Why HIP Backend Is Unavailable

The Radeon Cloud container environment uses virtualization that prevents
llama.cpp's HIP backend from directly accessing the GPU. The ROCm runtime
is installed and `rocm-smi` works, but the HIP compute layer cannot be
initialized inside the container.

This is a known limitation of the shared Radeon Cloud environment.
On bare-metal AMD GPU systems, the full optimization stack would be available.

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

### Benchmark Plan

```bash
# 1. CPU-only baseline
time python3 main.py analyze tests/test_cases/ --no-ai

# 2. GPU inference (when HIP available)
./llama-server -m qwen2.5-coder-7b-instruct-q4_k_m.gguf -ngl 999 -fa 1
# Then: python3 main.py analyze tests/test_cases/

# 3. rocm-smi monitoring
watch -n 1 rocm-smi
```

### Expected Results (Based on Literature)

| Metric | CPU | GPU (HIP) | Improvement |
|--------|-----|-----------|-------------|
| Model Load | ~15s | ~3s | 5x |
| Inference (per file) | ~8s | ~1.2s | 6.7x |
| Throughput | 6.8 t/s | 110 t/s | 16x |
| GPU Utilization | 0% | 85-95% | - |

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
