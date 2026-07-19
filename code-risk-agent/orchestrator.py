"""Orchestrator: State Machine Pipeline

Manages the complete analysis flow through states:
INIT -> PARSE -> ANALYZE -> VERIFY -> REPORT -> DONE

Coordinates all 4 agents with proper dependency management.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Optional

from rich.console import Console

from agents.deep_verifier import DeepVerifier
from agents.report_generator import ReportGenerator
from agents.semantic_analyzer import SemanticAnalyzer
from agents.static_analyzer import StaticAnalyzer
from core.llm_client import LLMClient
from core.models import (
    AnalysisRequest,
    AnalysisResult,
    CodeFile,
    Language,
)

console = Console()

# Minimum file line count to trigger LLM analysis (skip tiny files)
MIN_LINES_FOR_LLM = 20


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
        self.verifier = DeepVerifier(llm_client)
        self.reporter = ReportGenerator()

    def run(
        self,
        request: AnalysisRequest,
        output_format: str = "terminal",
    ) -> AnalysisResult:
        """Run the complete analysis pipeline.

        Args:
            request: Analysis request with files and options
            output_format: "terminal", "json", "md", or "all"

        Returns:
            AnalysisResult with all risks and metadata
        """
        start_time = time.monotonic()

        # State: PARSE
        self.state = State.PARSE
        console.print(f"\n[bold cyan]Orchestrator: Analyzing {len(request.files)} files...[/]\n")

        # Validate files
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

        # State: ANALYZE - Agent 1 (Static) + Agent 2 (Semantic) + Semgrep
        self.state = State.ANALYZE
        all_risks = []

        # Phase 1: Static analysis (regex patterns)
        console.print("[bold]  Phase 1: Static analysis (Agent 1)[/]")
        for f in valid_files:
            risks = self.static_analyzer.analyze(f)
            all_risks.extend(risks)
            if risks:
                console.print(f"  [red]  {f.path}: {len(risks)} risks[/]")
            else:
                console.print(f"  [green]  {f.path}: clean[/]")

        # Phase 2: Semgrep analysis
        console.print("\n[bold]  Phase 2: Semgrep analysis[/]")
        try:
            from core.semgrep_runner import analyze_with_semgrep
            for f in valid_files:
                semgrep_risks = analyze_with_semgrep(
                    f, config=request.rules[0], risk_counter_start=len(all_risks)
                )
                if semgrep_risks:
                    console.print(
                        f"  [red]  Semgrep {f.path}: {len(semgrep_risks)} risks[/]"
                    )
                    all_risks.extend(semgrep_risks)
        except Exception as e:
            console.print(f"[dim]  Semgrep skipped: {e}[/]")

        # Phase 3: LLM semantic analysis (skip small files)
        if request.enable_ai and self.semantic_analyzer:
            console.print("\n[bold]  Phase 3: LLM semantic analysis (Agent 2)[/]")
            for f in valid_files:
                file_risks = [r for r in all_risks if r.file_path == f.path]

                # Skip LLM for small files with no risks
                if f.line_count < MIN_LINES_FOR_LLM and not file_risks:
                    console.print(f"  [dim]  {f.path}: skipped (small file, {f.line_count} lines)[/]")
                    continue

                try:
                    enriched = self.semantic_analyzer.analyze(f, file_risks)
                    # Replace risks for this file
                    all_risks = [r for r in all_risks if r.file_path != f.path]
                    all_risks.extend(enriched)
                except Exception as e:
                    console.print(f"  [yellow]  LLM analysis failed for {f.path}: {e}[/]")

        # State: VERIFY - Agent 3 (Deep Verifier)
        self.state = State.VERIFY
        console.print("\n[bold]  Phase 4: Deep verification (Agent 3)[/]")
        all_risks = self.verifier.verify_batch(valid_files, all_risks)

        # State: REPORT - Agent 4 (Report Generator)
        self.state = State.REPORT
        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        model_desc = "static+semgrep"
        if request.enable_ai and self.llm:
            model_desc += "+llm"
        model_desc += "+verify"

        result = AnalysisResult(
            request_id=f"scan-{int(time.time())}",
            files_analyzed=len(valid_files),
            risks=all_risks,
            analysis_time_ms=elapsed_ms,
            model_used=model_desc,
        )

        # Generate output
        console.print(f"\n[bold]  Phase 5: Report generation (Agent 4)[/]")
        if output_format == "terminal" or output_format == "all":
            self.reporter.print_terminal(result)
        if output_format in ("json", "md", "all"):
            self.reporter.save_report(result, formats=["json", "md"])

        self.state = State.DONE
        console.print(f"\n[green]  Analysis complete. {result.total_risks} risks found in {elapsed_ms}ms.[/]")

        return result

    def _validate_files(self, files: list[CodeFile]) -> list[CodeFile]:
        """Validate and filter files."""
        valid = []
        for f in files:
            if not f.content.strip():
                console.print(f"[yellow]  Skipping empty file: {f.path}[/]")
                continue
            if f.language == Language.UNKNOWN:
                console.print(f"[yellow]  Skipping unsupported file: {f.path}[/]")
                continue
            valid.append(f)
        return valid

    @property
    def current_state(self) -> str:
        return self.state.value
