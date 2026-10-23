#!/usr/bin/env python3
"""Sync the static homepage and Wowchemy search index from data/*.json.

Run from any directory with Python 3. No third-party packages are needed.
Publication pages and the CV have separate builders in this directory.
"""

from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read_json(name):
    return json.loads((ROOT / "data" / name).read_text())


def section(document, section_id, replacement):
    pattern = rf'<section\b[^>]*\bid="{re.escape(section_id)}"[^>]*>.*?</section>'
    result, count = re.subn(pattern, lambda _: replacement, document, count=1, flags=re.S)
    if count != 1:
        raise ValueError(f"Missing homepage section: {section_id}")
    return result


def author_html(publication, name):
    authors = []
    for author in publication["authors"]:
        label = escape(author)
        if author in publication.get("equal_contributors", []):
            label += '<sup title="Equal contribution">*</sup>'
        if author == name:
            label = f'<span class="author-highlighted">{label}</span>'
        authors.append(label)
    return ", ".join(authors)


def pub_buttons(publication):
    button = 'class="btn btn-outline-primary btn-page-header btn-sm"'
    links = []
    if publication.get("pdf_url"):
        links.append(f'<a {button} href="{escape(publication["pdf_url"], quote=True)}" target="_blank" rel="noopener">{escape(publication.get("pdf_label", "PDF"))}</a>')
    links.append(f'<a href="#" class="btn btn-outline-primary btn-page-header btn-sm js-cite-modal" data-filename="{publication["cite_path"]}">Cite</a>')
    links.append(f'<a {button} href="{escape(publication["url"], quote=True)}" target="_blank" rel="noopener">Paper</a>')
    if publication.get("doi"):
        links.append(f'<a {button} href="https://doi.org/{publication["doi"]}" target="_blank" rel="noopener">DOI</a>')
    if publication.get("code_url"):
        links.append(f'<a {button} href="{publication["code_url"]}" target="_blank" rel="noopener">Code</a>')
    return "\n".join(links)


def publication_section(publications, profile):
    cards = []
    for publication in publications:
        venue = escape(publication["short_venue"])
        if publication.get("distinction"):
            venue += f' ({escape(publication["distinction"])})'
        contribution = '<div class="article-metadata"><sup>*</sup> Equal contribution.</div>' if publication.get("equal_contributors") else ""
        cards.append(f'''<div class="pub-list-item view-citation" style="margin-bottom: 1.5rem" id="pub-{publication['id']}">
  <i class="far fa-file-alt pub-icon" aria-hidden="true"></i>
  <span class="article-metadata li-cite-author">{author_html(publication, profile['name'])}</span>
  ({publication['year']}).
  <a href="{publication['path']}">{escape(publication['title'])}</a>.
  <em><strong>{venue}</strong></em>.
  {contribution}
  <p class="publication-links">{pub_buttons(publication)}</p>
</div>''')
    return '''<section id="publications" class="home-section publications">
  <div class="home-section-bg"></div>
  <div class="container"><div class="row">
    <div class="section-heading col-12 col-lg-4 mb-3 mb-lg-0">
      <h1>Publications</h1>
      <p><a href="/publication/">Browse all publications</a></p>
    </div>
    <div class="col-12 col-lg-8">
''' + "\n".join(cards) + '''
    </div>
  </div></div>
</section>'''


def news_section(news):
    entries = []
    for item in news:
        url = escape(item["url"], quote=True)
        external = ' target="_blank" rel="noopener"' if url.startswith("https://") else ""
        entries.append(f'<li><time datetime="{item["date"]}">{item["date"]}</time><a href="{url}"{external}>{escape(item["text"])}</a></li>')
    return '''<section id="news" class="home-section wg-markdown">
  <div class="home-section-bg"></div>
  <div class="container"><div class="row">
    <div class="section-heading col-12 col-lg-4 mb-3 mb-lg-0"><h1>Recent News</h1></div>
    <div class="col-12 col-lg-8"><ul class="news-list">
''' + "\n".join(entries) + '''
    </ul></div>
  </div></div>
</section>'''


def honors_section(honors):
    rows = []
    for honor in honors:
        years = ", ".join(str(year) for year in sorted(honor["years"], reverse=True))
        rows.append(f'<p><strong>[{years}]</strong> {escape(honor["title"])}</p>')
    return '''<section id="honors" class="home-section wg-markdown">
  <div class="home-section-bg"></div>
  <div class="container"><div class="row">
    <div class="section-heading col-12 col-lg-4 mb-3 mb-lg-0"><h1>Honors and Awards</h1></div>
    <div class="col-12 col-lg-8">
''' + "\n".join(rows) + '''
    </div>
  </div></div>
</section>'''


