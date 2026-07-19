"""CodeRisk Agent — AI 代码质量与风险智能体

Usage:
    code-risk analyze <path>     分析代码文件/目录
    code-risk demo               运行演示分析
    code-risk info               显示配置信息
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from agents.static_analyzer import StaticAnalyzer
from core.models import AnalysisResult, CodeFile, Language, Severity

console = Console()

BANNER = """[bold cyan]
 ██████╗ ██████╗ ██████╗ ███████╗    ██████╗ ██╗███████╗██╗  ██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗██║██╔════╝██║ ██╔╝
██║     ██║   ██║██║  ██║█████╗      ██████╔╝██║███████╗█████╔╝
██║     ██║   ██║██║  ██║██╔══╝      ██╔══██╗██║╚════██║██╔═██╗
╚██████╗╚██████╔╝██████╔╝███████╗    ██║  ██║██║███████║██║  ██╗
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝
[/]"""

VERSION = "0.1.0"


def cmd_analyze(path_str: str) -> None:
    """分析代码文件或目录"""
    path = Path(path_str)

    if not path.exists():
        console.print(f"[red]✗ 路径不存在: {path}[/]")
        sys.exit(1)

    # 收集文件
    files: list[CodeFile] = []
    extensions = {".c", ".h", ".py"}

    if path.is_file():
        if path.suffix in extensions:
            files.append(CodeFile.from_path(path))
        else:
            console.print(f"[red]✗ 不支持的文件类型: {path.suffix}[/]")
            sys.exit(1)
    else:
        for ext in extensions:
            files.extend(
                CodeFile.from_path(f) for f in path.rglob(f"*{ext}") if f.is_file()
            )

    if not files:
        console.print("[yellow]⚠ 未找到可分析的代码文件 (.c/.h/.py)[/]")
        sys.exit(0)

    console.print(f"\n[bold]📂 扫描 {len(files)} 个文件...[/]\n")

    # 静态分析
    analyzer = StaticAnalyzer()
    start = time.monotonic()
    risks = analyzer.analyze_batch(files)
    elapsed_ms = int((time.monotonic() - start) * 1000)

    # 构建结果
    result = AnalysisResult(
        request_id=f"scan-{int(time.time())}",
        files_analyzed=len(files),
        risks=risks,
        analysis_time_ms=elapsed_ms,
        model_used="pattern_matcher",
    )

    # 输出结果
    _print_results(result)


def cmd_demo() -> None:
    """运行演示分析"""
    console.print("[bold cyan]🎯 CodeRisk Agent 演示[/]\n")

    demo_c = CodeFile(
        path=Path("demo/vulnerable.c"),
        content="""#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int login(char *input) {
    char password[32];
    strcpy(password, input);    // 危险: 无边界检查
    if (strcmp(password, "admin123") == 0) {
        printf("Welcome!\\n");
        system("echo logged in");  // 危险: 命令注入
        return 1;
    }
    return 0;
}

