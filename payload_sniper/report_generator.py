"""
Report Generator & Formatter for PayloadSniper INP & Script Audits.
Outputs terminal tables, Markdown documents, and JSON objects.
"""

import json
from typing import Dict, Any, List

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def print_terminal_report(audit_result: Dict[str, Any]) -> None:
    """Print complete script audit report to terminal."""
    if not HAS_RICH:
        _print_plain_report(audit_result)
        return

    console = Console()

    url = audit_result.get("url", "")
    score = audit_result.get("overall_score", 0.0)
    grade = audit_result.get("grade", "F")
    stats = audit_result.get("stats", {})
    inp = audit_result.get("inp_estimate", {})

    score_color = "green" if score >= 80 else ("yellow" if score >= 55 else "red")

    header = Text()
    header.append("PayloadSniper: INP, Long Tasks & Script Bloat-Tracer\n", style="bold magenta")
    header.append(f"Target URL: {url}\n", style="bold white")
    header.append(f"Script Performance Score: {score}/100 (Grade: {grade})\n", style=f"bold {score_color}")
    header.append(
        f"Mode: {audit_result.get('mode')} | Total Scripts: {stats.get('total_scripts')} | "
        f"Third-Party Tags: {stats.get('third_party_scripts')} | TBT: {stats.get('total_blocking_time_ms')}ms | "
        f"Estimated INP: {inp.get('estimated_inp_ms')}ms",
        style="dim",
    )

    console.print(Panel(header, border_style="magenta"))

    # Component Scores Table
    comp = audit_result.get("component_scores", {})
    comp_table = Table(title="Component Score Breakdown", show_header=True, header_style="bold cyan")
    comp_table.add_column("Component Dimension", style="white")
    comp_table.add_column("Weight", justify="center", style="dim")
    comp_table.add_column("Score", justify="center")

    for name, weight, key in [
        ("Total Blocking Time (TBT)", "35%", "total_blocking_time"),
        ("Estimated INP Readiness", "25%", "estimated_inp_readiness"),
        ("Third-Party Script Overhead", "20%", "third_party_overhead"),
        ("Script Loading Hygiene", "10%", "script_loading_hygiene"),
        ("Bundle & Tag Efficiency", "10%", "bundle_efficiency"),
    ]:
        val = comp.get(key, 0.0)
        c = "green" if val >= 75 else ("yellow" if val >= 50 else "red")
        comp_table.add_row(name, weight, f"[{c}]{val}/100[/{c}]")

    console.print(comp_table)

    # INP Assessment Panel
    inp_text = Text()
    inp_text.append("Interaction to Next Paint (INP) Vulnerability Assessment\n", style="bold yellow")
    inp_text.append(f"Estimated Interaction Latency: {inp.get('estimated_inp_ms')}ms\n", style="bold white")
    inp_text.append(f"Status: {inp.get('status')}\n", style="bold")
    inp_text.append(f"Google 200ms Target Passed: {inp.get('meets_google_target')}\n", style="dim")
    inp_text.append(f"Max Long Task: {stats.get('max_long_task_ms')}ms | Total Long Tasks: {stats.get('long_tasks_count')}", style="dim")

    console.print(Panel(inp_text, border_style="green" if inp.get("meets_google_target") else "red"))

    # Vendor Breakdown Table
    vendors = audit_result.get("vendor_breakdown", [])
    if vendors:
        v_table = Table(title="Script Origins & Vendor Attribution", show_header=True, header_style="bold cyan")
        v_table.add_column("Vendor", style="white")
        v_table.add_column("Category", style="dim")
        v_table.add_column("Type", justify="center")
        v_table.add_column("Tags", justify="center")
        v_table.add_column("Render Blocking", justify="center")

        for v in vendors:
            type_str = "[yellow]Third-Party[/yellow]" if v.get("is_third_party") else "[green]First-Party[/green]"
            block_str = f"[red]{v.get('blocking_scripts')}[/red]" if v.get("blocking_scripts", 0) > 0 else "[green]0[/green]"
            v_table.add_row(
                v.get("vendor", ""),
                v.get("category", ""),
                type_str,
                str(v.get("script_count", 0)),
                block_str,
            )

        console.print(v_table)

    # Long Tasks Table
    long_tasks = audit_result.get("long_tasks", [])
    if long_tasks:
        lt_table = Table(title="Captured Main-Thread Long Tasks (> 50ms)", show_header=True, header_style="bold red")
        lt_table.add_column("Start", justify="center", style="dim")
        lt_table.add_column("Duration", justify="center", style="bold red")
        lt_table.add_column("Blocking", justify="center", style="red")
        lt_table.add_column("Attributed Vendor", style="white")
        lt_table.add_column("Initiator", style="dim", max_width=45, overflow="ellipsis")

        for lt in long_tasks[:8]:
            lt_table.add_row(
                f"{lt.get('start_time')}ms",
                f"{lt.get('duration')}ms",
                f"+{lt.get('blocking_time')}ms",
                lt.get("vendor", ""),
                lt.get("initiating_source", ""),
            )

        console.print(lt_table)

    # Recommendations Table
    recs = audit_result.get("recommendations", [])
    if recs:
        rec_table = Table(title="Actionable Core Web Vitals & INP Fixes", show_header=True, header_style="bold green")
        rec_table.add_column("Priority", justify="center", style="dim")
        rec_table.add_column("Recommended Remediation Step", style="white")
        for i, r in enumerate(recs, 1):
            rec_table.add_row(str(i), r)
        console.print(rec_table)

    console.print()


