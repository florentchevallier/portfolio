#!/usr/bin/env python3
"""Create the skeleton of a new project.

    python tools/new_project.py "My new project"

Creates content/projects/my-new-project/index.md marked `draft: true`, so it shows up in
`python build.py --serve` but not in the published site. Remove the `draft` line when it is ready.
"""
import re
import sys
from pathlib import Path

TEMPLATE = '''---
title: {title}
kind: What it is, in a few words        # e.g. Web map, Python tool, Analysis, Static map
status: Prototype                       # optional: version or state
year: {year}
order: {order}                          # position on the home page (lowest first)
featured: true                          # false = listed on /projects/ only
draft: true                             # remove this line to publish
summary: >-
  One or two sentences for the project card and for search results.
summary_de: >-
  Optional German summary, used on the German page.
lead: >-
  Optional longer introduction shown under the title (falls back to the summary).
tags: [Python, QGIS]                    # technologies, shown on the card
# cover: cover.jpg                      # image in this folder; optional
# cover_alt: Describe the image for screen readers
# cover_ratio: 16 / 9                   # width / height of the image
links:
  - {{label: Source code, url: "https://github.com/florentchevallier/..."}}
facts:                                  # optional: the panel next to the text
  - {{label: Role, value: "..."}}
  - {{label: Built with, value: "..."}}
---

## Why I built it

## How it works

## What I learned
'''

def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    title = sys.argv[1]
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    root = Path(__file__).resolve().parent.parent / "content" / "projects"
    folder = root / slug
    if folder.exists():
        sys.exit(f"{folder} already exists")
    folder.mkdir(parents=True)
    import datetime
    order = len(list(root.iterdir()))
    (folder / "index.md").write_text(TEMPLATE.format(title=title, year=datetime.date.today().year, order=order), encoding="utf-8")
    print(f"Created {folder / 'index.md'}")

if __name__ == "__main__":
    main()
