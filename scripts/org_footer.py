"""Shared footer and "listed in" badge for The Web Scraping Insider repos.

The data lives in shared/org.yml. The canonical copy is in the org's .github repo;
every other repo keeps a synced copy at shared/org.yml (and an identical copy of
this script) so builds and `--check` runs never depend on the network.

Usage:
    python scripts/org_footer.py sync     # refresh shared/org.yml from the .github repo
    python scripts/org_footer.py preview  # print this repo's footer and badge section

From a generator:
    from org_footer import load_org, footer_md, badge_section_md
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path
from urllib.parse import quote, urlencode

import yaml

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / "shared" / "org.yml"
CANONICAL = "https://raw.githubusercontent.com/The-Web-Scraping-Insider/.github/main/shared/org.yml"
START = "<!-- ORG-FOOTER:START - generated from shared/org.yml (canonical copy in The-Web-Scraping-Insider/.github); don't edit here -->"
END = "<!-- ORG-FOOTER:END -->"

# Badge colours: r/WebScrapingInsider navy + accent blue.
NAVY = "111A2D"
BLUE = "2F64F7"


def load_org(path: Path = LOCAL) -> dict:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    _validate(cfg)
    return cfg


def _validate(cfg) -> None:
    if not isinstance(cfg, dict):
        raise ValueError("org.yml: expected a mapping")
    for key in ("org", "links", "repos"):
        if key not in cfg:
            raise ValueError(f"org.yml: missing '{key}'")
    for k in ("newsletter", "subreddit", "hub", "scrapeops"):
        if k not in cfg["links"]:
            raise ValueError(f"org.yml: links.{k} missing")
    for r in cfg["repos"]:
        for k in ("name", "title"):
            if k not in r:
                raise ValueError(f"org.yml: repo entry missing '{k}': {r}")


def _repo(cfg: dict, name: str) -> dict:
    for r in cfg["repos"]:
        if r["name"] == name:
            return r
    raise KeyError(f"{name} is not in shared/org.yml")


def _utm(url: str, repo: str, campaign: str = "org-footer") -> str:
    sep = "&" if "?" in url else "?"
    return url + sep + urlencode({"utm_source": repo, "utm_medium": "github", "utm_campaign": campaign})


def repo_url(cfg: dict, name: str) -> str:
    return f"{cfg['org']['url']}/{name}"


# ------------------------------------------------------------------ footer

def footer_md(cfg: dict, current: str) -> str:
    """Footer for `current`'s README: the other live repos plus community links."""
    others = [r for r in cfg["repos"] if r.get("footer") and r["name"] != current]
    L = cfg["links"]
    org = cfg["org"]
    out = [START, "", "---", "", '<div align="center">', "",
           f"### More from [{org['name']}]({org['url']})", ""]
    if others:
        out += ["| Project | What it is |", "|---|---|"]
        for r in others:
            out.append(f"| [**{r['title']}**]({repo_url(cfg, r['name'])}) | {r.get('blurb', '')} |")
        out.append("")
    out += [
        f"📬 [Newsletter]({_utm(L['newsletter'], current)}) · "
        f"💬 [r/WebScrapingInsider]({L['subreddit']}) · "
        f"🧭 [Hub]({_utm(L['hub'], current)}) · "
        f"🐙 [All our repos]({org['url']})",
        "",
        f"<sub>Built and maintained by the team at <a href=\"{_utm(L['scrapeops'], current)}\">ScrapeOps</a>.</sub>",
        "", "</div>", "", END,
    ]
    return "\n".join(out)


# ------------------------------------------------------------------ badge

def badge_image_url(cfg: dict, name: str, style: str | None = None) -> str:
    r = _repo(cfg, name)
    # shields.io static badge: label-message-colour, with '-' doubled and ' ' as %20
    def esc(s):
        return quote(s.replace("-", "--").replace("_", "__"), safe="")
    url = f"https://img.shields.io/badge/{esc('listed in')}-{esc(r['title'])}-{BLUE}?labelColor={NAVY}"
    if style:
        url += f"&style={style}"
    return url


def badge_md(cfg: dict, name: str) -> str:
    r = _repo(cfg, name)
    return f"[![Listed in {r['title']}]({badge_image_url(cfg, name)})]({repo_url(cfg, name)})"


def badge_html(cfg: dict, name: str) -> str:
    r = _repo(cfg, name)
    return (f'<a href="{repo_url(cfg, name)}"><img src="{badge_image_url(cfg, name)}" '
            f'alt="Listed in {r["title"]}"></a>')


def badge_section_md(cfg: dict, name: str, heading: str = "## Are you listed? Add the badge") -> str:
    r = _repo(cfg, name)
    if not r.get("badge"):
        raise ValueError(f"{name} has badge: false in shared/org.yml")
    return "\n".join([
        f"{heading}\n",
        f"If your project is on this list, show it off in your README:\n",
        badge_md(cfg, name) + "\n",
        "**Markdown**\n",
        "```markdown", badge_md(cfg, name), "```\n",
        "**HTML**\n",
        "```html", badge_html(cfg, name), "```\n",
        "<sub>Prefer a bigger badge? Add <code>&amp;style=for-the-badge</code> to the image URL.</sub>\n",
    ])


# ------------------------------------------------------------------ sync

def sync(path: Path = LOCAL, url: str = CANONICAL) -> int:
    """Refresh the local copy from the .github repo. Never fails the build: on any
    error it keeps the existing copy and prints a warning."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "wsi-org-footer"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            text = resp.read().decode("utf-8")
        _validate(yaml.safe_load(text))
    except Exception as e:  # noqa: BLE001 - a footer must never break the daily job
        print(f"::warning::org_footer sync failed, keeping existing shared/org.yml ({e})")
        return 0
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    if text != old:
        path.parent.mkdir(exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print("shared/org.yml updated from the .github repo")
    else:
        print("shared/org.yml already up to date")
    return 0


def main(argv) -> int:
    cmd = argv[1] if len(argv) > 1 else "preview"
    if cmd == "sync":
        return sync()
    if cmd == "preview":
        cfg = load_org()
        name = ROOT.name if len(argv) < 3 else argv[2]
        print(footer_md(cfg, name))
        if _repo(cfg, name).get("badge"):
            print("\n" + badge_section_md(cfg, name))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
