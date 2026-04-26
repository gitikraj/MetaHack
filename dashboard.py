"""
dashboard.py – Rich-powered terminal metrics dashboard.

Functions
─────────
  print_summary(results)          – After running all cases
  print_agent_report(result)      – Detailed single-case view
  print_benchmark(metrics)        – Benchmark statistics table
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

try:
    from rich import box
    from rich.columns import Columns
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    console = Console()
except ImportError:
    console = None

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _bar(value: float, width: int = 20) -> str:
    """ASCII progress bar for 0-1 float."""
    filled = max(0, min(width, int(value * width)))
    color = "green" if value >= 0.7 else "yellow" if value >= 0.4 else "red"
    return f"[{color}]{'█' * filled}{'░' * (width - filled)}[/{color}] {value:.3f}"

def _reward_color(r: float) -> str:
    if r >= 0.65:
        return "bold green"
    if r >= 0.40:
        return "yellow"
    return "bold red"

# ─────────────────────────────────────────────────────────────────────────────
# Summary table (all cases)
# ─────────────────────────────────────────────────────────────────────────────
def print_summary(results: List[Dict[str, Any]]) -> None:
    if console is None:
        print(f"Evaluated {len(results)} cases")
        return
    
    table = Table(
        title="[bold cyan]CyberMultiAgent – Run Summary[/bold cyan]",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("Case ID", style="cyan", no_wrap=True)
    table.add_column("Attack", style="white")
    table.add_column("True", style="white")
    table.add_column("✓", justify="center", width=3)
    table.add_column("Score", justify="right")
    table.add_column("Reward", justify="right")

    for r in results:
        ev = r["eval_result"]
        pred_attack = r["prediction"]["attack_type"]
        true_attack = ev.correct_attack
        
        check = "✓" if ev.correct_attack else "✗"
        table.add_row(
            r["case_id"],
            pred_attack[:15],
            "True" if true_attack else "False",
            check,
            f"{ev.scores.final_score:.3f}",
            f"[{_reward_color(ev.reward)}]{ev.reward:+.3f}[/{_reward_color(ev.reward)}]",
        )

    console.print(table)

# ─────────────────────────────────────────────────────────────────────────────
# Detailed single-case report
# ─────────────────────────────────────────────────────────────────────────────
def print_agent_report(result: Dict[str, Any]) -> None:
    if console is None:
        print(f"Case: {result['case_id']}")
        print(f"Attack: {result['prediction']['attack_type']}")
        return
    
    case_id = result.get("case_id", "?")
    pred = result["prediction"]
    ev = result["eval_result"]

    console.rule(f"[bold cyan]Case: {case_id}[/bold cyan]")

    atk_color = "bold green" if ev.correct_attack else "bold red"
    console.print(
        Panel(
            f"[{atk_color}]{pred['attack_type']}[/{atk_color}]",
            title="Attack Classification",
        )
    )

    scores_table = Table(title="Scores", box=box.SIMPLE)
    scores_table.add_column("Dimension")
    scores_table.add_column("Score")
    s = ev.scores
    for name, val in [
        ("Logs", s.logs_score),
        ("Code", s.code_score),
        ("Requirements", s.requirements_score),
        ("Attack Type", s.attack_type_score),
        ("Final Score", s.final_score),
    ]:
        scores_table.add_row(name, f"{val:.3f}")

    console.print(scores_table)
    console.print(f"[bold]Reward:[/bold] [{_reward_color(ev.reward)}]{ev.reward:.4f}[/{_reward_color(ev.reward)}]")

def print_benchmark(metrics: Any, results: Optional[List[Dict[str, Any]]] = None) -> None:
    if console is None:
        print("Benchmark Results")
        print(f"Total Cases: {metrics.total_cases}")
        return
    
    console.rule("[bold cyan]Benchmark Report[/bold cyan]")

    overview = Table(title="Overall Metrics", box=box.DOUBLE_EDGE, header_style="bold magenta")
    overview.add_column("Metric")
    overview.add_column("Value")

    rows = [
        ("Total Cases", str(metrics.total_cases)),
        ("Mean Reward", f"{metrics.mean_reward:.4f}"),
        ("Mean Final Score", f"{metrics.mean_final_score:.4f}"),
        ("Attack Type Accuracy", f"{metrics.attack_type_accuracy:.2%}"),
    ]
    for label, val in rows:
        overview.add_row(label, val)
    console.print(overview)
