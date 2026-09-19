"""
Script catalog, third-party vendor detection, and origin classifier for PayloadSniper.
"""

from typing import Dict, Any, Optional, Tuple
import urllib.parse


THIRD_PARTY_PATTERNS = [
    ("Google Tag Manager", "Tag Management", ["googletagmanager.com/gtm.js", "gtm.js?"]),
    ("Google Analytics (GA4)", "Analytics", ["google-analytics.com/analytics.js", "googletagmanager.com/gtag/js"]),
    ("Meta Pixel (Facebook)", "Advertising", ["connect.facebook.net", "fbevents.js"]),
    ("Hotjar", "Session Recording", ["static.hotjar.com", "script.hotjar.com"]),
    ("Klaviyo", "Marketing Automation", ["static.klaviyo.com", "klaviyo.js"]),
    ("HubSpot", "Marketing Automation", ["js.hs-scripts.com", "js.hsforms.net", "js.hs-analytics.net"]),
    ("TikTok Pixel", "Advertising", ["analytics.tiktok.com"]),
    ("Intercom", "Customer Support", ["widget.intercom.io"]),
    ("Sentry", "Error Monitoring", ["browser.sentry-cdn.com"]),
    ("Stripe", "Payment Gateway", ["js.stripe.com"]),
    ("Cloudflare Insights", "Analytics", ["cloudflareinsights.com", "beacon.min.js"]),
    ("Segment", "Data Platform", ["cdn.segment.com/analytics.js"]),
    ("Microsoft Clarity", "Session Recording", ["www.clarity.ms"]),
    ("Datadog RUM", "Monitoring", ["datadoghq-browser-agent.com"]),
    ("Criteo", "Advertising", ["dynamic.criteo.com"]),
    ("Twitter / X Pixel", "Advertising", ["static.ads-twitter.com"]),
    ("LinkedIn Insight", "Advertising", ["snap.licdn.com"]),
]


def classify_script_vendor(script_url: str, page_domain: str) -> Dict[str, Any]:
    """Classify a script URL by vendor, category, and first-party vs third-party status."""
    if not script_url:
        return {
            "vendor": "Inline Script",
            "category": "Application Code",
            "is_third_party": False,
            "domain": page_domain,
        }

    try:
        parsed = urllib.parse.urlparse(script_url)
        host = parsed.netloc.lower()
    except Exception:
        host = ""

    # Check third party patterns
    lower_url = script_url.lower()
    for vendor, category, patterns in THIRD_PARTY_PATTERNS:
        for p in patterns:
            if p in lower_url:
                return {
                    "vendor": vendor,
                    "category": category,
                    "is_third_party": True,
                    "domain": host,
                }

    # If domain differs from page domain, mark as generic third-party
    clean_page_domain = page_domain.lower().replace("www.", "")
    clean_host = host.replace("www.", "")

    if clean_host and clean_page_domain and clean_page_domain not in clean_host and clean_host not in clean_page_domain:
        return {
            "vendor": f"External ({clean_host})",
            "category": "Third-Party Script",
            "is_third_party": True,
            "domain": host,
        }

    return {
        "vendor": "First-Party Application",
        "category": "First-Party Code",
        "is_third_party": False,
        "domain": host or page_domain,
    }
