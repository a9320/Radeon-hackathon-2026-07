"""CodeRisk Agent - AI Code Quality & Risk Analyzer

Usage:
    code-risk analyze <path>   Analyze code files/directory
    code-risk demo             Run demo analysis
    code-risk info             Show configuration

Options:
    --no-ai                    Disable LLM semantic analysis
    --semgrep-config <rules>   Semgrep rules (default: p/default)
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

BANNER = r"""[bold cyan]
 ██████╗ ██████╗ ██████╗ ███████╗    ██████╗ ██╗███████╗██╗  ██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗██║██╔════╝██║ ██╔╝
██║     ██║   ██║██║  ██║█████╗      ██████╔╝██║███████╗█████╔╝
██║     ██║   ██║██║  ██║██╔══╝      ██╔══██╗██║╚════██║██╔═██╗
╚██████╗╚██████╔╝██████╔╝███████╗    ██║  ██║██║███████║██║  ██╗
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝
[/]"""

VERSION = "0.2.0"

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
) -> None:
    """Analyze code files or directory."""
    path = Path(path_str)

    if not path.exists():
        console.print(f"[red]Path not found: {path}[/]")
        sys.exit(1)

    files = collect_files(path)
    if not files:
        console.print(f"[yellow]No supported code files found ({', '.join(SUPPORTED_EXTENSIONS)})[/]")
        sys.exit(0)

    console.print(f"\n[bold]Scanning {len(files)} files...[/]\n")

    # Phase 1: Static analysis (regex patterns)
    static_analyzer = StaticAnalyzer()
    start = time.monotonic()
    all_risks = static_analyzer.analyze_batch(files)
    elapsed_ms = int((time.monotonic() - start) * 1000)

    # Phase 2: Semgrep analysis
    try:
        from core.semgrep_runner import analyze_with_semgrep
        for f in files:
            semgrep_risks = analyze_with_semgrep(
                f, config=semgrep_config, risk_counter_start=len(all_risks)
            )
            if semgrep_risks:
                console.print(f"  [red]  Semgrep {f.path}: {len(semgrep_risks)} risks[/]")
                all_risks.extend(semgrep_risks)
    except Exception as e:
        console.print(f"[dim]Semgrep skipped: {e}[/]")

    # Phase 3: LLM semantic analysis (optional)
    if enable_ai:
        try:
            from core.llm_client import LLMClient
            from agents.semantic_analyzer import SemanticAnalyzer

            with LLMClient() as llm:
                semantic = SemanticAnalyzer(llm)
                for f in files:
                    file_risks = [r for r in all_risks if r.file_path == f.path]
                    if file_risks:
                        enriched = semantic.analyze(f, file_risks)
                        # Replace risks for this file
                        all_risks = [r for r in all_risks if r.file_path != f.path]
                        all_risks.extend(enriched)
        except Exception as e:
            console.print(f"[yellow]LLM analysis skipped: {e}[/]")

    # Build result
    result = AnalysisResult(
        request_id=f"scan-{int(time.time())}",
        files_analyzed=len(files),
        risks=all_risks,
        analysis_time_ms=elapsed_ms,
        model_used="static+semgrep" + ("+llm" if enable_ai else ""),
    )

    _print_results(result)


def cmd_demo() -> None:
    """Run demo analysis."""
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

    analyzer = StaticAnalyzer()
    files = [demo_c, demo_py]

    console.print("[bold]Demo files:[/]")
    for f in files:
        console.print(f"  - {f.path} ({f.language.value})")
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
    """Show configuration info."""
    table = Table(title="CodeRisk Agent Config", show_header=True)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", VERSION)
    table.add_row("Model", "Qwen2.5-Coder-7B-Instruct")
    table.add_row("Backends", "Shared API + llama-server + llama-cpp-python")
    table.add_row("Analyzers", "Static (regex) + Semgrep + LLM semantic")
    table.add_row("Languages", "C (.c/.h) + Python (.py)")
    table.add_row("CWE Rules", "CWE-120/134/476/415/78/95/502/73/617")

    console.print(table)


def _print_results(result: AnalysisResult) -> None:
    """Format and print analysis results."""
    console.print()

    # Summary table
    summary_table = Table(title="Risk Summary", show_header=True, border_style="cyan")
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
        "critical": "[red]C[/]",
        "high": "[red]H[/]",
        "medium": "[yellow]M[/]",
        "low": "[blue]L[/]",
        "info": "[dim]I[/]",
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

    # Detail table
    if result.risks:
        risk_table = Table(title="Risk Details", show_header=True, border_style="yellow")
        risk_table.add_column("ID", style="bold")
        risk_table.add_column("Sev")
        risk_table.add_column("CWE")
        risk_table.add_column("Title")
        risk_table.add_column("File")
        risk_table.add_column("Line", justify="center")
        risk_table.add_column("Evidence", justify="center")

        for risk in sorted(result.risks, key=lambda r: list(Severity).index(r.severity)):
            style = severity_style.get(risk.severity.value, "")
            icon = severity_icon.get(risk.severity.value, "")
            risk_table.add_row(
                risk.id,
                f"[{style}]{icon}[/]",
                risk.cwe_id or "-",
                risk.title[:50],
                str(risk.file_path)[-30:],
                str(risk.line_start),
                str(risk.evidence_count),
            )

        console.print(risk_table)

        # Fix suggestions tree
        console.print()
        tree = Tree("[bold]Fix Suggestions[/]", guide_style="cyan")
        for risk in result.risks:
            if risk.severity in (Severity.CRITICAL, Severity.HIGH):
                node = tree.add(f"[red]{risk.id}[/] {risk.title}")
                node.add(f"[yellow]Issue:[/] {risk.description[:100]}")
                node.add(f"[green]Fix:[/] {risk.suggestion[:100]}")
        console.print(tree)

    # Footer stats
    console.print(
        Panel(
            f"[bold]Files:[/] {result.files_analyzed}  |  "
            f"[bold]Risks:[/] {result.total_risks}  |  "
            f"[bold]Time:[/] {result.analysis_time_ms}ms  |  "
            f"[bold]Model:[/] {result.model_used}",
            border_style="cyan",
        )
    )


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
        if "--semgrep-config" in args:
            idx = args.index("--semgrep-config")
            if idx + 1 < len(args):
                semgrep_config = args[idx + 1]
        cmd_analyze(args[1], enable_ai=enable_ai, semgrep_config=semgrep_config)
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
