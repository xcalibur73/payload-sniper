# PayloadSniper

Interaction to Next Paint (INP), Long Tasks, and script bloat tracer.

Part of the [WebAudits.pro](https://webaudits.pro) technical intelligence platform.

---

## What it does

PayloadSniper profiles client-side JavaScript execution overhead, main-thread blocking bottlenecks, and third-party script congestion. It analyzes:
- Main-thread Long Tasks exceeding the 50ms threshold defined in the W3C Long Tasks API.
- Total Blocking Time (TBT) accumulation and its correlation to Interaction to Next Paint (INP).
- Third-party script attribution (identifying specific tag managers, ad pixels, analytics libraries, and chat widgets).
- Render-blocking script hygiene (`async`, `defer`, `type="module"`).
- Synthetic mobile performance through optional 4x CPU throttling via Chrome DevTools Protocol (CDP).

---

## Why it exists

Interaction to Next Paint (INP) replaced First Input Delay (FID) as an official Core Web Vitals metric. Sites frequently pass static Lighthouse audits yet fail real-world INP thresholds (200ms) because:
- Third-party marketing and analytics bundles execute heavy parsing, compilation, and hydration on the main thread during initial user interactions.
- Hydration scripts schedule consecutive unyielding execution blocks that delay keyboard and tap input dispatching.

PayloadSniper isolates the exact script origins responsible for main-thread congestion and provides concrete code-splitting and deferral recommendations.

---

## Key features

- **CDP Performance Timeline Tracing:** Intercepts low-level Chrome DevTools Protocol performance events to record task duration, start times, and execution chains.
- **Vendor Attribution Engine:** Classifies script origins against known first-party and third-party signatures (Google Tag Manager, Meta Pixel, Hotjar, Klaviyo, Intercom, Cloudflare).
- **Mobile Hardware Simulation:** Emulates mid-tier mobile hardware performance using CDP 4x CPU throttling.
- **Fast Static Inspection Mode:** Provides an optional lightweight HTTP analysis mode for rapid script inventory without headless browser overhead.
- **Developer Remediation Roadmap:** Outputs prioritized engineering actions to eliminate Long Tasks and optimize script delivery.

---

## Architecture

```text
[Input Target URL]
        |
        +---> [Chromium CDP Runner] (Optional: 4x CPU Throttle)
        |           |
        |           +---> Performance Timeline Tracing
        |           +---> Long Tasks Capture (> 50ms)
        |           +---> Script Execution Attribution
        |
        +---> [Static Parser Fallback]
                    |
                    v
         [Vendor Attribution Engine]
                    |
                    v
       [Performance Scoring Model]
                    |
                    +---> Terminal Report (Rich Table)
                    +---> Markdown Document / JSON Pipeline Output
```

PayloadSniper executes three modules:
1. `profiler.py`: Manages CDP timeline tracing, records Performance API metrics (`PerformanceLongTaskTiming`), captures script URLs, and computes blocking time.
2. `scorer.py`: Aggregates metrics into five weighted performance dimensions: Total Blocking Time, Estimated INP Readiness, Third-Party Overhead, Script Loading Hygiene, and Bundle Efficiency.
3. `report_generator.py`: Generates formatted terminal reports with encoding-safe tables, Markdown summaries, and JSON objects for automated performance monitoring.

---

## Installation

### Prerequisites
- Python 3.10 or higher
- Google Chrome or Chromium installed and available in system PATH

### Install from Source
```bash
git clone https://github.com/xcalibur73/payload-sniper.git
cd payload-sniper
pip install -r requirements.txt
pip install -e .
```

---

## Usage

### Basic CLI Invocation
```bash
# Audit a target URL in standard headless browser mode
payload-sniper https://webaudits.pro

# Simulate mid-tier mobile hardware with 4x CPU throttling
payload-sniper https://example.com --simulate-mobile

# Fast static inspection mode (skips headless browser)
payload-sniper https://example.com --fast

# Export JSON report for CI/CD performance gates
payload-sniper https://example.com --output json --save inp-report.json

# Check installed version
payload-sniper --version
```

---

## Example output

```text
+-------------------------------------------------------------------------------+
| PayloadSniper: INP, Long Tasks & Script Bloat-Tracer                          |
| Target URL: https://webaudits.pro                                             |
| Script Performance Score: 96.0/100 (Grade: A)                                 |
| Mode: cdp_headless | Total Scripts: 8 | Third-Party: 0 | TBT: 0ms | INP: 42ms |
+-------------------------------------------------------------------------------+

Component Score Breakdown:
+-----------------------------------+--------+------------+
| Component Dimension               | Weight | Score      |
+-----------------------------------+--------+------------+
| Total Blocking Time (TBT)         | 35%    | 100.0/100  |
| Estimated INP Readiness           | 25%    | 95.0/100   |
| Third-Party Script Overhead       | 20%    | 100.0/100  |
| Script Loading Hygiene            | 10%    | 90.0/100   |
| Bundle & Tag Efficiency           | 10%    | 95.0/100   |
+-----------------------------------+--------+------------+

Interaction to Next Paint (INP) Vulnerability Assessment:
- Estimated Interaction Latency: 42ms (Status: EXCELLENT)
- Google 200ms Target Passed: True
- Max Long Task: 0ms | Total Long Tasks: 0
```

---

## Benchmark / methodology

### 12-Site Third-Party Script Cost Study
- **Dataset:** 12 production sites across media, e-commerce, SaaS, and editorial publishing (`webaudits.pro`, `theverge.com`, `shopify.com`, `stripe.com`, `linear.app`, etc.).
- **Command Used:** `python run.py <url> --simulate-mobile --output json`
- **Tool Version:** PayloadSniper v1.0.0
- **Environment:** Windows 11, Chromium 128.0, 4x CPU throttling, Python 3.12, 1 Gbps fiber connection.
- **Raw Telemetry & Calculation:**
  - Blocking duration per task: `duration - 50ms` (standard TBT definition).
  - Third-party TBT ratio: `(third_party_blocking_ms / total_blocking_ms) * 100`.
- **Results:**
  - Third-party tracking tags accounted for 71.4% of total blocking time on surveyed publishing properties.
  - Complete study dataset: [BENCHMARKS.md](BENCHMARKS.md).

---

## Limitations

- **Synthetic Projection:** The Estimated INP latency is an experimental synthetic heuristic derived from lab Total Blocking Time and Long Task distribution. It is not a measurement of real user field interactions (RUM).
- **Simulated Hardware:** 4x CPU throttling models mid-tier devices (e.g. Moto G4) but does not account for variable mobile thermal throttling, RAM constraints, or GPU rendering pipelines.
- **Interaction Emulation:** Profiles load-phase and initial idle execution. Does not simulate complex drag-and-drop or canvas interactions unless orchestrated via automated test scripts.

---

## Accuracy / standards

PayloadSniper evaluates scripts against official W3C specifications and project heuristics:

| Metric / Analysis | Classification | Authority / Standard |
|:---|:---|:---|
| Long Tasks Detection (>50ms) | Web Standard | W3C Long Tasks API Level 1 |
| Total Blocking Time (TBT) | Google / Web Standard | Google Web Vitals Specification |
| Google INP 200ms Threshold | Google / Web Standard | Chrome Core Web Vitals Criteria |
| Vendor Domain Attribution | Project-Derived Heuristic | Curated registry of 50+ script origins |
| Synthetic INP Projection | Experimental Metric | Lab heuristic modeling worst-case latency |

---

## Testing

PayloadSniper includes unit tests covering Long Task attribution, TBT calculation, vendor matching, and scoring models:

```bash
# Run unit test suite
python -m unittest discover -s tests

# Test execution output
# Ran 9 tests in 0.000s
# OK
```

Continuous integration runs automatically across Linux and Windows runners via GitHub Actions.

---

## Roadmap

- [x] Initial release with CDP timeline tracing and 4x CPU throttling.
- [x] PEP 621 packaging, CLI `--version`, and Windows cp1252 encoding hardening.
- [ ] Automated interaction simulation (button clicking, dropdown opening) during trace.
- [ ] Source map resolution to attribute Long Tasks to specific source files and line numbers.
- [ ] WebAudits.pro continuous performance regression monitoring.

---

## License

MIT License. See [LICENSE](LICENSE) for full details.
