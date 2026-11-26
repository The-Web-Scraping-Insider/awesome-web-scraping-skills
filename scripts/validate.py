"""Validate data/*.yaml. Runs on every pull request.

Exit code 1 and a list of problems if anything is wrong.
"""
from __future__ import annotations

import re
import sys
from datetime import date

from common import load_yaml

TYPES = {"official-vendor", "official-tool", "community"}
REQUIRED = ["id", "name", "type", "category", "description", "paid_api", "capabilities", "install", "added"]
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def main() -> int:
    skills = load_yaml("skills.yaml")
    vendors = {v["id"] for v in load_yaml("vendors.yaml")}
    categories = {c["id"] for c in load_yaml("categories.yaml")}
    caps = {c["id"] for c in load_yaml("capabilities.yaml")}
    picks = load_yaml("quick_picks.yaml")
    errors: list[str] = []
    seen: set[str] = set()

    for i, s in enumerate(skills):
        where = f"skills.yaml entry #{i + 1} ({s.get('id', '?')})"
        for f in REQUIRED:
            if f not in s or s[f] in (None, ""):
                errors.append(f"{where}: missing '{f}'")
        if s.get("id") in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(s.get("id"))
        if s.get("type") not in TYPES:
            errors.append(f"{where}: type must be one of {sorted(TYPES)}")
        if s.get("type") == "community":
            if not s.get("author"):
                errors.append(f"{where}: community skills need 'author'")
            if s.get("vendor"):
                errors.append(f"{where}: community skills must not set 'vendor'")
        elif s.get("vendor") not in vendors:
            errors.append(f"{where}: vendor '{s.get('vendor')}' not in vendors.yaml")
        if s.get("category") not in categories:
            errors.append(f"{where}: unknown category '{s.get('category')}'")
        for c in s.get("capabilities") or []:
            if c not in caps:
                errors.append(f"{where}: unknown capability '{c}'")
        if not s.get("repo") and not s.get("url"):
            errors.append(f"{where}: needs 'repo' or 'url'")
        if s.get("repo") and not REPO_RE.match(s["repo"]):
            errors.append(f"{where}: repo must be 'owner/name'")
        if s.get("url") and not str(s["url"]).startswith("https://"):
            errors.append(f"{where}: url must start with https://")
        if not isinstance(s.get("paid_api"), bool):
            errors.append(f"{where}: paid_api must be true or false")
        desc = s.get("description") or ""
        if len(desc) > 220:
            errors.append(f"{where}: description is over 220 characters")
        if re.search(r"\b(best|leading|ultimate|revolutionary|#1)\b", desc, re.I):
            errors.append(f"{where}: description reads like marketing copy; describe what it does")
        if not isinstance(s.get("added"), date):
            errors.append(f"{where}: added must be a date (YYYY-MM-DD)")

    for p in picks:
        for sid in p["skills"]:
            if sid not in seen:
                errors.append(f"quick_picks.yaml: unknown skill id '{sid}'")

    if errors:
        print("\n".join(f"✗ {e}" for e in errors))
        return 1
    print(f"✓ {len(skills)} skills valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
