"""
PayloadSniper CLI: INP, Long Tasks & Script Bloat-Tracer.
"""

import argparse
import json
import sys

from payload_sniper.profiler import profile_page
from payload_sniper.scorer import audit_profile_results
from payload_sniper.report_generator import (
    print_terminal_report,
    export_markdown_report,
    export_json_report,
)


def run_audit(url: str, fast: bool = False, simulate_mobile: bool = False) -> dict:
    """Execute complete script profiling pipeline on a URL."""
    profile_data = profile_page(url, force_http=fast, simulate_mobile=simulate_mobile)
    audit = audit_profile_results(profile_data)
    return audit


def main():
    parser = argparse.ArgumentParser(
        description="PayloadSniper: Edge-Cached Code Split, INP & Core Web Vitals Bloat-Tracer",
        epilog="Example: python run.py https://webaudits.pro",
    )
    parser.add_argument(
        "url",
        help="Target URL to profile for JavaScript hydration, Long Tasks, and INP bottlenecks.",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast static script inspection mode (skips Chromium headless browser).",
    )
    parser.add_argument(
        "--simulate-mobile",
        action="store_true",
        help="Simulate mid-tier mobile device with 4x CPU throttling.",
    )
    parser.add_argument(
        "--output",
        choices=["terminal", "markdown", "json"],
        default="terminal",
        help="Output format (default: terminal).",
    )
    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="Save report to file path.",
    )

    args = parser.parse_args()

    target_url = args.url.strip()
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = "https://" + target_url

    print(f"PayloadSniper: Profiling JavaScript execution and INP on {target_url}...")

    try:
        audit_result = run_audit(target_url, fast=args.fast, simulate_mobile=args.simulate_mobile)
    except Exception as e:
        print(f"[ERROR] Audit failed: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output == "terminal":
        print_terminal_report(audit_result)

    elif args.output == "markdown":
        md = export_markdown_report(audit_result)
        if args.save:
            with open(args.save, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"Markdown report saved to: {args.save}")
        else:
            print(md)

    elif args.output == "json":
        data = export_json_report(audit_result)
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        if args.save:
            with open(args.save, "w", encoding="utf-8") as f:
                f.write(json_str)
            print(f"JSON report saved to: {args.save}")
        else:
            print(json_str)


if __name__ == "__main__":
    main()