void process() {
    char *buf = malloc(256);     // 危险: 未检查 NULL
    gets(buf);                    // 危险: 缓冲区溢出
    printf(buf);                  // 危险: 格式字符串
    free(buf);
    free(buf);                    // 危险: 双重释放
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
    return os.system(cmd)  # 危险: 命令注入

@app.route("/load")
def load_data():
    data = request.get_data()
    return pickle.loads(data)  # 危险: 反序列化

@app.route("/calc")
def calculate():
    expr = request.args.get("expr")
    return str(eval(expr))  # 危险: 代码注入
""",
        language=Language.PYTHON,
    )

    analyzer = StaticAnalyzer()
    files = [demo_c, demo_py]

    console.print("[bold]📂 演示文件:[/]")
    for f in files:
        console.print(f"  • {f.path} ({f.language.value})")
    console.print()

    risks = analyzer.analyze_batch(files)

    result = AnalysisResult(
        request_id="demo-001",
        files_analyzed=2,
        risks=risks,
        analysis_time_ms=0,
        model_used="pattern_matcher (demo)",
    )

    _print_results(result)


def cmd_info() -> None:
    """显示配置信息"""
    table = Table(title="CodeRisk Agent 配置", show_header=True)
    table.add_column("配置项", style="cyan")
    table.add_column("值", style="green")

    table.add_row("版本", VERSION)
    table.add_row("模型", "Qwen2.5-Coder-7B-Instruct")
    table.add_row("后端", "共享 API (Radeon Cloud) + 本地 llama.cpp")
    table.add_row("分析器", "Tree-sitter + Pattern Matcher")
    table.add_row("支持语言", "C (.c/.h) + Python (.py)")
    table.add_row("CWE 规则", "CWE-120/134/476/415/78/95/502/73/617")

    console.print(table)


def _print_results(result: AnalysisResult) -> None:
    """格式化输出分析结果"""
    console.print()

    # 风险统计表
    summary_table = Table(title="📊 风险统计", show_header=True, border_style="cyan")
    summary_table.add_column("等级", justify="center")
    summary_table.add_column("数量", justify="center")

    severity_style = {
        "critical": "bold red",
        "high": "red",
        "medium": "yellow",
        "low": "blue",
        "info": "dim",
    }
    severity_icon = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🔵",
        "info": "⚪",
    }

    for level in ["critical", "high", "medium", "low", "info"]:
        count = result.risk_summary.get(level, 0)
        if count > 0:
            summary_table.add_row(
                f"{severity_icon[level]} {level.upper()}",
                f"[{severity_style[level]}]{count}[/]",
            )

    console.print(summary_table)
    console.print()

    # 详细风险列表
    if result.risks:
        risk_table = Table(title="🔍 风险详情", show_header=True, border_style="yellow")
        risk_table.add_column("ID", style="bold")
        risk_table.add_column("等级")
        risk_table.add_column("CWE")
        risk_table.add_column("标题")
        risk_table.add_column("文件")
        risk_table.add_column("行号", justify="center")
        risk_table.add_column("证据数", justify="center")

        for risk in sorted(result.risks, key=lambda r: list(Severity).index(r.severity)):
            style = severity_style.get(risk.severity.value, "")
            icon = severity_icon.get(risk.severity.value, "")
            risk_table.add_row(
                risk.id,
                f"[{style}]{icon} {risk.severity.value.upper()}[/]",
                risk.cwe_id or "—",
                risk.title,
                str(risk.file_path),
                str(risk.line_start),
                str(risk.evidence_count),
            )

        console.print(risk_table)

        # 建议树
        console.print()
        tree = Tree("[bold]💡 修复建议[/]", guide_style="cyan")
        for risk in result.risks:
            if risk.severity in (Severity.CRITICAL, Severity.HIGH):
                node = tree.add(f"[red]{risk.id}[/] {risk.title}")
                node.add(f"[yellow]问题:[/] {risk.description}")
                node.add(f"[green]修复:[/] {risk.suggestion}")
        console.print(tree)

    # 底部统计
    console.print(
        Panel(
            f"[bold]文件:[/] {result.files_analyzed}  |  "
            f"[bold]风险:[/] {result.total_risks}  |  "
            f"[bold]耗时:[/] {result.analysis_time_ms}ms  |  "
            f"[bold]模型:[/] {result.model_used}",
            border_style="cyan",
        )
    )


# ─── CLI 入口 ────────────────────────────────────────────────────

def main():
    console.print(BANNER)

    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        console.print(__doc__)
        return

    cmd = args[0]

    if cmd == "analyze":
        if len(args) < 2:
            console.print("[red]✗ 用法: code-risk analyze <path>[/]")
            sys.exit(1)
        cmd_analyze(args[1])
    elif cmd == "demo":
        cmd_demo()
    elif cmd == "info":
        cmd_info()
    else:
        console.print(f"[red]✗ 未知命令: {cmd}[/]")
        console.print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
