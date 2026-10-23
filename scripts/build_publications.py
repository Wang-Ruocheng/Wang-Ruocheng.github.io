#!/usr/bin/env python3
"""Generate static publication pages and RSS from the shared data files.

Run from any directory with: python3 scripts/build_publications.py
No package install or site framework is required. Citation contents are read from
existing .bib files; this script never changes a citation or the homepage.
"""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
import json
from pathlib import Path
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

THEME_INIT = """<script>
try { const mode = localStorage.getItem('wcTheme') || '2';
  document.documentElement.dataset.theme = mode === '1' || (mode === '2' && matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light';
} catch (_) { document.documentElement.dataset.theme = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'; }
</script>"""

BEHAVIOR = """<script>
(() => {
  const theme = document.getElementById('publication-theme');
  const systemTheme = matchMedia('(prefers-color-scheme: dark)');
  let mode = '2';
  try { mode = localStorage.getItem('wcTheme') || '2'; } catch (_) {}
  const applyTheme = () => { document.documentElement.dataset.theme = mode === '1' || (mode === '2' && systemTheme.matches) ? 'dark' : 'light'; };
  theme.value = mode;
  theme.addEventListener('change', () => { mode = theme.value; try { localStorage.setItem('wcTheme', mode); } catch (_) {} applyTheme(); });
  if (systemTheme.addEventListener) systemTheme.addEventListener('change', applyTheme);
  window.addEventListener('storage', event => { if (event.key === 'wcTheme') { mode = event.newValue || '2'; theme.value = mode; applyTheme(); } });
  document.querySelectorAll('.copy-citation').forEach(button => {
    button.addEventListener('click', async () => {
      const citation = button.closest('.citation');
      const text = citation.querySelector('code').textContent;
      const status = citation.querySelector('.copy-status');
      try { await navigator.clipboard.writeText(text); status.textContent = 'BibTeX copied.'; }
      catch (_) { const range = document.createRange(); range.selectNodeContents(citation.querySelector('code')); const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range); status.textContent = 'BibTeX selected. Press Ctrl+C or Command+C to copy.'; }
    });
  });
  const openCitation = () => { if (location.hash) { const target = document.getElementById(decodeURIComponent(location.hash.slice(1))); if (target && target.tagName === 'DETAILS') target.open = true; } };
  openCitation(); window.addEventListener('hashchange', openCitation);
  const search = document.getElementById('publication-search');
  if (search) {
    const year = document.getElementById('publication-year');
    const type = document.getElementById('publication-type');
    const items = [...document.querySelectorAll('.publication-item')];
    const status = document.getElementById('results-status');
    const empty = document.getElementById('empty-state');
    const filter = () => {
      const words = search.value.toLocaleLowerCase().trim().split(/\\s+/).filter(Boolean);
      let visible = 0;
      items.forEach(item => { const match = words.every(word => item.dataset.search.includes(word)) && (!year.value || item.dataset.year === year.value) && (!type.value || item.dataset.type === type.value); item.hidden = !match; if (match) visible++; });
      status.textContent = visible + ' of ' + items.length + ' publications';
      empty.hidden = visible !== 0;
    };
    search.addEventListener('input', filter); year.addEventListener('change', filter); type.addEventListener('change', filter);
    const query = new URLSearchParams(location.search).get('q'); if (query) search.value = query;
    filter();
  }
})();
</script>"""


def h(value: object) -> str:
    return escape(str(value), quote=True)


def load_data() -> tuple[dict, list[dict]]:
    profile = json.loads((ROOT / 'data/profile.json').read_text(encoding='utf-8'))
    source = json.loads((ROOT / 'data/publications.json').read_text(encoding='utf-8'))
    publications = source.get('publications', []) if isinstance(source, dict) else source
    return profile, publications


def author_names(publication: dict) -> list[str]:
    return [a if isinstance(a, str) else a.get('name', '') for a in publication['authors']]


