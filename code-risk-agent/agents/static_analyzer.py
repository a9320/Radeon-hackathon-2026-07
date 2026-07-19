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
