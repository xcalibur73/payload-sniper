"""
Unit tests for PayloadSniper script profiling, vendor classification, and INP estimation.
"""

import unittest
from payload_sniper.script_analyzer import classify_script_vendor
from payload_sniper.scorer import calculate_tbt_score, estimate_inp_risk, audit_profile_results


class TestScriptAnalyzer(unittest.TestCase):

    def test_classify_google_tag_manager(self):
        res = classify_script_vendor("https://www.googletagmanager.com/gtm.js?id=GTM-XXXX", "example.com")
        self.assertEqual(res["vendor"], "Google Tag Manager")
        self.assertTrue(res["is_third_party"])
        self.assertEqual(res["category"], "Tag Management")

    def test_classify_meta_pixel(self):
        res = classify_script_vendor("https://connect.facebook.net/en_US/fbevents.js", "example.com")
        self.assertEqual(res["vendor"], "Meta Pixel (Facebook)")
        self.assertTrue(res["is_third_party"])

    def test_classify_first_party(self):
        res = classify_script_vendor("https://example.com/_next/static/chunks/main.js", "example.com")
        self.assertEqual(res["vendor"], "First-Party Application")
        self.assertFalse(res["is_third_party"])

    def test_classify_inline_script(self):
        res = classify_script_vendor("", "example.com")
        self.assertEqual(res["vendor"], "Inline Script")
        self.assertFalse(res["is_third_party"])


class TestTBTAndINPScorer(unittest.TestCase):

    def test_tbt_score_perfect(self):
        self.assertEqual(calculate_tbt_score(50), 100.0)

    def test_tbt_score_high_blocking(self):
        self.assertLess(calculate_tbt_score(1500), 15.0)

    def test_inp_risk_good(self):
        res = estimate_inp_risk(80, 50)
        self.assertTrue(res["meets_google_target"])
        self.assertEqual(res["status"], "Good (Low INP Risk)")

    def test_inp_risk_poor(self):
        res = estimate_inp_risk(600, 800)
        self.assertFalse(res["meets_google_target"])
        self.assertEqual(res["status"], "Poor (Severe Interaction Delay)")


class TestAuditProfileResults(unittest.TestCase):

    def test_composite_score_pass(self):
        profile_data = {
            "url": "https://example.com",
            "mode": "test",
            "total_scripts": 5,
            "third_party_scripts": 0,
            "render_blocking_scripts": 0,
            "total_blocking_time_ms": 50,
            "max_long_task_ms": 60,
            "scripts": [
                {
                    "src": "https://example.com/app.js",
                    "vendor": "First-Party Application",
                    "category": "Application Code",
                    "is_third_party": False,
                    "is_render_blocking": False,
                }
            ],
            "long_tasks": [],
        }
        res = audit_profile_results(profile_data)
        self.assertGreaterEqual(res["overall_score"], 90.0)
        self.assertEqual(res["grade"], "A")
        self.assertTrue(res["inp_estimate"]["meets_google_target"])


if __name__ == "__main__":
    unittest.main()