def _print_plain_report(audit_result: Dict[str, Any]) -> None:
    """Fallback plain text output when rich is not available."""
    print(f"\n=== PayloadSniper: INP & Script Performance Audit ===")
    print(f"Target URL: {audit_result.get('url')}")
    print(f"Overall Script Performance Score: {audit_result.get('overall_score')}/100 (Grade: {audit_result.get('grade')})")

    inp = audit_result.get("inp_estimate", {})
    print(f"Estimated INP: {inp.get('estimated_inp_ms')}ms ({inp.get('status')})")
    print(f"Total Blocking Time: {audit_result.get('stats', {}).get('total_blocking_time_ms')}ms")
    print(f"Total Scripts: {audit_result.get('stats', {}).get('total_scripts')}")

    print("\n--- Recommendations ---")
    for r in audit_result.get("recommendations", []):
        print(f"  - {r}")
    print()


def export_markdown_report(audit_result: Dict[str, Any]) -> str:
    """Generate Markdown audit report string."""
    lines = []
    lines.append("# PayloadSniper: INP, Long Tasks & Script Bloat-Tracer Audit\n")
    lines.append(f"**Target URL**: {audit_result.get('url')}\n")
    lines.append(f"**Overall Script Performance Score**: {audit_result.get('overall_score')}/100 (Grade: {audit_result.get('grade')})\n")

    stats = audit_result.get("stats", {})
    inp = audit_result.get("inp_estimate", {})

    lines.append(f"- Estimated INP Latency: {inp.get('estimated_inp_ms')}ms ({inp.get('status')})")
    lines.append(f"- Total Blocking Time (TBT): {stats.get('total_blocking_time_ms')}ms")
    lines.append(f"- Total Discovered Scripts: {stats.get('total_scripts')}")
    lines.append(f"- Third-Party Marketing Tags: {stats.get('third_party_scripts')}")
    lines.append(f"- Render-Blocking Head Scripts: {stats.get('render_blocking_scripts')}\n")

    # Component Scores
    lines.append("---\n")
    lines.append("## Component Breakdown\n")
    lines.append("| Component | Weight | Score |")
    lines.append("|:---|:---:|:---:|")
    comp = audit_result.get("component_scores", {})
    for name, weight, key in [
        ("Total Blocking Time (TBT)", "35%", "total_blocking_time"),
        ("Estimated INP Readiness", "25%", "estimated_inp_readiness"),
        ("Third-Party Script Overhead", "20%", "third_party_overhead"),
        ("Script Loading Hygiene", "10%", "script_loading_hygiene"),
        ("Bundle & Tag Efficiency", "10%", "bundle_efficiency"),
    ]:
        lines.append(f"| {name} | {weight} | {comp.get(key, 0)}/100 |")

    # Vendor Breakdown
    vendors = audit_result.get("vendor_breakdown", [])
    if vendors:
        lines.append("\n---\n")
        lines.append("## Script Vendors & Third-Party Tags\n")
        lines.append("| Vendor | Category | Origin | Script Count | Render Blocking |")
        lines.append("|:---|:---|:---:|:---:|:---:|")
        for v in vendors:
            origin = "Third-Party" if v.get("is_third_party") else "First-Party"
            lines.append(f"| {v.get('vendor')} | {v.get('category')} | {origin} | {v.get('script_count')} | {v.get('blocking_scripts')} |")

    # Recommendations
    lines.append("\n---\n")
    lines.append("## INP & Core Web Vitals Remediation Steps\n")
    for i, r in enumerate(audit_result.get("recommendations", []), 1):
        lines.append(f"{i}. {r}")

    lines.append("\n---\n")
    lines.append("*Generated by [PayloadSniper](https://github.com/xcalibur73/payload-sniper) | [WebAudits.pro](https://webaudits.pro/tools/payload-sniper)*\n")

    return "\n".join(lines)


def export_json_report(audit_result: Dict[str, Any]) -> dict:
    """Build JSON-serializable audit report dict."""
    return {
        "tool": "PayloadSniper",
        "version": "1.0.0",
        **audit_result,
    }
