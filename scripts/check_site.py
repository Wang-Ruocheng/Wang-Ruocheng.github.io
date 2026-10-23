#!/usr/bin/env python3
"""Check local HTML links, anchors, metadata, JSON/XML and shared publications."""

from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "data/profile.json").read_text())
SITE_HOST = urlsplit(PROFILE["site_url"]).netloc


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.duplicates = []
        self.links = []
        self.title_count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        identifier = attrs.get("id")
        if identifier:
            if identifier in self.ids:
                self.duplicates.append(identifier)
            self.ids.add(identifier)
        if tag == "title":
            self.title_count += 1
        attribute = "href" if tag in {"a", "link"} else "src" if tag in {"img", "iframe", "script"} else None
        if attribute and attrs.get(attribute):
            self.links.append((self.getpos()[0], attrs[attribute]))
        if tag == "a" and attrs.get("data-filename"):
            self.links.append((self.getpos()[0], attrs["data-filename"]))


def local_target(source, href):
    url = urlsplit(href)
    if url.netloc and url.netloc.lower() != SITE_HOST:
        return None
    if url.scheme and url.scheme not in {"http", "https"}:
        return None
    value = unquote(url.path)
    path = ROOT / value.lstrip("/") if value.startswith("/") else source.parent / value
    path = path.resolve()
    if path.is_dir():
        path /= "index.html"
    return path, unquote(url.fragment)


def main():
    errors = []
    pages = {}
    for source in ROOT.rglob("*.html"):
        if any(part in {".git", "admin", "node_modules", "output"} for part in source.relative_to(ROOT).parts):
            continue
        page = Page()
        text = source.read_text()
        page.feed(text)
        pages[source.resolve()] = page
        if page.duplicates:
            errors.append(f"{source.relative_to(ROOT)}: duplicate ids {page.duplicates}")
        if page.title_count != 1:
            errors.append(f"{source.relative_to(ROOT)}: {page.title_count} title elements")
        if re.search(r"wenbin[\s-]*zhai|wenbinzhai\.github\.io", text, re.I):
            errors.append(f"{source.relative_to(ROOT)}: inherited identity")
    for source, page in pages.items():
        for line, href in page.links:
            target = local_target(source, href)
            if target is None:
                continue
            path, fragment = target
            if not path.exists():
                errors.append(f"{source.relative_to(ROOT)}:{line}: missing {href}")
            elif fragment and path in pages and fragment not in pages[path].ids:
                errors.append(f"{source.relative_to(ROOT)}:{line}: missing anchor {href}")
    for source in [ROOT / "manifest.webmanifest", ROOT / "index.json", *sorted((ROOT / "data").glob("*.json"))]:
        json.loads(source.read_text())
    for source in ROOT.rglob("*.xml"):
        if ".git" not in source.parts:
            ET.parse(source)
    publications = json.loads((ROOT / "data/publications.json").read_text())
    index = json.loads((ROOT / "index.json").read_text())
    for publication in publications:
        detail = ROOT / publication["path"].strip("/") / "index.html"
        citation = ROOT / publication["cite_path"].lstrip("/")
        if not detail.exists() or not citation.exists():
            errors.append(f"Missing page/citation for {publication['id']}")
        if not any(record["title"] == publication["title"] and record["relpermalink"] == publication["path"] for record in index):
            errors.append(f"Missing search entry for {publication['id']}")
    years = [publication["year"] for publication in publications]
    if years != sorted(years, reverse=True):
        errors.append("Selected publications are not ordered by descending year")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"PASS: {len(pages)} HTML pages; local links and anchors; JSON/XML; {len(publications)} publication records and search entries.")


if __name__ == "__main__":
    main()
