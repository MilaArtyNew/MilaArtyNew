import json
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generate_profile", ROOT / "scripts" / "generate_profile.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProfileGeneratorTests(unittest.TestCase):
    def fixture(self):
        return {
            "generated_at": datetime(2026, 7, 11, tzinfo=timezone.utc).isoformat(),
            "user": {
                "created_at": "2024-01-01T00:00:00Z",
                "public_repos": 3,
                "followers": 7,
            },
            "repos": [
                {"name": "carrypilot", "private": False, "fork": False, "language": "Python", "stargazers_count": 2, "updated_at": "2026-07-10T00:00:00Z"},
                {"name": "lp-tracker", "private": False, "fork": False, "language": "Python", "stargazers_count": 1, "updated_at": "2026-07-09T00:00:00Z"},
                {"name": "forked", "private": False, "fork": True, "language": "Go", "stargazers_count": 99, "updated_at": "2026-07-01T00:00:00Z"},
            ],
        }

    def test_summary_uses_public_original_repos(self):
        stats = MODULE.summarize(self.fixture())
        self.assertEqual(stats["public_repos"], "3")
        self.assertEqual(stats["original_repos"], "2")
        self.assertEqual(stats["stars"], "3")
        self.assertEqual(stats["selected_systems"], "2")
        self.assertEqual(stats["top_languages"], "Python")

    def test_svg_is_valid_and_public_safe(self):
        svg = MODULE.render_svg(MODULE.summarize(self.fixture()))
        ET.fromstring(svg)
        self.assertIn("Mila Arty", svg)
        self.assertIn("PUBLIC PROFILE · NO PRIVATE RUNTIME DATA", svg)
        forbidden = ["TELEGRAM_TOKEN", "API_KEY", "PRIVATE KEY", "session.json", ".env"]
        for word in forbidden:
            self.assertNotIn(word, svg)


if __name__ == "__main__":
    unittest.main()
