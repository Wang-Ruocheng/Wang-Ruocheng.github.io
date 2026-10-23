#!/usr/bin/env python3
"""Sync a selected PDF, or build a CV from shared profile/publication records.

Run with a Python environment containing reportlab and pypdf:
    python3 scripts/build_cv.py

Profile, education, availability, publication, and honor facts are read from data/.
When profile.cv_source is set, that supplied PDF is copied without rewriting
its contents. Remove this field only when intentionally regenerating the CV.
The research, coursework, and activities below are preserved from the
previous downloadable CV; update these editorial sections here when needed.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/pdf/Ruocheng_Wang_CV.pdf"
DOWNLOAD = ROOT / "authors/admin/CV.pdf"
INK = colors.HexColor("#202936")
ACCENT = colors.HexColor("#184a70")
MUTED = colors.HexColor("#526170")
WIDTH, HEIGHT = A4
MARGIN = 43
CONTENT_WIDTH = WIDTH - 2 * MARGIN

# The previous CV contains no separate technical-skills section. This generator
# preserves the experience claims instead of inventing a new skills inventory.
COURSEWORK = (
    "Mathematical Analysis; Advanced Algebra; Methods of Mathematical Physics; "
    "Classical Mechanics; Quantum Mechanics II (A+); Thermodynamics and "
    "Statistical Physics (99); Electrodynamics (98); Introduction to Computational "
    "Physics (99); Introduction to Nanotechnology (Prof. Nai-Chang Yeh, Caltech)."
)

RESEARCH = [
    {
        "title": "QuanONet: Quantum Neural Operator with Application to Differential Equation",
        "dates": "Jan. 2024 - Present",
        "advisor": "Prof. Junchi Yan, School of Artificial Intelligence, SJTU",
        "bullets": [
            "Proposed QuanONet, a quantum neural operator framework for the NISQ era that approximates continuous nonlinear operators.",
            "Extended the universal approximation theorem to quantum computing; analyzed an implicit effective frame of size O(p<super>2</super>) constructed through the density matrix.",
            "Introduced the adaptive Trainable-Frequency strategy (TF-QuanONet) to improve frequency alignment and the use of the implicit quadratic feature frame.",
            "Evaluated Antiderivative and Diffusion-Reaction benchmarks against DeepONet and FNO, demonstrating competitive accuracy and parameter efficiency.",
            "Deployed the framework on the IBM ibm_fez quantum processor to assess functional viability and resilience to hardware noise.",
        ],
    },
    {
        "title": "Constrained quantum variational circuits for complex optimization problems",
        "dates": "Sept. 2023 - Dec. 2023",
        "advisor": "Prof. Junchi Yan, Department of Computer Science and Engineering, SJTU",
        "bullets": [
            "Analyzed Hamming-weight-preserving ansatzes and dynamical Lie algebras under fully connected and bow-tie conditions, deriving guidance for parameter settings.",
            "Combined Hamming-weight-preserving ansatzes with topology-aware parity checks to enforce hard constraints for the Quadratic Assignment Problem (QAP).",
            "Applied the method to the Travelling Salesman Problem through its QAP formulation; explored reducing redundant state spaces using fewer anyons in topological quantum computing.",
        ],
    },
    {
        "title": "Quantum Langevin equations and frequency locking in periodically driven systems",
        "dates": "Sept. 2022 - Oct. 2023",
        "advisor": "Prof. Carlos Navarrete-Benlloch, School of Physics and Astronomy, SJTU",
        "bullets": [
            "Derived asymptotic solutions and performed stability analysis in the classical limits of feedback-tuned van der Pol (VdP) and degenerate optical parametric oscillator (DOPO) models.",
            "Simulated frequency locking and studied qualitative diagnostics through phase analysis in the complex plane.",
        ],
    },
    {
        "title": "Non-equilibrium and self-organization in hot-spot ignition models",
        "dates": "Sept. 2023 - Feb. 2024",
        "advisor": "Prof. Dong Wu and Prof. Jie Zhang (Academician of CAS), SJTU",
        "bullets": [
            "Extended a non-equilibrium model to isobaric and isochoric conditions with different hot-spot densities and expansion speeds.",
            "Studied self-organization in the bifurcated evolution of ion and electron temperatures and the role of ion-temperature heating in ignition.",
        ],
    },
]

ACTIVITIES = [
    "Chairman of the Student Union of Zhiyuan College.",
    "Participant in the 12-9 Concert representing Zhiyuan College.",
    "Volunteer welcoming 2020 SJTU graduate freshmen.",
]


def register_fonts():
    """Embed an available font family; retain a portable built-in fallback."""
    font_dir = Path("/System/Library/Fonts/Supplemental")
    files = {
        "CVSans": "Arial.ttf",
        "CVSans-Bold": "Arial Bold.ttf",
        "CVSans-Italic": "Arial Italic.ttf",
        "CVSans-BoldItalic": "Arial Bold Italic.ttf",
    }
    if all((font_dir / filename).exists() for filename in files.values()):
        for name, filename in files.items():
            pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
        pdfmetrics.registerFontFamily(
            "CVSans", normal="CVSans", bold="CVSans-Bold",
            italic="CVSans-Italic", boldItalic="CVSans-BoldItalic"
        )
        return "CVSans"
    return "Helvetica"


FONT = register_fonts()
STYLES = {
    "body": ParagraphStyle("body", fontName=FONT, fontSize=9.2, leading=11.7, textColor=INK, spaceAfter=2.2),
    "small": ParagraphStyle("small", fontName=FONT, fontSize=8.7, leading=11, textColor=INK),
    "name": ParagraphStyle("name", fontName=FONT, fontSize=23, leading=28, textColor=INK, alignment=TA_CENTER, spaceAfter=4),
    "contact": ParagraphStyle("contact", fontName=FONT, fontSize=9, leading=12.2, textColor=MUTED, alignment=TA_CENTER),
    "availability": ParagraphStyle("availability", fontName=FONT, fontSize=10, leading=13, textColor=ACCENT, alignment=TA_CENTER, spaceBefore=7, spaceAfter=8),
    "section": ParagraphStyle("section", fontName=FONT, fontSize=11, leading=14, textColor=ACCENT, spaceBefore=9, spaceAfter=5, keepWithNext=True),
    "title": ParagraphStyle("title", fontName=FONT, fontSize=9.4, leading=11.8, textColor=INK, keepWithNext=True),
    "date": ParagraphStyle("date", fontName=FONT, fontSize=8.6, leading=11.8, textColor=MUTED, alignment=TA_RIGHT),
    "advisor": ParagraphStyle("advisor", fontName=FONT, fontSize=8.7, leading=11, textColor=MUTED, spaceAfter=3),
    "pub": ParagraphStyle("pub", fontName=FONT, fontSize=9.2, leading=11.6, textColor=INK, spaceAfter=1.4),
    "bullet": ParagraphStyle("bullet", fontName=FONT, fontSize=9.2, leading=11.7, leftIndent=9, firstLineIndent=-8, textColor=INK, spaceAfter=2.2),
}


def p(text, style="body"):
    return Paragraph(text, STYLES[style])


def section(title):
    return p(f"<b>{escape(title.upper())}</b>", "section")


def title_date(title, date):
    table = Table([[p(f"<b>{escape(title)}</b>", "title"), p(escape(date), "date")]], colWidths=[CONTENT_WIDTH - 120, 120])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return table


def link(label, url):
    return f'<a href="{escape(url, {chr(34): "&quot;"})}" color="#184a70">{escape(label)}</a>'


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d7dfe6"))
    canvas.setLineWidth(0.4)
    canvas.line(MARGIN, 33, WIDTH - MARGIN, 33)
    canvas.setFont(FONT, 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, 21, doc.title)
    canvas.drawRightString(WIDTH - MARGIN, 21, f"{doc.page}")
    canvas.restoreState()


def load_records():
    return (
        json.loads((ROOT / "data/profile.json").read_text()),
        json.loads((ROOT / "data/publications.json").read_text()),
        json.loads((ROOT / "data/honors.json").read_text()),
    )


def build_story(profile, publications, honors_records):
    """Assemble current shared records with the preserved CV experience."""
    def clean(value):
        return str(value).replace("–", "-").replace("—", "-").replace("‑", "-")

    def safe(value):
        return escape(clean(value))

    story = [
        p(f"<b>{safe(profile['name'])}</b>", "name"),
        p(safe(profile["role"]), "contact"),
        p(safe(profile["institution"]), "contact"),
        p(safe(profile["affiliation"]), "contact"),
        p(
            link(profile["email"], "mailto:" + profile["email"])
            + "  |  +86 13851362201  |  "
            + link("Homepage", profile["site_url"]),
            "contact",
        ),
        p(f"<b>{safe(profile['internship']['message'])}</b>", "availability"),
        p("Research interests: " + "; ".join(safe(x) for x in profile["research_interests"]), "contact"),
        section("Education and Training"),
        title_date("Shanghai Jiao Tong University & Shanghai Innovation Institute (SII)", f"{profile['phd_start']} - Present"),
        p("PhD in Computer Science; School of Artificial Intelligence."),
        p("Supervisor: Prof. " + safe(profile["supervisor"]), "advisor"),
        title_date(
            profile["bsc_institution"],
            f"{profile['bsc_start']} - {profile['bsc_end']}" if profile.get("bsc_start") else f"Graduated {profile['bsc_end']}",
        ),
        p("BSc in " + safe(profile["bsc_subject"]) + "; Zhiyuan Honors Program (top 10% in SJTU)."),
        p("<b>Selected coursework:</b> " + escape(COURSEWORK), "small"),
        Spacer(1, 4),
        title_date("Institute of Computing Technology, Chinese Academy of Sciences", "Aug. 2023"),
        p("Quantum Information - Research Internship.", "small"),
        Spacer(1, 3),
        title_date("University of Oxford", "Aug. 2024"),
        p("Advanced English Language and British Culture Programme.", "small"),
        section("Publications"),
        p("<super>*</super> Equal contribution.", "small"),
        Spacer(1, 4),
    ]

    for index, publication in enumerate(publications, 1):
        authors = []
        for author in publication["authors"]:
            shown = safe(author)
            if author == profile["name"]:
                shown = f"<b>{shown}</b>"
            if author in publication.get("equal_contributors", []):
                shown += "<super>*</super>"
            authors.append(shown)

        if publication["type"] == "journal":
            volume = publication.get("volume", "")
            if publication.get("number"):
                volume += f"({publication['number']})"
            venue = f"<i>{safe(publication['venue'])}</i> {safe(volume)}, {safe(publication['pages'])} ({publication['year']})."
        else:
            venue = f"<i>{safe(publication['short_venue'])}</i>"
            if publication.get("distinction"):
                venue += f" (<b>{safe(publication['distinction'])}</b>)"
            if "Machine Learning" in publication["venue"]:
                venue += f"; PMLR {safe(publication['volume'])}: {safe(publication['pages'])}."
            else:
                venue += f"; vol. {safe(publication['volume'])}, pp. {safe(publication['pages'])}."

        links = [link("Paper", publication["url"])]
        if publication.get("doi"):
            links.append(link("DOI: " + publication["doi"], "https://doi.org/" + publication["doi"]))
        links.append(link("BibTeX", profile["site_url"].rstrip("/") + publication["cite_path"]))
        if publication.get("code_url"):
            links.append(link("Code", publication["code_url"]))
        story.append(KeepTogether([
            p(f"<b>[{index}] {safe(publication['title'])}</b>", "pub"),
            p(", ".join(authors) + ".", "pub"),
            p(venue, "pub"),
            p("  |  ".join(links), "small"),
            Spacer(1, 7),
        ]))

    story.extend([PageBreak(), section("Research Experience")])
    for project in RESEARCH:
        elements = [title_date(project["title"], project["dates"]), p("Advisor: " + escape(project["advisor"]), "advisor")]
        elements += [p("- " + item, "bullet") for item in project["bullets"]]
        elements.append(Spacer(1, 5))
        story.append(KeepTogether(elements))

    story.append(p("<b>Teaching Assistant:</b> Quantum Mechanics II, Autumn 2024, Shanghai Jiao Tong University."))
    story.append(section("Selected Honors and Awards"))
    rows = [[p(escape(honor["title"])), p(", ".join(str(year) for year in honor["years"]), "date")] for honor in honors_records]
    honors = Table(rows, colWidths=[CONTENT_WIDTH - 100, 100])
    honors.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
    ]))
    story.append(honors)
    story.append(section("Activities and Engagement"))
    story.extend(p("- " + escape(item), "bullet") for item in ACTIVITIES)
    return story


def main():
    profile, publications, honors = load_records()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if profile.get("cv_source"):
        from pypdf import PdfReader
        source = (ROOT / profile["cv_source"]).resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Selected CV does not exist: {source}")
        page_count = len(PdfReader(source).pages)
        if not page_count:
            raise ValueError("The selected CV has no pages")
        for target in (OUTPUT, DOWNLOAD):
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.resolve() != source:
                shutil.copyfile(source, target)
        print(f"Synced selected {page_count}-page CV unchanged: {source}")
        print(f"Updated stable download: {DOWNLOAD}")
        return
    rl_config.invariant = True
    doc = BaseDocTemplate(
        str(OUTPUT), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=39, bottomMargin=43, title="Ruocheng Wang | Curriculum Vitae",
        author="Ruocheng Wang", subject="Academic CV and PhD research internship availability",
    )
    frame = Frame(MARGIN, 43, CONTENT_WIDTH, HEIGHT - 82, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id="CV", frames=frame, onPage=footer))
    doc.build(build_story(profile, publications, honors))
    from pypdf import PdfReader
    pages = PdfReader(OUTPUT).pages
    if len(pages) != 2:
        raise RuntimeError(f"Expected a two-page CV; generated {len(pages)} pages")
    extracted = re.sub(r"\s+", " ", " ".join(page.extract_text() for page in pages))
    required_text = [
        profile["name"], profile["email"], profile["institution"],
        profile["affiliation"], profile["supervisor"],
        profile["internship"]["message"],
    ] + [publication["title"] for publication in publications] + [honor["title"] for honor in honors]
    missing = [text for text in required_text if re.sub(r"\s+", " ", text) not in extracted]
    if missing:
        raise RuntimeError(f"Missing expected CV text: {missing}")
    shutil.copyfile(OUTPUT, DOWNLOAD)
    print(f"Built {len(pages)} pages: {OUTPUT}")
    print(f"Updated stable download: {DOWNLOAD}")


if __name__ == "__main__":
    main()
