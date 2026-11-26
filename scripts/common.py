"""Shared loading, scoring and formatting helpers."""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STATS = DATA / "stats"

# Weights for the ranking score. Documented in METHODOLOGY.md; change both together.
W_STARS = 0.45
W_INSTALLS = 0.45
W_FRESH = 0.10
CATALOG_STAR_FACTOR = 0.25  # stars of multi-purpose collections count for less
FRESH_DAYS = 90


def load_yaml(name: str):
    with open(DATA / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_stats() -> dict:
    p = STATS / "latest.json"
    if not p.exists():
        return {"updated": None, "repos": {}, "installs": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def load_history_snapshot(days_ago: int) -> dict | None:
    """Return the snapshot closest to `days_ago` days before today (or None)."""
    hist = sorted((STATS / "history").glob("*.json"))
    if not hist:
        return None
    target = date.today() - timedelta(days=days_ago)
    best = None
    for p in hist:
        try:
            d = date.fromisoformat(p.stem)
        except ValueError:
            continue
        if d <= target:
            best = p
    return json.loads(best.read_text(encoding="utf-8")) if best else None


def skill_url(s: dict) -> str:
    if s.get("url"):
        return s["url"]
    return f"https://github.com/{s['repo']}"


def load_all():
    skills = load_yaml("skills.yaml")
    vendors = {v["id"]: v for v in load_yaml("vendors.yaml")}
    categories = load_yaml("categories.yaml")
    capabilities = load_yaml("capabilities.yaml")
    picks = load_yaml("quick_picks.yaml")
    stats = load_stats()
    attach_stats(skills, stats)
    return skills, vendors, categories, capabilities, picks, stats


def attach_stats(skills: list[dict], stats: dict) -> None:
    repos = stats.get("repos", {})
    installs = stats.get("installs", {})
    week_ago = load_history_snapshot(7)
    old_repos = (week_ago or {}).get("repos", {})

    for s in skills:
        r = repos.get(s.get("repo") or "", {})
        s["stars"] = r.get("stars")
        s["pushed_at"] = r.get("pushed_at")
        s["archived"] = r.get("archived", False)
        s["installs"] = installs.get(s["id"])
        old = old_repos.get(s.get("repo") or "", {}).get("stars")
        s["stars_week"] = (s["stars"] - old) if (s["stars"] is not None and old is not None) else None

    # Score: log-scaled stars and installs, each normalised to the list maximum.
    def eff_stars(s):
        if s["stars"] is None:
            return 0
        return s["stars"] * (CATALOG_STAR_FACTOR if s.get("catalog") else 1)

    max_s = max((math.log10(eff_stars(s) + 1) for s in skills), default=1) or 1
    max_i = max((math.log10((s["installs"] or 0) + 1) for s in skills), default=1) or 1
    now = datetime.now(timezone.utc)
    for s in skills:
        fresh = 0.0
        if s["pushed_at"]:
            pushed = datetime.fromisoformat(s["pushed_at"].replace("Z", "+00:00"))
            age = (now - pushed).days
            fresh = max(0.0, 1 - age / FRESH_DAYS)
        score = (
            W_STARS * math.log10(eff_stars(s) + 1) / max_s
            + W_INSTALLS * math.log10((s["installs"] or 0) + 1) / max_i
            + W_FRESH * fresh
        )
        if s["archived"]:
            score *= 0.5
        s["score"] = round(score * 100, 1)


def fmt_num(n) -> str:
    if n is None:
        return "–"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"{n/1_000:.1f}K".replace(".0K", "K")
    return str(n)
