#!/usr/bin/env python3
"""Replace inherited template pages and regenerate this static site's metadata.

Run from any directory. This intentionally preserves images, PDFs, source
Markdown, the gallery, the CMS, and the publication pages maintained elsewhere.
"""

import argparse
import html
import json
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "data/profile.json").read_text())
BASE = PROFILE["site_url"].rstrip("/")
NAME = PROFILE["name"]
LEGACY_DIRS = {
    "backpack", "categories", "category", "event", "home", "honors",
    "news", "post", "project", "slides", "tag", "tags", "talk",
}
ATOM = "http://www.w3.org/2005/Atom"
ET.register_namespace("atom", ATOM)


def destination(path):
    parts = path.relative_to(ROOT).parts
    if parts[0] == "news" or parts[:2] == ("home", "recent_news"):
        return "/#news", "recent news"
    if parts[0] == "honors":
        return "/#honors", "honors and awards"
    if parts[0] in {"home", "post"}:
        return "/#about", "homepage"
    if parts[0] in {"backpack", "categories", "category", "project", "tag", "tags"}:
        return "/publication/", "publications"
    return "/", "homepage"


def page_head(title, canonical, description):
    esc = html.escape
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} | {NAME}</title>
  <meta name="author" content="{NAME}">
  <meta name="description" content="{esc(description, quote=True)}">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="{esc(canonical, quote=True)}">
  <link rel="icon" href="/media/site-icon.svg" type="image/svg+xml">
  <meta property="og:site_name" content="{NAME}'s homepage">
  <meta property="og:title" content="{esc(title, quote=True)} | {NAME}">
  <meta property="og:url" content="{esc(canonical, quote=True)}">
  <style>
    body {{ margin: 0; color: #203047; background: #f8fafc; font: 1rem/1.6 system-ui, sans-serif; }}
    main {{ max-width: 42rem; margin: 15vh auto; padding: 2rem; }}
    h1 {{ line-height: 1.2; }}
    a {{ color: #155bb5; text-underline-offset: .2em; }}
    .name {{ color: #53657b; }}
  </style>
"""


def redirect_page(target, label):
    canonical = BASE + target.split("#", 1)[0]
    return page_head("Page moved", canonical, f"Continue to {NAME}'s {label}.") + f"""  <meta http-equiv="refresh" content="0; url={html.escape(target, quote=True)}">
</head>
<body>
  <!-- Managed legacy redirect; source assets remain in the repository. -->
  <main>
    <p class="name">{NAME}</p>
    <h1>This page has moved</h1>
    <p>Continue to my <a href="{html.escape(target, quote=True)}">{label}</a>.</p>
  </main>
</body>
</html>
"""


def not_found_page():
    return page_head("Page not found", BASE + "/404.html", f"Find {NAME}'s homepage and publications.") + f"""</head>
<body>
  <main>
    <p class="name">{NAME}</p>
    <h1>Page not found</h1>
    <p>The address may have changed. Visit my <a href="/">homepage</a> or browse my <a href="/publication/">publications</a>.</p>
    <p>You can also <a href="/authors/admin/CV.pdf">download my CV</a> or <a href="mailto:{html.escape(PROFILE['email'], quote=True)}">contact me</a>.</p>
  </main>
</body>
</html>
"""


def write_xml(path, tree):
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    with path.open("ab") as handle:
        handle.write(b"\n")


def feed(path, publications=()):
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = f"{NAME}'s publications"
    ET.SubElement(channel, "link").text = BASE + "/"
    ET.SubElement(channel, "description").text = (
        f"Publications by {NAME}." if publications else
        f"This legacy feed is no longer updated. Subscribe to {BASE}/index.xml for publications by {NAME}."
    )
    ET.SubElement(channel, "language").text = "en"
    relative = "/" + path.relative_to(ROOT).as_posix()
    ET.SubElement(channel, f"{{{ATOM}}}link", {
        "href": BASE + relative, "rel": "self", "type": "application/rss+xml",
    })
    if relative != "/index.xml":
        ET.SubElement(channel, f"{{{ATOM}}}link", {
            "href": BASE + "/index.xml", "rel": "related", "type": "application/rss+xml",
        })
    for publication in publications:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = publication["title"]
        url = BASE + publication_path(publication)
        ET.SubElement(item, "link").text = url
        ET.SubElement(item, "guid", {"isPermaLink": "true"}).text = url
        authors = publication.get("authors", [])
        if isinstance(authors, list):
            authors = ", ".join(a if isinstance(a, str) else a.get("name", "") for a in authors)
        description = ". ".join(str(value).rstrip(".") for value in (
            authors, publication.get("venue", ""), publication.get("year", ""),
        ) if value)
        if publication.get("doi"):
            description += f". DOI: {publication['doi']}"
        ET.SubElement(item, "description").text = description + "."
    write_xml(path, ET.ElementTree(rss))


def publication_path(publication):
    for key in ("path", "local_url", "detail_url", "canonical", "canonical_url", "url"):
        value = publication.get(key, "")
        if not isinstance(value, str):
            continue
        parsed = urlparse(value)
        if parsed.netloc and parsed.netloc.lower() != urlparse(BASE).netloc:
            continue
        if parsed.path.startswith("/publication/"):
            return parsed.path.rstrip("/") + "/"
    raise ValueError(f"Missing local publication path: {publication['title']}")


def metadata(publications):
    paths = ["/", "/publication/"] + [publication_path(p) for p in publications]
    if len(set(paths)) != len(paths):
        raise ValueError("Duplicate canonical publication paths")
    sitemap = ET.Element("urlset", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})
    for path in paths:
        entry = ET.SubElement(sitemap, "url")
        ET.SubElement(entry, "loc").text = BASE + path
    write_xml(ROOT / "sitemap.xml", ET.ElementTree(sitemap))
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
    manifest = {
        "name": f"{NAME}'s homepage", "short_name": NAME, "lang": "en",
        "description": f"Research and publications by {NAME}.",
        "theme_color": "#1565c0", "background_color": "#ffffff",
        "icons": [{"src": "/media/site-icon.svg", "sizes": "any", "type": "image/svg+xml"}],
        "display": "standalone", "start_url": "/", "scope": "/",
    }
    (ROOT / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2) + "\n")
    feed(ROOT / "index.xml", publications)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-only", action="store_true", help="Defer metadata until canonical publication data exists.")
    args = parser.parse_args()
    html_count = 0
    feed_count = 0
    for directory in sorted(LEGACY_DIRS):
        for path in sorted((ROOT / directory).rglob("*.html")):
            previous = path.read_text()
            inherited = "wenbin" in previous.lower()
            managed = f"<title>Page moved | {NAME}</title>" in previous
            if not inherited and not managed:
                continue
            path.write_text(redirect_page(*destination(path)))
            html_count += 1
        for path in sorted((ROOT / directory).rglob("index.xml")):
            previous = path.read_text()
            if "wenbin" not in previous.lower() and "This legacy feed is no longer updated." not in previous:
                continue
            feed(path)
            feed_count += 1
    (ROOT / "404.html").write_text(not_found_page())
    if not args.legacy_only:
        data = json.loads((ROOT / "data/publications.json").read_text())
        publications = data if isinstance(data, list) else data["publications"]
        metadata(publications)
    print(f"Updated {html_count} legacy HTML pages, 1 error page, and {feed_count} legacy feeds.")


if __name__ == "__main__":
    main()
