# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.3.1] - 2026-09-21

### Added
- Added stealth Chromium CDP flags (--disable-blink-features=AutomationControlled and isolated origin bypassing) to headless browser launch configurations to evade WAFs and bot challenges.

## [1.3.0] - 2026-09-20
 
### Added
- Google Core Web Vitals 3-tier rating (`good`, `needs_improvement`, `poor`) based on official web.dev INP thresholds (200ms and 500ms cutoffs).
- Tailored remediation playbooks per interaction bottleneck (startup long-task yielding, scheduler.yield deferral, and layout thrashing prevention) integrated into terminal and markdown reports.

## [1.2.0] - 2026-09-20

### Added
- 3-Phase INP sub-part attribution decomposition inspired by Google Chrome `web-vitals`:
  - Algorithmic latency splitting into Input Delay, Processing Duration, and Presentation Delay.
  - Automated primary interaction bottleneck diagnosis (Main Thread Congestion, Long JavaScript Callbacks, or Layout/Rendering Overhead).
  - Terminal, Markdown, and JSON reporting of sub-part timing breakdown.

## [1.1.0] - 2026-09-19

### Added
- W3C Resource Timing API integration capturing wire transfer bytes, compressed sizes, and uncompressed memory footprint (`decodedBodySize`).
- Top 5 Heaviest JavaScript Files ranking table displaying script byte bloat across terminal, Markdown, and JSON outputs.
- Automated payload budget check warning when uncompressed JavaScript exceeds 1.0 MB.
- Dedicated unit test `test_payload_size_metrics` covering transfer and decoded byte extraction.

## [1.0.0] - 2026-09-19

### Added
- Initial release of payload-sniper: Interaction to Next Paint (INP), Long Tasks, and script bloat tracer.
- CLI entry point with `--output` (terminal, markdown, json) and `--version` flags.
- Standard PEP 621 packaging via `pyproject.toml`.
- GitHub Actions CI matrix workflow for Python 3.10, 3.11, and 3.12.
- Comprehensive automated unit test suite.
- Integration endpoints for the WebAudits.pro technical audit platform.

### Hardened
- Cross-platform Windows terminal encoding safety (`_safe_str` Unicode sanitization).
- Universal test discovery path resilience.