def normalize_publication(raw: dict) -> dict:
    p = dict(raw)
    p['path'] = p.get('path') or p.get('detail_path') or p.get('url')
    if not p['path'] or not p['path'].startswith('/publication/'):
        raise ValueError(f"Publication needs a local /publication/ path: {p.get('id')}")
    p['path'] = p['path'].rstrip('/') + '/'
    p['id'] = p.get('id') or p['path'].strip('/').replace('/', '-')
    p['bib'] = p.get('cite_path') or p.get('bib') or p.get('bibtex') or p.get('citation') or p['path'] + 'cite.bib'
    p['official_url'] = p.get('official_url') or p.get('paper_url') or p.get('paper') or p.get('url') or ''
    p['pdf'] = p.get('pdf') or p.get('pdf_url') or ''
    p['code'] = p.get('code') or p.get('code_url') or ''
    p['equal_contribution'] = p.get('equal_contribution') or p.get('equal_contributors') or []
    p['type'] = {'journal': 'Journal article', 'conference': 'Conference paper', 'preprint': 'Preprint'}.get(p.get('type'), p.get('type') or p.get('kind') or 'Publication')
    p['issue'] = p.get('issue') or p.get('number')
    p['badge'] = p.get('short_venue', p['type']) + (' · ' + p['distinction'] if p.get('distinction') else '')
    p['venue'] = p.get('venue') or p.get('publication') or ''
    if isinstance(p['bib'], dict):
        p['bib'] = p['bib']['path']
    bib_path = ROOT / p['bib'].lstrip('/')
    p['bib_text'] = bib_path.read_text(encoding='utf-8').strip()
    return p


def authors_markup(publication: dict, name: str) -> str:
    equal = publication['equal_contribution']
    if equal is True:
        equal = author_names(publication)[:2]
    output = []
    for author in author_names(publication):
        text = f'<strong>{h(author)}</strong>' if author == name else h(author)
        if author in equal:
            text += '<sup class="author-mark" aria-label="equal contribution">*</sup>'
        output.append(text)
    return ', '.join(output)


def contribution_markup(publication: dict) -> str:
    return '<p class="contribution">* These authors contributed equally.</p>' if publication['equal_contribution'] else ''


def venue_text(p: dict) -> str:
    if p.get('venue_display'):
        return p['venue_display']
    venue = p['venue']
    if p.get('volume'):
        venue += ' ' + str(p['volume'])
        if p.get('issue'):
            venue += '(' + str(p['issue']) + ')'
    if p.get('pages'):
        venue += ', ' + str(p['pages'])
    if p.get('distinction'):
        venue += ' (' + p['distinction'] + ')'
    return venue


def resource_links(p: dict, citation_id: str = 'citation') -> str:
    doi_url = 'https://doi.org/' + p['doi'].removeprefix('https://doi.org/') if p.get('doi') else ''
    links = [('Paper', p['official_url'] if p['official_url'] != doi_url else ''), (p.get('pdf_label', 'PDF'), p['pdf'])]
    if p.get('doi'):
        links.append((p.get('doi_label', 'DOI'), 'https://doi.org/' + p['doi'].removeprefix('https://doi.org/')))
    if p.get('arxiv'):
        arxiv = str(p['arxiv'])
        links.append(('arXiv', arxiv if arxiv.startswith('https://') else 'https://arxiv.org/abs/' + arxiv))
    links.extend([('Code', p['code']), ('Cite', '#' + citation_id)])
    seen = set()
    anchors = []
    for label, url in links:
        if not url or (url in seen and label != 'Cite'):
            continue
        seen.add(url)
        anchors.append(f'<a href="{h(url)}">{h(label)}</a>')
    return '<div class="resource-links" aria-label="Publication resources">' + '\n'.join(anchors) + '</div>'


def citation_markup(p: dict, citation_id: str = 'citation') -> str:
    return f'''<details class="citation" id="{h(citation_id)}">
  <summary>Cite this paper</summary>
  <pre><code>{h(p['bib_text'])}</code></pre>
  <div class="citation-actions"><button class="copy-citation" type="button">Copy BibTeX</button>
  <a href="{h(p['bib'])}" download>Download .bib</a><span class="copy-status" role="status" aria-live="polite"></span></div>
</details>'''