def about_section(document, profile):
    match = re.search(r'<section\b[^>]*\bid="about"[^>]*>.*?</section>', document, re.S)
    if not match:
        raise ValueError("Missing about section")
    about = match.group()
    about = re.sub(r'<head>.*?</head>', '', about, flags=re.S)
    about = re.sub(r'<!--.*?-->', '', about, flags=re.S)
    portrait = f'''<div class="portrait-title">
        <h2>{escape(profile['name'])}</h2>
        <h3>PhD Student</h3>
        <h3><a href="https://soai.sjtu.edu.cn" target="_blank" rel="noopener">School of Artificial Intelligence, SJTU</a></h3>
        <h3>{escape(profile['affiliation'])}</h3>
      </div>'''
    about, count = re.subn(r'<div class="portrait-title">.*?</div>', lambda _: portrait, about, count=1, flags=re.S)
    if count != 1:
        raise ValueError("Missing profile title")
    internship = profile["internship"]
    details = []
    if internship.get("directions"):
        details.append("Areas: " + ", ".join(internship["directions"]) + ".")
    if internship.get("start"):
        details.append("Available from " + internship["start"] + ".")
    if internship.get("duration"):
        details.append("Duration: " + internship["duration"] + ".")
    extra = " ".join(escape(value) for value in details)
    biography = f'''<div class="article-style">
      <p class="alert alert-info" id="contact">
        <strong>{escape(internship['message'])}</strong>
        {extra}
        Please contact me at <a class="alert-link" href="mailto:{profile['email']}">{profile['email']}</a>.
      </p>
      <p>I am a PhD student in Computer Science at the <a href="https://soai.sjtu.edu.cn" target="_blank" rel="noopener">School of Artificial Intelligence, Shanghai Jiao Tong University</a> and {escape(profile['affiliation'])}, supervised by <a href="{profile['supervisor_url']}" target="_blank" rel="noopener">Professor {escape(profile['supervisor'])}</a>.</p>
      <p>My research focuses on quantum algorithms and machine learning, with applications to differential equations and quantum chemistry. My recent work includes <a href="/publication/journal-article/nmi-quanonet/">quantum neural operators</a> and <a href="/publication/conference-paper/icml-coevol-no/">neural operator learning</a>.</p>
      <p>I received my BSc in Physics from Zhiyuan College, Shanghai Jiao Tong University, in {profile['bsc_end']}.</p>
      <details class="personal-background">
        <summary>Personal background</summary>
        <p>I am from Suqian, Jiangsu. I attended Huaiyin Middle School from 2016 to 2019 and joined the Jiangsu provincial Physics Olympiad team in 2018.</p>
      </details>
    </div>'''
    about, count = re.subn(r'<div class="article-style">.*?</div>', lambda _: biography, about, count=1, flags=re.S)
    if count != 1:
        raise ValueError("Missing biography")
    start = profile.get("bsc_start")
    bsc_dates = f"{start}–{profile['bsc_end']}" if start else str(profile["bsc_end"])
    about = re.sub(r'<p class="course">BSc.*?</p>', f'<p class="course">BSc in Physics, {bsc_dates}</p>', about)
    about = about.replace("Education Experience", "Education")
    return section(document, "about", about)


def search_record(title, content, path, record_type="page", authors=None, tags=None):
    return {
        "title": title, "summary": content[:300], "content": content,
        "authors": authors or [], "tags": tags or [], "categories": [],
        "type": record_type, "kind": "page", "section": record_type,
        "relpermalink": path, "permalink": PROFILE["site_url"] + path,
        "objectID": path, "lang": "en", "date": 0, "lastmod": 0,
    }


