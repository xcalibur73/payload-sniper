# PayloadSniper

Edge-Cached Code Split, INP & Core Web Vitals Bloat-Tracer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Status: Production](https://img.shields.io/badge/status-production-success.svg)](#)
[![Cloud Engine: WebAudits.pro](https://img.shields.io/badge/cloud-webaudits.pro-orange.svg)](https://webaudits.pro/tools/payload-sniper)

PayloadSniper is a command-line utility and headless Chromium diagnostic engine that profiles JavaScript hydration overhead, main-thread blocking tasks, and third-party script execution costs. It isolates the exact code chunks responsible for degrading Total Blocking Time (TBT) and Google's Interaction to Next Paint (INP) Core Web Vital.

Key capabilities:
- Main-thread Long Tasks profiling via Chrome DevTools Protocol (CDP) Performance timeline. Captures every execution task exceeding 50ms.
- Third-party script attribution: maps blocking durations to known marketing and analytics vendors (Google Tag Manager, Meta Pixel, Hotjar, Klaviyo, HubSpot, TikTok Pixel, Intercom).
- First-party vs third-party execution split: computes the percentage of Total Blocking Time driven by marketing scripts vs application code.
- Unused code estimation: identifies bundle weight vs active execution overhead.
- INP vulnerability rating: translates synthetic Long Tasks and Total Blocking Time into an empirical INP risk classification (Good < 200ms, Needs Improvement 200-500ms, Poor > 500ms).
- Automated script deferral recipes: generates prioritized code modifications (web worker offloading, dynamic imports, async/defer hints).
- Multi-format reporting: high-contrast terminal tables, Markdown audit reports, and JSON pipelines.

---

## The Engineering Problem

Interaction to Next Paint (INP) replaced First Input Delay (FID) as an official Google Core Web Vital in March 2024. Unlike FID, which measured only the initial interaction delay, INP evaluates the longest interaction latency across the entire user session.

Common frontend architectures face severe INP degradation due to:
1. Hydration Monoliths: Single Page Applications (Next.js, Nuxt, Remix) execute multi-megabyte JavaScript bundles during initial render, locking the main thread for 400ms to 1,500ms while hydrating the DOM.
2. Third-Party Script Congestion: Tag managers inject marketing pixels, session recorders, and chat widgets. A single unoptimized tracking script can spawn multiple 150ms+ Long Tasks, dropping user input events.
3. Synchronous Event Handlers: Heavy computational tasks bound to `click`, `scroll`, or `input` events prevent the browser from scheduling the next frame, causing visual input lag.
4. Render-Blocking Script Tags: Legacy `<script src="...">` tags without `defer` or `async` stall DOM construction and prolong First Contentful Paint.

---

## Installation

```bash
git clone https://github.com/xcalibur73/payload-sniper.git
cd payload-sniper
pip install -r requirements.txt
```

### System Requirements
- Python 3.10 or higher.
- Optional: Google Chrome, Chromium, or Microsoft Edge for headless CDP profiling. When no browser binary is detected, PayloadSniper automatically uses static HTTP inspection mode.

---

## Usage

### Profile a Live URL via Headless Chromium
```bash
python run.py https://webaudits.pro
```

### Simulate Mobile CPU Throttling
```bash
python run.py https://example.com --simulate-mobile
```

### Fast Static Script Analysis Mode
```bash
python run.py https://example.com --fast
```

### Export Markdown Audit Report
```bash
python run.py https://example.com --output markdown --save PAYLOAD-AUDIT.md
```

### Export Machine-Readable JSON for CI/CD Pipelines
```bash
python run.py https://example.com --output json --save audit.json
```

---

## Web Platform Integration (WebAudits.pro)

To run hosted audits without installing local Python or Chromium binaries:
- Interactive web tool: [WebAudits.pro/tools/payload-sniper](https://webaudits.pro/tools/payload-sniper)
- Automated long tasks profiling and script attribution.

---

## Scoring Model

PayloadSniper calculates an overall Script Performance Score (0-100) and letter grade:

| Component | Weight | Measurement Criteria |
|:---|:---:|:---|
| Total Blocking Time (TBT) | 35% | Cumulative main-thread blocking time (> 50ms per task) |
| Estimated INP Readiness | 25% | Maximum continuous blocking task and input response latency |
| Third-Party Script Overhead | 20% | Ratio of main-thread blocking attributed to third-party tags |
| Script Loading Hygiene | 10% | Presence of `async`, `defer`, or `type="module"` on external scripts |
| Bundle Weight Efficiency | 10% | Total raw JavaScript transfer size (< 350KB target) |

### Grade Scale
- **A**: Score >= 90 (TBT < 150ms, estimated INP < 100ms)
- **B**: Score >= 75 (TBT < 300ms, minor script congestion)
- **C**: Score >= 60 (TBT < 600ms, noticeable input lag)
- **D**: Score >= 40 (TBT < 1,000ms, heavy marketing script bloat)
- **F**: Score < 40 (TBT > 1,000ms, frozen main thread)

---

## Running Unit Tests

```bash
python -m unittest discover tests/
```

---

## Author

Maintained by [@xcalibur73](https://github.com/xcalibur73), creator of [WebAudits.pro](https://webaudits.pro).

Part of a technical SEO engineering tooling suite:
1. [payload-sniper](https://github.com/xcalibur73/payload-sniper): Edge-cached code split, INP and Core Web Vitals bloat-tracer.
2. [img-spec](https://github.com/xcalibur73/img-spec): Responsive viewport breakpoint and LCP image auditor.
3. [schema-graph](https://github.com/xcalibur73/schema-graph): Cross-page entity and knowledge graph integrity tracer.
4. [dom-hydrate](https://github.com/xcalibur73/dom-hydrate): Headless Chromium SSR vs CSR DOM diff engine.
5. [citation-pulse](https://github.com/xcalibur73/citation-pulse): GEO and AI search citability benchmark engine.
6. [index-trace](https://github.com/xcalibur73/index-trace): Search Console emergency triage and crawler collision tracer.
7. [overflow-trace](https://github.com/xcalibur73/overflow-trace): Mobile viewport horizontal overflow tracer.

---

## License

Licensed under the [MIT License](LICENSE).