def page(profile: dict, title: str, path: str, description: str, body: str, *, schema: dict | None = None, citation: dict | None = None, noindex: bool = False) -> str:
    name = profile.get('name', 'Ruocheng Wang')
    base_url = profile.get('site_url') or profile.get('base_url') or 'https://wang-ruocheng.github.io/'
    canonical = urljoin(base_url.rstrip('/') + '/', path.lstrip('/'))
    site_title = profile.get('site_title') or name + "'s homepage"
    image = urljoin(base_url, profile.get('social_image') or '/wrc.png')
    citation_meta = ''
    if citation:
        fields = [('citation_title', citation['title']), ('citation_publication_date', citation['year'])]
        fields.extend(('citation_author', author) for author in author_names(citation))
        fields.append(('citation_journal_title' if citation['type'] == 'Journal article' else 'citation_conference_title', citation['venue']))
        for field, key in [('citation_doi', 'doi'), ('citation_volume', 'volume'), ('citation_issue', 'issue')]:
            if citation.get(key): fields.append((field, citation[key]))
        if citation.get('pdf'):
            fields.append(('citation_pdf_url', urljoin(base_url, citation['pdf'])))
        citation_meta = '\n  '.join(f'<meta name="{h(key)}" content="{h(value)}">' for key, value in fields)
    structured = json.dumps(schema or {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': title, 'url': canonical}, ensure_ascii=False).replace('</', '<\\/')
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="author" content="{h(name)}">
  <meta name="description" content="{h(description)}">
  <meta name="theme-color" content="#155ab6">
  {'<meta name="robots" content="noindex, follow">' if noindex else ''}
  <title>{h(title)} | {h(site_title)}</title>
  <link rel="canonical" href="{h(canonical)}">
  <link rel="icon" href="/media/site-icon.svg" type="image/svg+xml">
  <link rel="manifest" href="/manifest.webmanifest">
  <link rel="alternate" type="application/rss+xml" href="/publication/index.xml" title="{h(name)} — Publications">
  <meta property="og:type" content="{'article' if schema and schema.get('@type') == 'ScholarlyArticle' else 'website'}">
  <meta property="og:site_name" content="{h(site_title)}">
  <meta property="og:title" content="{h(title)}">
  <meta property="og:description" content="{h(description)}">
  <meta property="og:url" content="{h(canonical)}">
  <meta property="og:image" content="{h(image)}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{h(title)}">
  <meta name="twitter:description" content="{h(description)}">
  <meta name="twitter:image" content="{h(image)}">
  {citation_meta}
  {THEME_INIT}
  <link rel="stylesheet" href="/css/publications.css">
  <script type="application/ld+json">{structured}</script>
</head>
<body>
<a class="skip-link" href="#main-content">Skip to content</a>
<header class="site-header"><div class="header-inner">
  <a class="brand" href="/">{h(name)}</a>
  <nav class="site-nav" aria-label="Main navigation">
    <a href="/">Home</a><a href="/publication/" {'aria-current="page"' if path == '/publication/' else ''}>Publications</a><a href="/#contact">Contact</a>
    <label><span class="visually-hidden" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)">Color theme</span>
    <select class="theme-select" id="publication-theme" aria-label="Color theme"><option value="2">Auto theme</option><option value="0">Light theme</option><option value="1">Dark theme</option></select></label>
  </nav>
</div></header>
<main id="main-content">{body}</main>
<footer class="site-footer"><p>© {h(name)}. <a href="/">Homepage</a> · <a href="/publication/index.xml">Publication RSS</a></p></footer>
{BEHAVIOR}
</body>
</html>
'''


def detail_page(profile: dict, p: dict, *, additional: bool = False) -> str:
    name = profile.get('name', 'Ruocheng Wang')
    base_url = profile.get('site_url') or profile.get('base_url') or 'https://wang-ruocheng.github.io/'
    description = f"{p['title']}. {', '.join(author_names(p))}. {venue_text(p)}, {p['year']}."
    rows = [('Year', str(p['year'])), ('Type', p['type']), ('Venue', venue_text(p))]
    for key, label in [('volume', 'Volume'), ('issue', 'Issue'), ('pages', 'Pages')]:
        if p.get(key): rows.append((label, str(p[key])))
    metadata = ''.join(f'<dt>{h(key)}</dt><dd>{h(value)}</dd>' for key, value in rows)
    if p.get('doi'):
        metadata += f'<dt>DOI</dt><dd><a href="https://doi.org/{h(p["doi"])}">{h(p["doi"])}</a></dd>'
    note = f'<p class="section-note">{h(p["note"])}</p>' if p.get('note') else ''
    abstract = f'<section><h2>Abstract</h2><p>{h(p["abstract"])}</p></section>' if p.get('abstract') else ''
    if additional:
        note += '<p class="section-note">Additional preprint. See the <a href="/publication/">publication archive</a> for selected publications.</p>'
    body = f'''<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/publication/">Publications</a></nav>
<article>
<header class="article-header">
  <p class="eyebrow">{h(p['type'])} · {h(p['year'])}</p>
  <h1>{h(p['title'])}</h1>
  <p class="authors">{authors_markup(p, name)}</p>
  {contribution_markup(p)}
  <p class="venue">{h(venue_text(p))}</p>
  {resource_links(p)}
</header>
<div class="article-body">{note}{abstract}<h2>Publication details</h2><dl class="metadata">{metadata}</dl>
<h2>Citation</h2>{citation_markup(p)}</div>
</article>'''
    schema = {'@context': 'https://schema.org', '@type': 'ScholarlyArticle', 'headline': p['title'], 'name': p['title'], 'author': [{'@type': 'Person', 'name': a} for a in author_names(p)], 'datePublished': str(p.get('date') or p['year']), 'url': urljoin(base_url, p['path']), 'isPartOf': {'@type': 'Periodical' if 'journal' in p['type'].lower() else 'CreativeWork', 'name': p['venue']}}
    if p.get('doi'): schema['sameAs'] = 'https://doi.org/' + p['doi']
    if p.get('pages'): schema['pagination'] = p['pages']
    if p.get('volume'): schema['volumeNumber'] = p['volume']
    if p.get('issue'): schema['issueNumber'] = p['issue']
    return page(profile, p['title'], p['path'], description, body, schema=schema, citation=p)


def archive_page(profile: dict, publications: list[dict]) -> str:
    name = profile.get('name', 'Ruocheng Wang')
    years = sorted({str(p['year']) for p in publications}, reverse=True)
    types = sorted({p['type'] for p in publications})
    options = lambda values: ''.join(f'<option value="{h(v)}">{h(v)}</option>' for v in values)
    cards = []
    for p in publications:
        citation_id = 'cite-' + p['id']
        search = ' '.join([p['title'], *author_names(p), venue_text(p), str(p['year']), p['type'], *p.get('search_aliases', [])]).lower()
        cards.append(f'''<li class="publication-item" data-year="{h(p['year'])}" data-type="{h(p['type'])}" data-search="{h(search)}"><article class="publication-card">
  <span class="pub-label">{h(p.get('badge') or p['type'])} · {h(p['year'])}</span>
  <h2><a href="{h(p['path'])}">{h(p['title'])}</a></h2>
  <p class="authors">{authors_markup(p, name)}</p>{contribution_markup(p)}
  <p class="venue">{h(venue_text(p))}</p>
  {resource_links(p, citation_id)}{citation_markup(p, citation_id)}
</article></li>''')
    body = f'''<p class="eyebrow">Research</p><h1>Publications</h1>
<p class="intro">Selected research papers by {h(name)}. Browse the papers, follow official publication links, or download citations in BibTeX format.</p>
<div class="filters" role="search" aria-label="Filter publications">
  <label class="filter filter-search" for="publication-search">Search papers<input id="publication-search" type="search" placeholder="Title, author, or venue" autocomplete="off"></label>
  <label class="filter" for="publication-year">Year<select id="publication-year"><option value="">All years</option>{options(years)}</select></label>
  <label class="filter" for="publication-type">Publication type<select id="publication-type"><option value="">All types</option>{options(types)}</select></label>
</div><output class="results-status" id="results-status" aria-live="polite">{len(publications)} publications</output>
<ul class="publication-list">{''.join(cards)}</ul><p class="empty-state" id="empty-state" hidden>No publications match these filters. Try another title, author, or venue.</p>'''
    return page(profile, 'Publications', '/publication/', f'Selected publications by {name}, including official papers, DOI links, and BibTeX citations.', body)


def redirect_page(profile: dict, source_path: str) -> str:
    name = profile.get('name', 'Ruocheng Wang')
    base_url = profile.get('site_url') or profile.get('base_url') or 'https://wang-ruocheng.github.io/'
    target = urljoin(base_url, '/publication/')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, follow"><meta http-equiv="refresh" content="0; url=/publication/">
<link rel="canonical" href="{h(target)}"><link rel="icon" href="/media/site-icon.svg" type="image/svg+xml"><title>Publications | {h(name)}</title>
<link rel="stylesheet" href="/css/publications.css">{THEME_INIT}</head>
<body><main><h1>Publications</h1><p>Continue to <a href="/publication/">{h(name)}’s publication archive</a>.</p></main></body></html>
'''


def write_rss(profile: dict, publications: list[dict]) -> None:
    base_url = profile.get('site_url') or profile.get('base_url') or 'https://wang-ruocheng.github.io/'
    name = profile.get('name', 'Ruocheng Wang')
    ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
    rss = ET.Element('rss', {'version': '2.0'})
    channel = ET.SubElement(rss, 'channel')
    for tag, text in [('title', name + ' — Publications'), ('link', urljoin(base_url, '/publication/')), ('description', 'Selected research publications by ' + name), ('language', 'en')]: ET.SubElement(channel, tag).text = text
    ET.SubElement(channel, '{http://www.w3.org/2005/Atom}link', {'href': urljoin(base_url, '/publication/index.xml'), 'rel': 'self', 'type': 'application/rss+xml'})
    for p in publications:
        item = ET.SubElement(channel, 'item')
        link = urljoin(base_url, p['path'])
        description = ', '.join(author_names(p)) + '. ' + venue_text(p) + ', ' + str(p['year']) + '.'
        for tag, text in [('title', p['title']), ('link', link), ('guid', link), ('description', description)]: ET.SubElement(item, tag).text = text
        date = p.get('date')
        if date and len(str(date)) >= 10:
            try:
                parsed = datetime.fromisoformat(str(date).replace('Z', '+00:00'))
                if parsed.tzinfo is None: parsed = parsed.replace(tzinfo=timezone.utc)
                ET.SubElement(item, 'pubDate').text = format_datetime(parsed)
            except ValueError: pass
    ET.indent(rss, space='  ')
    ET.ElementTree(rss).write(ROOT / 'publication/index.xml', encoding='utf-8', xml_declaration=True)


def write_html(destination: Path, content: str) -> None:
    destination.write_text('\n'.join(line.rstrip() for line in content.splitlines()) + '\n', encoding='utf-8')


def main() -> None:
    profile, raw_publications = load_data()
    publications = [normalize_publication(p) for p in raw_publications]
    owned_paths = set()
    for p in publications:
        destination = ROOT / p['path'].lstrip('/') / 'index.html'
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_html(destination, detail_page(profile, p))
        owned_paths.add(destination)
    archive = ROOT / 'publication/index.html'
    write_html(archive, archive_page(profile, publications))
    owned_paths.add(archive)
    additional_path = ROOT / 'publication/preprint/uhwp/index.html'
    if additional_path not in owned_paths:
        additional = normalize_publication({'id': 'uhwp', 'title': 'Universal Hamming Weight Preserving Variational Quantum Ansatz', 'authors': ['Ge Yan', 'Kaisen Pan', 'Ruocheng Wang', 'Mengfei Ran', 'Hongxu Chen', 'Xunuo Wang', 'Junchi Yan'], 'year': 2024, 'type': 'Preprint', 'venue': 'arXiv:2412.04825', 'path': '/publication/preprint/uhwp/', 'bib': '/publication/preprint/uhwp/cite.bib', 'pdf': '/publication/preprint/uhwp/uhwp.pdf', 'official_url': 'https://arxiv.org/abs/2412.04825'})
        write_html(additional_path, detail_page(profile, additional, additional=True))
        owned_paths.add(additional_path)
    redirects = []
    legacy_routes = [
        '/publication/conference-paper/', '/publication/journal-article/',
        '/publication/preprint/', '/publication/thesis/postgraduatethesis/',
        '/publication/thesis/undergraduatethesis/',
    ]
    for source_path in legacy_routes:
        destination = ROOT / source_path.lstrip('/') / 'index.html'
        if destination in owned_paths: continue
        write_html(destination, redirect_page(profile, source_path))
        redirects.append(source_path)
    write_rss(profile, publications)
    print(f'Generated {len(publications)} selected publication details, publication archive and RSS; preserved UHWP; redirected {len(redirects)} legacy routes.')
    for p in publications: print(p['path'])
    for path in redirects: print('redirect: ' + path)


if __name__ == '__main__':
    main()