def make_search_index(profile, publications, news, honors):
    biography = (f"{profile['name']} {profile['name_zh']}. {profile['role']}, "
                 f"{profile['institution']} and {profile['affiliation']}. "
                 f"Supervisor: {profile['supervisor']}. "
                 + ", ".join(profile["research_interests"]) + ". "
                 + profile["internship"]["message"] + " " + profile["email"])
    records = [search_record(profile["name"], biography, "/#about", "authors", [profile["name"]])]
    for publication in publications:
        content = (publication["title"] + ". " + ", ".join(publication["authors"]) + ". "
                   + publication["venue"] + f" ({publication['year']}). "
                   + publication.get("distinction", "") + " " + (publication.get("doi") or ""))
        tags = [publication["short_venue"], publication["type"], *publication.get("search_aliases", [])]
        records.append(search_record(publication["title"], content, publication["path"], "publication", publication["authors"], tags))
    additional = ROOT / "publication/preprint/uhwp/index.html"
    if additional.exists() and "Universal Hamming Weight Preserving Variational Quantum Ansatz" in additional.read_text():
        records.append(search_record("Universal Hamming Weight Preserving Variational Quantum Ansatz", "Ge Yan, Kaisen Pan, Ruocheng Wang, Mengfei Ran, Hongxu Chen, Xunuo Wang, Junchi Yan. arXiv:2412.04825 (2024). Additional preprint.", "/publication/preprint/uhwp/", "publication", ["Ge Yan", "Kaisen Pan", "Ruocheng Wang", "Mengfei Ran", "Hongxu Chen", "Xunuo Wang", "Junchi Yan"], ["Preprint", "Quantum Algorithms"]))
    records.append(search_record("Recent News", " ".join(item["date"] + ": " + item["text"] for item in news), "/#news"))
    honor_text = " ".join(honor["title"] + " (" + ", ".join(map(str, honor["years"])) + ")." for honor in honors)
    records.append(search_record("Honors and Awards", honor_text, "/#honors"))
    records.append(search_record("Curriculum Vitae", f"{profile['name']} CV. PhD research internship. Education, publications, research experience and awards.", "/authors/admin/CV.pdf"))
    (ROOT / "index.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    PROFILE = read_json("profile.json")
    publications = read_json("publications.json")
    news = read_json("news.json")
    honors = read_json("honors.json")
    path = ROOT / "index.html"
    document = path.read_text()
    document = about_section(document, PROFILE)
    document = section(document, "news", news_section(news))
    document = section(document, "publications", publication_section(publications, PROFILE))
    document = section(document, "honors", honors_section(honors))
    document = re.sub(r'<li class="nav-item">\s*<a[^>]*href="/#posts".*?</a>\s*</li>', '', document, flags=re.S)
    document = document.replace("Research intern till now", "PhD supervisor (2025–present)")
    document = re.sub(r'<script src="https://polyfill\.io/[^\"]*"></script>\s*', '', document)
    document = re.sub(r'<script src="https://cdn\.jsdelivr\.net/gh/(?:krisk/Fuse|julmot/mark\.js)[^\"]*"[^>]*></script>\s*', '', document)
    document = re.sub(r'\n?[ \t]*<script src="/js/site-search\.js" defer></script>[ \t]*\n?', '', document)
    document = document.replace('</body>', '\n  <script src="/js/site-search.js" defer></script>\n</body>', 1)
    document = re.sub(r'<!--(?:(?!-->).)*(?:Wenbin|wenbin)(?:(?!-->).)*-->', '', document, flags=re.S)
    document = re.sub(r'<meta property="twitter:(?:site|creator)"[^>]*>\s*', '', document)
    document = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="Ruocheng Wang, PhD student at SJTU and SII. Research in quantum algorithms, machine learning and neural operators. Seeking PhD research internships." />', document)
    document = re.sub(r'<meta property="og:updated_time"[^>]*>', f'<meta property="og:updated_time" content="{PROFILE["updated"]}T00:00:00+08:00" />', document)
    document = document.replace('https://Wang-Ruocheng.github.io/', PROFILE["site_url"] + '/')
    document = re.sub(r'<!--\s*<meta property="og:description".*?-->', '', document, flags=re.S)
    if '<meta property="og:description"' not in document:
        document = document.replace('<meta property="og:site_name"', '<meta property="og:description" content="PhD student at Shanghai Jiao Tong University and Shanghai Innovation Institute. Quantum algorithms, machine learning and neural operators." />\n<meta property="og:image" content="' + PROFILE["site_url"] + '/authors/admin/wrc_ox.jpg" />\n<meta property="og:locale" content="en_US" />\n<meta property="og:site_name"', 1)
    document = re.sub(r'<link rel="icon" href="wrc.png" type="image/png">', '<link rel="icon" href="/media/site-icon.svg" type="image/svg+xml">', document)
    document = re.sub(r'^[ \t]*<link rel="stylesheet" href="/?css/styles\.css">[ \t]*\n?', '', document, flags=re.M)
    document = document.replace('</head>', '  <link rel="stylesheet" href="/css/styles.css">\n</head>', 1)
    document = re.sub(r'© \d{4} Ruocheng Wang', f'© {PROFILE["updated"][:4]} Ruocheng Wang', document)
    document = document.replace('Zhiyuan Outstanding Leader Scholarship (</strong>First prize</strong>)', 'Zhiyuan Outstanding Leader Scholarship (First prize)')
    document = "\n".join(line.rstrip() for line in document.splitlines()) + "\n"
    path.write_text(document)
    make_search_index(PROFILE, publications, news, honors)
    (ROOT / "newslist.dat").write_text("\n".join(f'[{item["date"]}] {item["text"]} {item["url"]}' for item in news) + "\n")
    (ROOT / "honorslist.dat").write_text("\n".join(f'[{", ".join(map(str, honor["years"]))}] {honor["title"]}' for honor in honors) + "\n")
    print(f"Updated homepage and search index: {len(publications)} selected publications.")
