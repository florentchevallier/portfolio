#!/usr/bin/env python3
"""Static site builder for the portfolio.

    python build.py              build the site into dist/
    python build.py --serve      build, serve on http://localhost:8000 and rebuild on change
    python build.py --strict     build and exit with an error if a warning is raised (used in CI)

Content lives in content/, layout in templates/, styling and scripts in static/.
See README.md for how to add a project or edit a page.
"""
from __future__ import annotations

import argparse
import datetime as dt
import functools
import http.server
import re
import shutil
import socketserver
import sys
import threading
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, pass_context, select_autoescape

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
DIST = ROOT / "dist"

WARNINGS: list[str] = []


def warn(msg: str) -> None:
    WARNINGS.append(msg)
    print(f"  warning: {msg}", file=sys.stderr)


# --------------------------------------------------------------------------- loading

def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def split_front_matter(text: str) -> tuple[dict, str]:
    """Return (metadata, body) for a Markdown file with optional YAML front matter."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return yaml.safe_load(parts[1]) or {}, parts[2].lstrip("\n")
    return {}, text


def render_markdown(text: str) -> tuple[str, list[dict]]:
    """Render Markdown to HTML. Returns (html, [{'id':..., 'title':...}, ...]) for the h2 headings."""
    md = markdown.Markdown(
        extensions=["extra", "toc", "attr_list", "sane_lists", "smarty", "codehilite"],
        extension_configs={
            "toc": {"toc_depth": "2-3", "permalink": False},
            "codehilite": {"css_class": "hl", "guess_lang": False},
        },
    )
    html = md.convert(text)
    toc = [{"id": t["id"], "title": t["name"]} for t in md.toc_tokens if t["level"] == 2]
    return html, toc


REQUIRED_PROJECT_FIELDS = ("title", "summary", "kind", "order")


def load_projects(include_drafts: bool) -> list[dict]:
    projects = []
    for folder in sorted((CONTENT / "projects").iterdir()):
        index = folder / "index.md"
        if not index.exists():
            continue
        meta, body = split_front_matter(index.read_text(encoding="utf-8"))
        missing = [f for f in REQUIRED_PROJECT_FIELDS if f not in meta]
        if missing:
            warn(f"{index.relative_to(ROOT)}: missing front-matter field(s): {', '.join(missing)}")
            continue
        if meta.get("draft") and not include_drafts:
            continue
        html, toc = render_markdown(body)
        meta.update(slug=folder.name, folder=folder, body=html, toc=toc, url=f"projects/{folder.name}/")
        for key in ("cover",):
            if meta.get(key) and not (folder / meta[key]).exists():
                warn(f"{index.relative_to(ROOT)}: {key} file '{meta[key]}' not found")
        projects.append(meta)
    projects.sort(key=lambda p: (p["order"], p["title"]))
    return projects


# --------------------------------------------------------------------------- rendering

@pass_context
def translate(ctx, value):
    """Pick the text for the page language from {en: ..., de: ...}; plain values pass through."""
    if isinstance(value, dict) and ("en" in value or "de" in value):
        return value.get(ctx.get("lang", "en")) or value.get("en")
    return value


def make_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["tr"] = translate
    return env


def root_for(url: str) -> str:
    """Relative prefix that leads from a page URL back to the site root ('' for the home page)."""
    depth = len([p for p in url.split("/") if p])
    return "../" * depth


def write_page(env: Environment, out_rel: str, template: str, ctx: dict, root: str | None = None) -> None:
    """Render `template` to dist/<out_rel>.

    out_rel is either a directory URL ('' for home, 'about/', 'projects/x/') written as <dir>/index.html,
    or a plain file name ('404.html'). `root` is the relative prefix leading back to the site root.
    """
    is_dir = out_rel == "" or out_rel.endswith("/")
    target = DIST / (out_rel + "index.html") if is_dir else DIST / out_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    ctx = {**ctx, "root": root_for(out_rel) if root is None else root, "url": out_rel}
    target.write_text(env.get_template(template).render(**ctx), encoding="utf-8")


def copy_static() -> None:
    shutil.copytree(STATIC, DIST / "static", dirs_exist_ok=True)


def copy_project_assets(project: dict) -> None:
    dest = DIST / "projects" / project["slug"]
    dest.mkdir(parents=True, exist_ok=True)
    for f in project["folder"].iterdir():
        if f.name == "index.md" or f.name.startswith("."):
            continue
        if f.is_dir():
            shutil.copytree(f, dest / f.name, dirs_exist_ok=True)
        else:
            shutil.copy2(f, dest / f.name)


def write_sitemap(site: dict, urls: list[str]) -> None:
    base = site["url"].rstrip("/")
    today = dt.date.today().isoformat()
    body = "".join(f"  <url><loc>{base}/{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "</urlset>\n",
        encoding="utf-8",
    )
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")


# --------------------------------------------------------------------------- link check

LINK_RE = re.compile(r'(?:href|src)="([^"]+)"')


def check_links() -> None:
    """Warn about internal links/assets that point to files missing from dist/."""
    for page in DIST.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        for link in LINK_RE.findall(text):
            if re.match(r"^(https?:|mailto:|tel:|data:|#|javascript:)", link) or link in ("", "./"):
                continue
            path = unquote(urlparse(link).path)
            target = (page.parent / path).resolve()
            if path.endswith("/") or target.is_dir():
                target = target / "index.html"
            if not target.exists():
                warn(f"{page.relative_to(DIST)}: broken link -> {link}")


# --------------------------------------------------------------------------- build

def build(include_drafts: bool = False) -> None:
    WARNINGS.clear()
    t0 = time.time()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    site = load_yaml(CONTENT / "site.yml")
    profile = load_yaml(CONTENT / "data" / "profile.yml")
    german = load_yaml(CONTENT / "data" / "de.yml")
    projects = load_projects(include_drafts)
    featured = [p for p in projects if p.get("featured", True)]

    about_meta, about_body = split_front_matter((CONTENT / "pages" / "about.md").read_text(encoding="utf-8"))
    about_html, _ = render_markdown(about_body)

    env = make_env()
    env.globals.update(site=site, profile=profile, de=german, projects=projects, year=dt.date.today().year)

    urls = [""]
    write_page(env, "", "home.html", {"featured": featured, "page_title": None})
    write_page(env, "projects/", "projects.html", {"page_title": "Work", "meta": {"description": site["work_description"]}})
    urls.append("projects/")
    write_page(env, "about/", "about.html", {"page_title": "About", "body": about_html, "meta": about_meta})
    urls.append("about/")
    write_page(env, "de/", "de.html", {"page_title": None, "lang": "de"})
    urls.append("de/")

    for i, p in enumerate(projects):
        neighbour = projects[(i + 1) % len(projects)] if len(projects) > 1 else None
        write_page(env, p["url"], "project.html", {"p": p, "page_title": p["title"], "next_project": neighbour})
        copy_project_assets(p)
        urls.append(p["url"])

    # The 404 page can be served from any depth, so it links to the site through absolute URLs.
    write_page(env, "404.html", "404.html", {"page_title": "Page not found"}, root=site["url"].rstrip("/") + "/")
    copy_static()
    write_sitemap(site, urls)
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    check_links()
    print(f"Built {len(urls)} pages in {time.time() - t0:.1f}s -> {DIST.relative_to(ROOT)}/"
          f"  ({len(WARNINGS)} warning{'s' if len(WARNINGS) != 1 else ''})")


# --------------------------------------------------------------------------- serve / watch

def snapshot() -> float:
    newest = 0.0
    for base in (CONTENT, TEMPLATES, STATIC):
        for f in base.rglob("*"):
            if f.is_file():
                newest = max(newest, f.stat().st_mtime)
    return newest


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args, **kwargs):
        pass


def serve(port: int) -> None:
    handler = functools.partial(_QuietHandler, directory=str(DIST))
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print(f"Serving http://localhost:{port}  (Ctrl+C to stop; the site rebuilds when you save a file)")
    last = snapshot()
    try:
        while True:
            time.sleep(0.8)
            now = snapshot()
            if now != last:
                last = now
                try:
                    build(include_drafts=True)
                except Exception as exc:  # keep serving even if a save leaves a file half-written
                    print(f"  build failed: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        print()
        httpd.shutdown()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serve", action="store_true", help="serve dist/ locally and rebuild on change")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--drafts", action="store_true", help="include projects marked `draft: true`")
    ap.add_argument("--strict", action="store_true", help="fail if any warning is raised")
    args = ap.parse_args()

    build(include_drafts=args.drafts or args.serve)
    if args.serve:
        serve(args.port)
        return 0
    return 1 if (args.strict and WARNINGS) else 0


if __name__ == "__main__":
    sys.exit(main())
