"""
JavaScript performance profiler and Long Tasks collector for PayloadSniper.
"""

import asyncio
import json
import urllib.parse
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup

from payload_sniper.browser import ChromeRunner, CDPClient, find_browser_executable
from payload_sniper.script_analyzer import classify_script_vendor

LONG_TASK_INIT_SCRIPT = """
window.__payloadSniperLongTasks = [];
try {
    const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
            window.__payloadSniperLongTasks.push({
                name: entry.name,
                startTime: Math.round(entry.startTime),
                duration: Math.round(entry.duration),
                blockingTime: Math.max(0, Math.round(entry.duration - 50)),
                attribution: entry.attribution && entry.attribution.length > 0 ? {
                    name: entry.attribution[0].name || '',
                    entryType: entry.attribution[0].entryType || '',
                    containerType: entry.attribution[0].containerType || '',
                    containerSrc: entry.attribution[0].containerSrc || '',
                    containerId: entry.attribution[0].containerId || '',
                    containerName: entry.attribution[0].containerName || ''
                } : null
            });
        }
    });
    observer.observe({ type: 'longtask', buffered: true });
} catch (e) {
    // longtask not supported or blocked
}
"""

DOM_SCRIPTS_SCRIPT = """
(() => {
    const scripts = [];
    document.querySelectorAll('script').forEach((el, index) => {
        const src = el.src || el.getAttribute('src') || '';
        const isAsync = el.async;
        const isDefer = el.defer;
        const type = el.type || 'text/javascript';
        const isModule = type === 'module';
        const isInline = !src;
        const inlineLength = isInline ? (el.textContent || '').length : 0;

        scripts.push({
            index: index + 1,
            src: src,
            is_inline: isInline,
            is_async: isAsync,
            is_defer: isDefer,
            is_module: isModule,
            type: type,
            inline_char_length: inlineLength
        });
    });
    return scripts;
})()
"""


