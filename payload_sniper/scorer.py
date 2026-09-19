"""
Scoring and INP vulnerability estimation engine for PayloadSniper.
"""

from typing import Dict, Any, List


def calculate_tbt_score(tbt_ms: int) -> float:
    """Calculate Total Blocking Time score (0-100) based on Google Lighthouse curve."""
    if tbt_ms <= 100:
        return 100.0
    elif tbt_ms <= 200:
        return round(100.0 - ((tbt_ms - 100) * 0.15), 1)
    elif tbt_ms <= 400:
        return round(85.0 - ((tbt_ms - 200) * 0.125), 1)
    elif tbt_ms <= 800:
        return round(60.0 - ((tbt_ms - 400) * 0.075), 1)
    elif tbt_ms <= 1400:
        return round(30.0 - ((tbt_ms - 800) * 0.033), 1)
    else:
        return max(0.0, round(10.0 - ((tbt_ms - 1400) * 0.01), 1))


def estimate_inp_risk(max_task_ms: int, tbt_ms: int) -> Dict[str, Any]:
    """Estimate Interaction to Next Paint (INP) vulnerability from Long Tasks."""
    # INP is typically driven by max main-thread blocking task + event handler dispatch
    estimated_inp_ms = max(50, int(max_task_ms * 0.85) + int(tbt_ms * 0.15))

    if estimated_inp_ms <= 150:
        status = "Good (Low INP Risk)"
        score = 100.0
    elif estimated_inp_ms <= 250:
        status = "Good (Borderline 200ms Target)"
        score = 85.0
    elif estimated_inp_ms <= 450:
        status = "Needs Improvement (Noticeable Input Lag)"
        score = 55.0
    else:
        status = "Poor (Severe Interaction Delay)"
        score = 25.0

    return {
        "estimated_inp_ms": estimated_inp_ms,
        "status": status,
        "inp_score": score,
        "meets_google_target": estimated_inp_ms <= 200,
    }


def audit_profile_results(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate composite Script Performance Score and synthesize remediation recommendations."""
    tbt_ms = profile_data.get("total_blocking_time_ms", 0)
    max_task_ms = profile_data.get("max_long_task_ms", 0)
    total_scripts = max(1, profile_data.get("total_scripts", 0))
    tp_scripts = profile_data.get("third_party_scripts", 0)
    blocking_scripts = profile_data.get("render_blocking_scripts", 0)
    long_tasks = profile_data.get("long_tasks", [])

    # 1. TBT Score (35%)
    tbt_score = calculate_tbt_score(tbt_ms)

    # 2. INP Risk Score (25%)
    inp_info = estimate_inp_risk(max_task_ms, tbt_ms)
    inp_score = inp_info["inp_score"]

    # 3. Third-Party Script Overhead (20%)
    # Compute third-party blocking ratio
    tp_blocking_ms = sum(lt["blocking_time"] for lt in long_tasks if lt.get("is_third_party"))
    if tbt_ms > 0:
        tp_blocking_ratio = tp_blocking_ms / tbt_ms
        tp_score = max(0.0, round(100.0 - (tp_blocking_ratio * 100.0), 1))
    else:
        # Static mode fallback: ratio of third-party scripts to total
        tp_ratio = tp_scripts / total_scripts
        tp_score = max(20.0, round(100.0 - (tp_ratio * 70.0), 1))

    # 4. Script Loading Hygiene (10%): render-blocking ratio
    hygiene_score = max(0.0, round(100.0 - ((blocking_scripts / total_scripts) * 100.0), 1))

    # 5. Bundle Weight / Count Efficiency (10%)
    if total_scripts <= 8:
        weight_score = 100.0
    elif total_scripts <= 20:
        weight_score = 80.0
    elif total_scripts <= 35:
        weight_score = 60.0
    else:
        weight_score = 35.0

    overall = round(
        (tbt_score * 0.35)
        + (inp_score * 0.25)
        + (tp_score * 0.20)
        + (hygiene_score * 0.10)
        + (weight_score * 0.10),
        1
    )

    grade = (
        "A" if overall >= 90.0
        else "B" if overall >= 75.0
        else "C" if overall >= 60.0
        else "D" if overall >= 40.0
        else "F"
    )

    # Vendor aggregation
    vendor_stats: Dict[str, Dict[str, Any]] = {}
    for s in profile_data.get("scripts", []):
        v = s.get("vendor", "Unknown")
        if v not in vendor_stats:
            vendor_stats[v] = {
                "vendor": v,
                "category": s.get("category", "General"),
                "is_third_party": s.get("is_third_party", False),
                "script_count": 0,
                "blocking_scripts": 0,
            }
        vendor_stats[v]["script_count"] += 1
        if s.get("is_render_blocking"):
            vendor_stats[v]["blocking_scripts"] += 1

    # Actionable Recommendations
    recommendations = []

    if blocking_scripts > 0:
        recommendations.append(f"Add 'defer' or 'async' to {blocking_scripts} render-blocking <script> tag(s) in HTML head to unblock First Contentful Paint.")

    if tbt_ms > 200:
        recommendations.append(f"Total Blocking Time ({tbt_ms}ms) exceeds Google's 200ms Core Web Vitals threshold. Break up long tasks (>50ms) using requestIdleCallback() or scheduler.yield().")

    if not inp_info["meets_google_target"]:
        recommendations.append(f"Estimated INP latency ({inp_info['estimated_inp_ms']}ms) fails Google's 200ms target. Largest single execution block was {max_task_ms}ms.")

    if tp_blocking_ms > 100:
        recommendations.append(f"Third-party tracking scripts consume {tp_blocking_ms}ms of main-thread execution. Offload non-critical analytics (GTM, Meta, Hotjar) via Partytown web workers.")

    if tp_scripts >= 8:
        recommendations.append(f"Consolidate {tp_scripts} external third-party marketing tags to reduce DNS handshakes and asynchronous event loop congestion.")

    if not recommendations:
        recommendations.append("Main-thread execution is optimal with negligible Total Blocking Time and healthy INP headroom.")

    return {
        "url": profile_data.get("url"),
        "mode": profile_data.get("mode"),
        "overall_score": overall,
        "grade": grade,
        "component_scores": {
            "total_blocking_time": tbt_score,
            "estimated_inp_readiness": inp_score,
            "third_party_overhead": tp_score,
            "script_loading_hygiene": hygiene_score,
            "bundle_efficiency": weight_score,
        },
        "inp_estimate": inp_info,
        "stats": {
            "total_scripts": total_scripts,
            "third_party_scripts": tp_scripts,
            "render_blocking_scripts": blocking_scripts,
            "total_blocking_time_ms": tbt_ms,
            "max_long_task_ms": max_task_ms,
            "long_tasks_count": len(long_tasks),
            "third_party_blocking_time_ms": tp_blocking_ms,
            "js_heap_used_mb": profile_data.get("js_heap_used_mb", 0.0),
        },
        "vendor_breakdown": list(vendor_stats.values()),
        "long_tasks": long_tasks[:10],
        "recommendations": recommendations[:5],
    }
