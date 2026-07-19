# CodeRisk Agent 🛡️

AI 代码质量与风险智能体 — AMD AI DevMaster Hackathon Track 2 参赛项目

## 特性

- 🔍 **静态分析** — Tree-sitter AST 解析 + Semgrep 规则扫描
- 🤖 **AI 审查** — Qwen2.5-Coder-7B 驱动的智能代码审查
- 🔄 **自省循环** — Agent 自我验证，三重交叉确认
- 📊 **可解释** — 完整证据链，每个风险都有来源
- 🐍🐢 **双语言** — 深度支持 C + Python

## 架构

```
                    ┌─────────────┐
                    │ Orchestrator│
                    └──────┬──────┘
                           │
        ┌──────────┬───────┼───────┬──────────┐
        ▼          ▼       ▼       ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │Static  │ │Semantic│ │Pattern │ │Report  │
   │Analyzer│ │Analyzer│ │Matcher │ │Generator│
   └────────┘ └────────┘ └────────┘ └────────┘
```

## 快速开始

```bash
# 安装
pip install -e .

# 配置
cp .env.example .env
# 编辑 .env 填入 API Key

# 运行
code-risk analyze ./path/to/code
```

## 技术栈

- **模型:** Qwen2.5-Coder-7B-Instruct（统一模型）
- **推理:** llama.cpp (ROCm) / 共享 API 双后端
- **分析:** Tree-sitter + Semgrep
- **搜索:** Meilisearch（记忆层）
- **CLI:** Rich 终端 UI

## 许可

MIT
