#!/usr/bin/env python3
"""Assemble the static site from one layout and a content fragment per page.

Five pages share a head, a navigation bar and a footer. Keeping five hand-written
copies in sync fails the first time someone edits the nav and misses a file, so the
shared shell lives in _layout.html and each page contributes only its body, from
_pages/. Output is plain HTML committed to the repo: GitHub Pages serves it
directly, with no CI and no toolchain on the author's machine.

    python3 build.py            # write the pages
    python3 build.py --check    # fail if the committed output is stale
"""
from pathlib import Path
import html
import sys

ROOT = Path(__file__).resolve().parent
LAYOUT = ROOT / "_layout.html"
PAGES = ROOT / "_pages"

SITE_DESC = ("Ph.D. candidate in Accounting at the University of Maryland's Robert H. Smith "
             "School of Business. Research on AI, generative AI, and financial information in "
             "capital markets. On the 2026–27 academic job market.")

# The person markup belongs on the home page only; repeating it on every page
# gives search engines four competing descriptions of the same person.
PERSON_JSONLD = """    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Person",
      "name": "Leonard Yang Liu",
      "alternateName": "Yang Liu",
      "givenName": "Leonard Yang",
      "familyName": "Liu",
      "jobTitle": "Ph.D. Candidate in Accounting",
      "description": "Ph.D. candidate in Accounting at the University of Maryland's Robert H. Smith School of Business. Research on artificial intelligence, generative AI, and financial information in capital markets.",
      "url": "https://leonardyangliu.com/",
      "image": "https://leonardyangliu.com/images/headshot.jpg",
      "email": "yliu337@umd.edu",
      "worksFor": {
        "@type": "CollegeOrUniversity",
        "name": "University of Maryland, Robert H. Smith School of Business",
        "url": "https://www.rhsmith.umd.edu/"
      },
      "affiliation": {
        "@type": "CollegeOrUniversity",
        "name": "University of Maryland, Robert H. Smith School of Business",
        "url": "https://www.rhsmith.umd.edu/"
      },
      "alumniOf": [
        { "@type": "CollegeOrUniversity", "name": "Peking University HSBC Business School" },
        { "@type": "CollegeOrUniversity", "name": "Huazhong University of Science and Technology" }
      ],
      "knowsAbout": [
        "Accounting", "Financial Accounting", "Generative AI", "Artificial Intelligence",
        "Financial Analysts", "Capital Markets", "Earnings Forecasts"
      ]
    }
    </script>
"""

# Top-level navigation, in the order a visitor should meet it. `key` is matched
# against each page's `nav` field to mark the current item.
NAV = [
    ("about",    "/#about",     "About"),
    ("research", "/#research",  "Research"),
    ("teaching", "/teaching/",  "Teaching"),
    ("hobbies",  "/hobbies/",   "Hobbies"),
    ("cv",       "/cv.pdf",     "CV"),
    ("contact",  "/#contact",   "Contact"),
]

PAGE_LIST = [
    dict(src="index.html", out="index.html", path="/", nav="about",
         title="Leonard Yang Liu — Accounting Ph.D. Candidate, U. Maryland",
         og_title="Leonard Yang Liu — Accounting Ph.D. Candidate, University of Maryland",
         description=("Leonard Yang Liu, Accounting Ph.D. candidate at the University of Maryland "
                      "(Smith). Research on AI and generative AI in capital markets, financial "
                      "analysts, and earnings forecasts. On the 2026–27 job market."),
         head_extra=PERSON_JSONLD, progress=True),

    dict(src="teaching.html", out="teaching/index.html", path="/teaching/", nav="teaching",
         title="Teaching — Leonard Yang Liu",
         og_title="Teaching — Leonard Yang Liu",
         description=("Teaching record of Leonard Yang Liu: instructor of record for Principles of "
                      "Accounting I at the University of Maryland, with course evaluations.")),

    dict(src="hobbies.html", out="hobbies/index.html", path="/hobbies/", nav="hobbies",
         title="Hobbies — Leonard Yang Liu",
         og_title="Hobbies — Leonard Yang Liu",
         description="Two long-running hobbies: building PCs, and Romantic-era classical music."),

    dict(src="pc-building.html", out="hobbies/pc-building/index.html",
         path="/hobbies/pc-building/", nav="hobbies",
         title="PC Building — Leonard Yang Liu",
         og_title="PC Building — Leonard Yang Liu",
         description=("Ten-plus years of building gaming PCs and research workstations, with photos "
                      "of past builds and an open offer of parts advice.")),

    dict(src="classical-music.html", out="hobbies/classical-music/index.html",
         path="/hobbies/classical-music/", nav="hobbies",
         title="Classical Music — Leonard Yang Liu",
         og_title="Classical Music — Leonard Yang Liu",
         description=("At the piano since six, and a Romantic ever since: Rachmaninoff's Second and "
                      "Third Concertos, the Second Symphony, and Beethoven.")),
]


def render_nav(active: str, is_home: bool) -> str:
    """Render the bar, marking the current page.

    Section links point at bare fragments on the home page so the scroll-spy in
    script.js (which selects `.topnav a[href^="#"]`) can find and highlight them,
    and at root-relative fragments elsewhere so they navigate home first. The home
    page therefore carries no aria-current on a section link: which section is
    "current" there depends on scroll position, and the script owns that.
    """
    out = []
    for key, href, label in NAV:
        if is_home and href.startswith("/#"):
            href = href[1:]
        attrs = ' aria-current="page"' if key == active and not href.startswith("#") else ""
        ext = ' target="_blank" rel="noopener"' if href.endswith(".pdf") else ""
        out.append(f'            <a href="{href}"{attrs}{ext}>{label}</a>')
    return "\n".join(out)


def render(page: dict, layout: str) -> str:
    body = (PAGES / page["src"]).read_text(encoding="utf-8").rstrip("\n")
    out = layout
    for token, value in {
        "{{TITLE}}": html.escape(page["title"], quote=True),
        "{{DESCRIPTION}}": html.escape(page["description"], quote=True),
        "{{OG_TITLE}}": html.escape(page["og_title"], quote=True),
        "{{OG_DESCRIPTION}}": html.escape(page.get("og_description", page["description"]), quote=True),
        "{{PATH}}": page["path"],
        "{{HEAD_EXTRA}}": page.get("head_extra", ""),
        # The reading-progress bar earns its place only on the long landing page.
        "{{PROGRESS}}": '<div id="progress" aria-hidden="true"></div>\n' if page.get("progress") else "",
        "{{NAV}}": render_nav(page["nav"], page["path"] == "/"),
        "{{BODY}}": body,
    }.items():
        out = out.replace(token, value)
    if "{{" in out:
        leftover = out[out.index("{{"):out.index("{{") + 40]
        raise SystemExit(f"unreplaced placeholder in {page['out']}: {leftover!r}")
    return out


def main(argv: list[str]) -> int:
    check = "--check" in argv
    layout = LAYOUT.read_text(encoding="utf-8")
    stale = []
    for page in PAGE_LIST:
        rendered = render(page, layout)
        dest = ROOT / page["out"]
        current = dest.read_text(encoding="utf-8") if dest.exists() else None
        if check:
            if current != rendered:
                stale.append(page["out"])
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(rendered, encoding="utf-8")
        print(f"  {'=' if current == rendered else '+'} {page['out']}")
    if check:
        if stale:
            print("stale output, run python3 build.py:\n  " + "\n  ".join(stale), file=sys.stderr)
            return 1
        print("  output is up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
