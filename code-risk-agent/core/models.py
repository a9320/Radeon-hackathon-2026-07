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
    LOCAL = "local"


class LLMConfig(BaseModel):
    """LLM 客户端配置"""
    backend: LLMBackend = LLMBackend.SHARED_API
    api_url: str = ""
    api_key: str = ""
    model: str = ""
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
