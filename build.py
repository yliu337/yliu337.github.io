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
# against each page's `nav` field to mark the current item. Hobbies points
# straight at the first hobby: the sub-navigation strip on those pages does the
# switching, so an intermediate landing page would be one click of pure ceremony.
# Contact lives in the footer of every page rather than in the nav.
NAV = [
    ("about",    "/",                     "About"),
    ("research", "/research/",            "Research"),
    ("teaching", "/teaching/",            "Teaching"),
    ("hobbies",  "/hobbies/classical-music/", "Hobbies"),
    ("cv",       "/cv.pdf",               "CV"),
]

# Old URLs that must keep working after the restructure -> where they go now.
REDIRECTS = {
    "hobbies/index.html": "/hobbies/classical-music/",
}

PAGE_LIST = [
    dict(src="index.html", out="index.html", path="/", nav="about",
         title="Leonard Yang Liu — Accounting Ph.D. Candidate, U. Maryland",
         og_title="Leonard Yang Liu — Accounting Ph.D. Candidate, University of Maryland",
         description=("Leonard Yang Liu, Accounting Ph.D. candidate at the University of Maryland "
                      "(Smith). Research on AI and generative AI in capital markets, financial "
                      "analysts, and earnings forecasts. On the 2026–27 job market."),
         head_extra=PERSON_JSONLD),

    dict(src="research.html", out="research/index.html", path="/research/", nav="research",
         title="Research — Leonard Yang Liu",
         og_title="Research — Leonard Yang Liu",
         description=("Research by Leonard Yang Liu on generative AI and financial information in "
                      "capital markets: consensus forecasts, sell-side analysts, crowdsourced "
                      "forecasts, and CFO communication.")),

    dict(src="teaching.html", out="teaching/index.html", path="/teaching/", nav="teaching",
         title="Teaching — Leonard Yang Liu",
         og_title="Teaching — Leonard Yang Liu",
         description=("Teaching record of Leonard Yang Liu: instructor of record for Principles of "
                      "Accounting I at the University of Maryland, with course evaluations.")),

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
         description=("At the piano since six and a classical music fan ever since, drawn above "
                      "all to the Romantic era: Rachmaninoff's Second and Third Concertos, the "
                      "Second Symphony, and Beethoven.")),
]


def render_nav(active: str, path: str) -> str:
    """Render the bar, marking the current page.

    aria-current="page" is only honest when the link's target IS the page being
    viewed; when the link merely belongs to the active section (Hobbies while
    on /hobbies/classical-music/), the correct token is "true".
    """
    out = []
    for key, href, label in NAV:
        if href == path:
            attrs = ' aria-current="page"'
        elif key == active:
            attrs = ' aria-current="true"'
        else:
            attrs = ""
        ext = ' target="_blank" rel="noopener"' if href.endswith(".pdf") else ""
        out.append(f'            <a href="{href}"{attrs}{ext}>{label}</a>')
    return "\n".join(out)


def asset_stamp(layout: str) -> str:
    """Append ?v=<content-hash> to the css/js references in the layout, so a
    republish can never pair a browser-cached old script with a new stylesheet
    (or vice versa): any change to either file changes the URL."""
    import hashlib
    for name in ("styles.css", "script.js"):
        digest = hashlib.md5((ROOT / name).read_bytes()).hexdigest()[:8]
        layout = layout.replace(f'"/{name}"', f'"/{name}?v={digest}"')
    return layout


REDIRECT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url={target}">
    <meta name="robots" content="noindex">
    <link rel="canonical" href="https://leonardyangliu.com{target}">
    <title>Redirecting&hellip;</title>
</head>
<body>
    <p><a href="{target}">This page has moved.</a></p>
</body>
</html>
"""


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
        "{{NAV}}": render_nav(page["nav"], page["path"]),
        "{{BODY}}": body,
    }.items():
        out = out.replace(token, value)
    if "{{" in out:
        leftover = out[out.index("{{"):out.index("{{") + 40]
        raise SystemExit(f"unreplaced placeholder in {page['out']}: {leftover!r}")
    return out


def main(argv: list[str]) -> int:
    check = "--check" in argv
    layout = asset_stamp(LAYOUT.read_text(encoding="utf-8"))
    stale = []
    outputs = [(page["out"], render(page, layout)) for page in PAGE_LIST]
    outputs += [(out, REDIRECT_HTML.format(target=t)) for out, t in REDIRECTS.items()]
    for out_path, rendered in outputs:
        dest = ROOT / out_path
        current = dest.read_text(encoding="utf-8") if dest.exists() else None
        if check:
            if current != rendered:
                stale.append(out_path)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(rendered, encoding="utf-8")
        print(f"  {'=' if current == rendered else '+'} {out_path}")
    if check:
        if stale:
            print("stale output, run python3 build.py:\n  " + "\n  ".join(stale), file=sys.stderr)
            return 1
        print("  output is up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