def inspect_via_http(url: str, timeout: int = 15) -> Dict[str, Any]:
    """Fallback static inspection mode when Chromium is not present."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    html = resp.text

    parsed_url = urllib.parse.urlparse(url)
    page_domain = parsed_url.netloc

    soup = BeautifulSoup(html, "html.parser")
    script_tags = soup.find_all("script")

    scripts = []
    third_party_count = 0
    blocking_script_count = 0

    for idx, el in enumerate(script_tags, 1):
        src = el.get("src", "")
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = urllib.parse.urljoin(url, src)

        is_async = el.has_attr("async")
        is_defer = el.has_attr("defer")
        script_type = el.get("type", "text/javascript")
        is_module = script_type == "module"
        is_inline = not bool(src)

        classification = classify_script_vendor(src, page_domain)
        if classification["is_third_party"]:
            third_party_count += 1

        # Non-async, non-defer external script is render-blocking
        is_render_blocking = not is_inline and not is_async and not is_defer and not is_module
        if is_render_blocking:
            blocking_script_count += 1

        scripts.append({
            "index": idx,
            "src": src,
            "is_inline": is_inline,
            "is_async": is_async,
            "is_defer": is_defer,
            "is_module": is_module,
            "type": script_type,
            "is_render_blocking": is_render_blocking,
            "vendor": classification["vendor"],
            "category": classification["category"],
            "is_third_party": classification["is_third_party"],
            "domain": classification["domain"],
        })

    return {
        "mode": "http_static",
        "url": url,
        "page_domain": page_domain,
        "total_scripts": len(scripts),
        "third_party_scripts": third_party_count,
        "render_blocking_scripts": blocking_script_count,
        "scripts": scripts,
        "long_tasks": [],
        "total_blocking_time_ms": 0,
        "max_long_task_ms": 0,
    }


async def _profile_url_cdp(
    ws_url: str,
    url: str,
    simulate_mobile: bool = False,
    wait_time: float = 4.0,
) -> Dict[str, Any]:
    """Profile URL via CDP and extract Long Tasks, script definitions, and Performance metrics."""
    client = CDPClient(ws_url)
    await client.connect()

    parsed_url = urllib.parse.urlparse(url)
    page_domain = parsed_url.netloc

    try:
        # Enable domains
        await client.send("Page.enable")
        await client.send("DOM.enable")
        await client.send("Performance.enable")
        await client.send("Network.enable")

        # Inject Long Tasks observer before page scripts execute
        await client.send("Page.addScriptToEvaluateOnNewDocument", {
            "source": LONG_TASK_INIT_SCRIPT,
        })

        # CPU Throttling (simulate mid-tier mobile processor if requested)
        if simulate_mobile:
            await client.send("Emulation.setCPUThrottlingRate", {"rate": 4})
            await client.send("Emulation.setDeviceMetricsOverride", {
                "width": 375,
                "height": 667,
                "deviceScaleFactor": 2.0,
                "mobile": True,
            })

        # Navigate
        await client.send("Page.navigate", {"url": url})

        # Wait for page load and hydration tasks
        await asyncio.sleep(wait_time)

        # Retrieve Long Tasks collected
        long_tasks_res = await client.send("Runtime.evaluate", {
            "expression": "window.__payloadSniperLongTasks || []",
            "returnByValue": True,
        })
        raw_long_tasks = long_tasks_res.get("result", {}).get("value", [])

        # Retrieve DOM scripts
        scripts_res = await client.send("Runtime.evaluate", {
            "expression": DOM_SCRIPTS_SCRIPT,
            "returnByValue": True,
        })
        raw_scripts = scripts_res.get("result", {}).get("value", [])

        # Retrieve Performance Metrics
        perf_metrics_res = await client.send("Performance.getMetrics")
        metrics_dict = {
            m["name"]: m["value"]
            for m in perf_metrics_res.get("metrics", [])
        }

        # Process scripts with vendor classifications
        scripts = []
        third_party_count = 0
        blocking_script_count = 0

        for s in raw_scripts:
            classification = classify_script_vendor(s.get("src", ""), page_domain)
            is_tp = classification["is_third_party"]
            if is_tp:
                third_party_count += 1

            is_blocking = not s["is_inline"] and not s["is_async"] and not s["is_defer"] and not s["is_module"]
            if is_blocking:
                blocking_script_count += 1

            scripts.append({
                **s,
                "is_render_blocking": is_blocking,
                "vendor": classification["vendor"],
                "category": classification["category"],
                "is_third_party": is_tp,
                "domain": classification["domain"],
            })

        # Process Long Tasks & compute Total Blocking Time (TBT)
        long_tasks = []
        total_tbt = 0
        max_duration = 0

        for lt in raw_long_tasks:
            duration = lt.get("duration", 0)
            blocking = max(0, duration - 50)
            total_tbt += blocking
            if duration > max_duration:
                max_duration = duration

            container_src = lt.get("attribution", {}).get("containerSrc", "") if lt.get("attribution") else ""
            attribution_info = classify_script_vendor(container_src, page_domain) if container_src else None

            long_tasks.append({
                "duration": duration,
                "blocking_time": blocking,
                "start_time": lt.get("startTime", 0),
                "initiating_source": container_src or "Page Hydration / Event Loop",
                "vendor": attribution_info["vendor"] if attribution_info else "Application Main Thread",
                "is_third_party": attribution_info["is_third_party"] if attribution_info else False,
            })

        return {
            "mode": "cdp_longtask_profiling",
            "url": url,
            "page_domain": page_domain,
            "total_scripts": len(scripts),
            "third_party_scripts": third_party_count,
            "render_blocking_scripts": blocking_script_count,
            "scripts": scripts,
            "long_tasks": long_tasks,
            "total_blocking_time_ms": total_tbt,
            "max_long_task_ms": max_duration,
            "task_duration_total_s": round(metrics_dict.get("TaskDuration", 0), 2),
            "js_heap_used_mb": round(metrics_dict.get("JSHeapUsedSize", 0) / (1024 * 1024), 2),
        }

    finally:
        await client.close()


def profile_page(url: str, force_http: bool = False, simulate_mobile: bool = False) -> Dict[str, Any]:
    """Profile page scripts and long tasks. Uses headless Chromium when available."""
    has_browser = bool(find_browser_executable())

    if force_http or not has_browser:
        return inspect_via_http(url)

    runner = ChromeRunner()
    runner.start()

    try:
        ws_url = runner.get_tab_ws_url()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                _profile_url_cdp(ws_url, url, simulate_mobile=simulate_mobile)
            )
        finally:
            loop.close()
    except Exception as e:
        print(f"[WARN] Chromium profiling failed ({e}), falling back to static inspection.")
        return inspect_via_http(url)
    finally:
        runner.stop()
