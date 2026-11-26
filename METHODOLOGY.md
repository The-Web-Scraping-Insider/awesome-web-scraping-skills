# How the list is built and ranked

## Inclusion (editorial)

A skill is listed if it meets the rules in [CONTRIBUTING.md](CONTRIBUTING.md). Inclusion is the only human decision. Order is never hand-tuned.

## Ranking (automatic)

Every skill gets a score from 0 to 100:

| Signal | Weight | Source | Notes |
|---|---:|---|---|
| GitHub stars | 45% | GitHub API | `log10(stars + 1)`, divided by the highest value in the list |
| Installs | 45% | [skills.sh](https://skills.sh) skill pages | `log10(installs + 1)`, divided by the highest value in the list |
| Recent activity | 10% | GitHub API (`pushed_at`) | 1.0 if pushed today, falling to 0 at 90 days |

Adjustments:

- **Collection repos.** When a skill lives in a large multi-purpose repo (marked `catalog: true`), the repo's stars say little about that one skill, so they count at 25%. These are marked with † in the README.
- **Archived repos** have their score halved.
- **Missing data** counts as zero. Install counts are only available for skills listed on skills.sh, so skills not listed there rank on stars and activity alone.

Log scaling stops one huge repo from flattening everything else: 10× the stars is worth a fixed step up, not 10× the score.

The weights live in [`scripts/common.py`](scripts/common.py). Any change to them is made in a public PR.

## Refresh schedule

A [GitHub Action](.github/workflows/refresh.yml) runs daily. It fetches stars and installs, saves a snapshot to `data/stats/history/`, re-renders the README and commits the result. The snapshots power the weekly star changes shown next to each skill.

## Limitations

- Install counts come from one directory and are approximate. Skills installed by cloning a repo or through a plugin marketplace aren't counted.
- Stars measure attention, not quality. Read a skill's `SKILL.md` before you install it, especially one that runs scripts.
- Capability tags come from each skill's own documentation; we don't benchmark them. (For scraping API performance benchmarks, see [ScrapeOps](https://scrapeops.io/?utm_source=awesome-web-scraping-skills&utm_medium=github).)

## Disclosure

The list is curated by [The Web Scraping Insider](https://www.reddit.com/r/WebScrapingInsider/) and supported by [ScrapeOps](https://scrapeops.io/?utm_source=awesome-web-scraping-skills&utm_medium=github). Any skill published by ScrapeOps follows exactly the same inclusion and ranking rules as every other vendor.
