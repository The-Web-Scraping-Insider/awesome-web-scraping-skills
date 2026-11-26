# Contributing

Thanks for helping keep this list useful. There are two ways to add a skill.

## 1. Use the form (easiest)

[Open a "Submit a skill" issue](https://github.com/The-Web-Scraping-Insider/awesome-web-scraping-skills/issues/new?template=submit-skill.yml). A maintainer adds it to the data file.

## 2. Open a pull request

The README is **generated**, so never edit it directly. Instead:

1. Add an entry to [`data/skills.yaml`](data/skills.yaml). Copy an existing entry and follow the field notes at the top of the file.
2. For a new vendor's official skill, also add the vendor to [`data/vendors.yaml`](data/vendors.yaml).
3. Run the checks locally:

   ```bash
   pip install -r requirements.txt
   python scripts/validate.py
   python scripts/render.py   # optional: preview the README
   ```

4. Open the PR. A bot refreshes stars, installs and the README after it's merged.

## What gets in

- The skill is about **getting data from the web**: scraping, crawling, browser automation, proxies, unblocking or extraction.
- It's a real Agent Skill (a `SKILL.md`) or a Claude Code plugin that ships skills, not just an MCP server or a library.
- It works and is maintained, or is new enough to be given the benefit of the doubt.
- The description is one plain sentence about what it does. "Best", "#1", "ultimate" and similar words are rejected by the validator.

## Official vs community

- **Official**: published by the company or open-source project behind the tool the skill uses.
- **Community**: everything else, including skills that wrap a vendor's API but aren't published by that vendor.

## Vendors

Vendors are welcome to add and update their own skills. Please say in the PR that you work for the vendor. Placement is decided by the automatic ranking ([METHODOLOGY.md](METHODOLOGY.md)), never by who submitted the entry.

## Removing or correcting an entry

Open an issue or PR. If you maintain a listed skill and want it removed, we'll remove it.
