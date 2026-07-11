#!/usr/bin/env python3
"""Generate Mila's terminal-style GitHub profile SVG from public GitHub data."""

from __future__ import annotations

import argparse
import base64
import calendar
import json
import os
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
USERNAME = "MilaArtyNew"
API = "https://api.github.com"

SELECTED_REPOS = [
    "carrypilot",
    "x-web3-digest",
    "funding-alerts-bot",
    "lp-tracker",
    "polymarket-tracker",
]


def request_json(path: str, token: str | None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "milanewgpt-profile-readme",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{API}{path}", headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def load_live_data(token: str | None) -> dict[str, Any]:
    user = request_json(f"/users/{USERNAME}", token)
    repos: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = request_json(
            f"/users/{USERNAME}/repos?type=owner&sort=updated&per_page=100&page={page}", token
        )
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return {"user": user, "repos": repos, "generated_at": datetime.now(timezone.utc).isoformat()}


def whole_months_between(start: datetime, end: datetime) -> tuple[int, int, int]:
    months = (end.year - start.year) * 12 + end.month - start.month
    if end.day < start.day:
        months -= 1
    anchor_year = start.year + (start.month - 1 + months) // 12
    anchor_month = (start.month - 1 + months) % 12 + 1
    anchor_day = min(start.day, calendar.monthrange(anchor_year, anchor_month)[1])
    anchor = datetime(anchor_year, anchor_month, anchor_day, tzinfo=timezone.utc)
    days = (end - anchor).days
    return months // 12, months % 12, days


def summarize(data: dict[str, Any]) -> dict[str, str]:
    user = data["user"]
    repos = [repo for repo in data["repos"] if not repo.get("private")]
    originals = [repo for repo in repos if not repo.get("fork")]
    languages = Counter(repo.get("language") for repo in originals if repo.get("language"))
    top_languages = " · ".join(language for language, _ in languages.most_common(4)) or "Python"
    stars = sum(int(repo.get("stargazers_count") or 0) for repo in originals)
    latest = max((repo.get("updated_at") or "" for repo in repos), default="")
    latest_text = latest[:10] if latest else "—"
    created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    generated = datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
    years, months, days = whole_months_between(created, generated)
    selected = [repo for repo in originals if repo.get("name") in SELECTED_REPOS]
    return {
        "uptime": f"{years}y {months}m {days}d on GitHub",
        "public_repos": str(user.get("public_repos", len(repos))),
        "original_repos": str(len(originals)),
        "followers": str(user.get("followers", 0)),
        "stars": str(stars),
        "top_languages": top_languages,
        "selected_systems": str(len(selected)),
        "latest_update": latest_text,
    }


def text(x: int, y: int, value: str, css_class: str, anchor: str = "start") -> str:
    return f'<text x="{x}" y="{y}" class="{css_class}" text-anchor="{anchor}">{escape(value)}</text>'


def row(y: int, label: str, value: str, value_class: str = "value") -> str:
    return "\n".join([
        text(488, y, label, "key"),
        text(700, y, "········", "dots"),
        text(786, y, value, value_class),
    ])


def render_avatar() -> str:
    avatar_path = ROOT / "assets" / "avatar.png"
    encoded = base64.b64encode(avatar_path.read_bytes()).decode("ascii")
    return f'''
  <defs>
    <clipPath id="avatarClip">
      <rect x="42" y="112" width="364" height="400" rx="20"/>
    </clipPath>
  </defs>
  <image x="42" y="112" width="364" height="400" preserveAspectRatio="xMidYMid slice" href="data:image/png;base64,{encoded}" clip-path="url(#avatarClip)"/>
  <rect x="42" y="112" width="364" height="400" rx="20" fill="none" stroke="#38e8c5" stroke-opacity="0.38"/>
  <rect x="42" y="438" width="364" height="74" rx="20" fill="#020409" opacity="0.42"/>
  <text x="66" y="474" class="monoLabel">WEB3 OPERATOR</text>
  <text x="66" y="498" class="monoSmall">RISK · SYSTEMS · AUTOMATION</text>
'''


def render_svg(stats: dict[str, str]) -> str:
    sections = [
        text(488, 60, "PROFILE / OPERATOR OVERVIEW", "eyebrow"),
        text(488, 92, "Mila Arty", "hero"),
        row(136, "Mode", "Web3 operator · finance brain", "accent"),
        row(170, "Uptime", stats["uptime"], "accent"),
        row(204, "Focus", "DeFi · prediction markets · onchain"),
        row(238, "Edge", "risk-first systems, not hype"),
        row(272, "Runtime", "Telegram bots · alerts · automation"),
        text(488, 316, "— BUILD SURFACE", "section"),
        row(354, "Languages.Code", stats["top_languages"], "accent"),
        row(388, "Languages.Real", "Russian · English · Hebrew"),
        row(422, "Systems", "funding · LP ranges · digests · trackers"),
        row(456, "Building", "semi-passive Web3 workflows"),
        text(488, 500, "— CONTACT", "section"),
        row(538, "GitHub", "github.com/MilaArtyNew", "accent"),
        row(572, "X", "@mila_arty"),
        row(606, "Signal", "mechanics before narrative", "accent"),
        text(488, 652, "— GITHUB SIGNAL", "section"),
    ]
    stat_items = [
        (488, "PUBLIC REPOS", stats["public_repos"]),
        (650, "ORIGINAL", stats["original_repos"]),
        (812, "STARS", stats["stars"]),
        (974, "SYSTEMS", stats["selected_systems"]),
    ]
    stat_svg = []
    for x, label, value in stat_items:
        stat_svg.extend([
            f'<rect x="{x}" y="672" width="148" height="56" rx="12" class="statBox"/>',
            text(x + 14, 692, label, "statLabel"),
            text(x + 14, 716, value, "statValue"),
        ])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760" role="img" aria-labelledby="title desc">
  <title id="title">Mila — Web3 operator profile</title>
  <desc id="desc">Terminal-style GitHub profile card with public focus areas, links, and GitHub statistics.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#04060b"/>
      <stop offset="0.50" stop-color="#08101a"/>
      <stop offset="1" stop-color="#0b0712"/>
    </linearGradient>
    <radialGradient id="cyanGlow" cx="0.18" cy="0.55" r="0.54">
      <stop offset="0" stop-color="#20e3c2" stop-opacity="0.16"/>
      <stop offset="1" stop-color="#20e3c2" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="goldGlow" cx="0.92" cy="0.05" r="0.62">
      <stop offset="0" stop-color="#ffb454" stop-opacity="0.14"/>
      <stop offset="1" stop-color="#ffb454" stop-opacity="0"/>
    </radialGradient>
    <style>
      text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }}
      .eyebrow {{ font-size: 12px; fill: #8894a8; letter-spacing: 2px; font-weight: 700; }}
      .hero {{ font-size: 26px; fill: #f6f8ff; font-weight: 800; letter-spacing: -0.6px; }}
      .key {{ font-size: 14px; fill: #ffb454; font-weight: 700; }}
      .dots {{ font-size: 14px; fill: #273247; letter-spacing: 1.5px; }}
      .value {{ font-size: 14px; fill: #cdd8e8; }}
      .accent {{ font-size: 14px; fill: #64f0d2; }}
      .section {{ font-size: 12px; fill: #8d98aa; letter-spacing: 1.6px; font-weight: 700; }}
      .statBox {{ fill: #0d1522; stroke: #29364c; stroke-opacity: 0.85; }}
      .statLabel {{ font-size: 10px; fill: #8390a5; letter-spacing: 1px; font-weight: 700; }}
      .statValue {{ font-size: 18px; fill: #f0f5ff; font-weight: 800; }}
      .micro {{ font-size: 10px; fill: #76849a; letter-spacing: 0.7px; }}
      .monoArt {{ font-size: 19px; fill: #79ffe1; font-weight: 800; }}
      .monoLabel {{ font-size: 20px; fill: #f6f8ff; font-weight: 800; letter-spacing: 2px; }}
      .monoSmall {{ font-size: 12px; fill: #ffcf8a; letter-spacing: 1.4px; font-weight: 700; }}
    </style>
  </defs>
  <rect width="1200" height="760" rx="26" fill="#020409"/>
  <rect x="5" y="5" width="1190" height="750" rx="22" fill="url(#bg)" stroke="#202b3b"/>
  <rect x="6" y="6" width="1188" height="748" rx="21" fill="url(#cyanGlow)"/>
  <rect x="6" y="6" width="1188" height="748" rx="21" fill="url(#goldGlow)"/>
  <line x1="448" y1="42" x2="448" y2="724" stroke="#263143" stroke-opacity="0.82"/>
  <text x="54" y="60" class="eyebrow">IDENTITY / WEB3 SIGNAL</text>
  <text x="54" y="91" class="hero">Mila Arty</text>
  {render_avatar()}
  <text x="54" y="638" class="section">— OPERATOR SIGNAL</text>
  <text x="54" y="670" class="micro">MODE  ANALYZE / BUILD / AUTOMATE</text>
  <text x="54" y="694" class="micro">LENS  RISK FIRST · MECHANICS FIRST</text>
  <text x="54" y="722" class="micro">PUBLIC PROFILE · NO PRIVATE RUNTIME DATA</text>
  {''.join(sections)}
  {''.join(stat_svg)}
  <text x="1138" y="740" class="micro" text-anchor="end">UPDATED {escape(stats['latest_update'])}</text>
</svg>
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, help="Use deterministic JSON instead of GitHub API")
    parser.add_argument("--output", type=Path, default=ROOT / "assets" / "profile.svg")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = json.loads(args.fixture.read_text(encoding="utf-8")) if args.fixture else load_live_data(os.environ.get("GITHUB_TOKEN"))
    stats = summarize(data)
    output = render_svg(stats)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    sys.stdout.write(json.dumps({"output": str(args.output), "stats": stats}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
