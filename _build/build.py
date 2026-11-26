#!/usr/bin/env python3
"""Build the Strip Club Etiquette website from the Markdown guides and CSV data.

Run from the repository root:

    pip install -r _build/requirements.txt
    python3 _build/build.py

The site is written to _site/. Every page is static HTML that works without
JavaScript. Edit the Markdown and CSV files, not the generated HTML.
"""

import csv
import html
import re
import shutil
from collections import Counter, OrderedDict
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
STATIC = Path(__file__).resolve().parent / "static"

# ---------------------------------------------------------------------------
# Settings. Fill these in at launch.
# ---------------------------------------------------------------------------
SITE_NAME = "Strip Club Etiquette"
# Full address of the live site with no trailing slash, such as
# "https://stripclubetiquette.org". Leave empty until there is one: it turns on
# canonical links and the sitemap.
SITE_URL = ""
# GoatCounter site code, such as "stripclubetiquette" for
# stripclubetiquette.goatcounter.com. Leave empty to build with no counter.
GOATCOUNTER = ""
# Where corrections go. The issues page works once the repository is public.
CONTACT_EMAIL = ""
REPO_URL = "https://github.com/travisvought-byte/stripclubettiquette"

# ---------------------------------------------------------------------------
# Pages made from Markdown files: source -> (output, short label, icon)
# ---------------------------------------------------------------------------
MD_PAGES = OrderedDict([
    ("guides/etiquette.md", ("etiquette.html", "Etiquette", "person")),
    ("guides/for-dancers.md", ("dancers.html", "For dancers", "heart")),
    ("guides/human-trafficking.md", ("trafficking.html", "Stop trafficking", "shield")),
    ("guides/for-club-operators.md", ("operators.html", "For clubs", "building")),
    ("guides/how-strip-clubs-work.md", ("how-clubs-work.html", "How clubs work", "dollar")),
    ("guides/laws-by-state.md", ("laws.html", "Laws by state", "scale")),
    ("standards/club-safety-standard.md", ("standard.html", "Safety standard", "checkbox")),
    ("METHODOLOGY.md", ("method.html", "How we rate", "search")),
    ("data/README.md", ("data.html", "Data files", "file")),
    ("research/national.md", ("coverage.html", "Coverage", "map")),
    ("research/ohio.md", ("ohio.html", "Ohio notes", "map")),
])

# Other repository paths that links may point to.
LINK_MAP = {
    "README.md": "index.html",
    "data/clubs.csv": "directory.html",
    "data/evidence.csv": "records.html",
}

# Titles for pages, used when a link's text is a bare file name such as "laws-by-state.md".
PAGE_TITLES = {"index.html": "the home page", "directory.html": "the club directory",
               "records.html": "the public records"}
for _src, (_out, _label, _icon) in MD_PAGES.items():
    _m = re.search(r"^# (.+)$", (ROOT / _src).read_text(encoding="utf-8"), re.M)
    PAGE_TITLES[_out] = _m.group(1).strip() if _m else _label

# Anchors that exist on GitHub but not on the site (sections left off the site).
DROP_ANCHORS = {("research/ohio.md", "open-leads")}

# Sections left off the published page, by source file and heading text.
SKIP_SECTIONS = {"research/ohio.md": {"Open leads"}}

NAV = [
    ("etiquette.html", "Etiquette"),
    ("dancers.html", "Dancers"),
    ("trafficking.html", "Trafficking"),
    ("directory.html", "Directory"),
    ("laws.html", "Laws"),
    ("operators.html", "For clubs"),
    ("about.html", "About"),
]

STATUS = OrderedDict([
    ("verified", ("Verified open", "check-circle", "ok")),
    ("reported-open", ("Reported open", "dot-circle", "info")),
    ("unverified", ("Not yet confirmed", "dash-circle", "muted")),
    ("unknown", ("Status unknown", "question", "warn")),
    ("closed", ("Closed", "x-circle", "muted")),
])

FLAG = OrderedDict([
    ("not-reviewed", ("Not reviewed", "minus-circle", "muted")),
    ("none-found", ("Nothing found", "check-circle", "ok")),
    ("concern", ("Concern", "alert", "warn")),
    ("serious", ("Serious", "octagon", "bad")),
])

DIMENSION = {
    "dancer-pay": "Dancer pay",
    "safety": "Safety",
    "licensing": "Legal and licensing",
    "trafficking": "Trafficking",
    "customer": "Customer fairness",
    "status": "Open or closed",
}

RECORD_TYPE = {
    "allegation": "Allegation",
    "government-action": "Government action",
    "finding": "Finding",
    "settlement": "Settlement",
    "conviction": "Conviction",
    "incident": "Incident",
    "closure": "Closure",
    "positive": "Positive",
}

SOURCE_TYPE = {
    "court": "court record",
    "agency": "government agency",
    "company-filing": "company filing",
    "news": "news",
    "settlement-notice": "settlement notice",
}

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "PR": "Puerto Rico", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

e = html.escape


def icon(name, cls="ic"):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" '
            f'focusable="false"><use href="assets/icons.svg#{name}"/></svg>')


def badge(text, icon_name, tone):
    return f'<span class="badge {tone}">{icon(icon_name)}<span>{e(text)}</span></span>'


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def read_csv(rel):
    with open(ROOT / rel, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


CLUBS = read_csv("data/clubs.csv")
EVIDENCE = read_csv("data/evidence.csv")
CLUB_BY_ID = {c["id"]: c for c in CLUBS}
RECORDS_BY_CLUB = OrderedDict()
for rec in EVIDENCE:
    RECORDS_BY_CLUB.setdefault(rec["club_id"], []).append(rec)


# ---------------------------------------------------------------------------
# Markdown to HTML
# ---------------------------------------------------------------------------

def strip_sections(text, titles):
    """Remove level-2 sections whose heading text is in titles."""
    if not titles:
        return text
    out, skipping = [], False
    for line in text.splitlines(keepends=True):
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m:
            skipping = m.group(1) in titles
        if not skipping:
            out.append(line)
    return "".join(out)


def resolve(src_rel, href):
    """Turn a repository-relative link in src_rel into a site link."""
    if re.match(r"^[a-z]+:", href) or href.startswith("#"):
        return href
    path, _, anchor = href.partition("#")
    target = (Path(src_rel).parent / path).as_posix()
    parts = []
    for p in target.split("/"):
        if p == "..":
            if parts:
                parts.pop()
        elif p and p != ".":
            parts.append(p)
    target = "/".join(parts)
    if target in MD_PAGES:
        page = MD_PAGES[target][0]
    elif target in LINK_MAP:
        page = LINK_MAP[target]
    else:
        raise SystemExit(f"{src_rel}: no site page for link {href!r}")
    if anchor and (target, anchor) not in DROP_ANCHORS:
        return f"{page}#{anchor}"
    return page


def friendly_link_text(body):
    """Replace link text that is only a file name with the page's title."""
    def fix(m):
        href, text = m.group(1), m.group(2)
        if re.fullmatch(r"[\w./-]+\.(md|csv)(#[\w-]+)?", text):
            text = e(PAGE_TITLES.get(href.split("#")[0], text))
        return f'<a href="{href}">{text}</a>'
    return re.sub(r'<a href="([^"]+)">([^<]+)</a>', fix, body)


def label_tables(body):
    """Make tables keyboard-scrollable and give header cells a scope."""
    out, last_heading, seen = [], "Table", Counter()
    pos = 0
    for m in re.finditer(r'<h[1-6][^>]*>(.*?)</h[1-6]>|<table>', body, re.S):
        out.append(body[pos:m.start()])
        if m.group(0).startswith("<h"):
            last_heading = re.sub(r"<[^>]+>", "", m.group(1))
            out.append(m.group(0))
        else:
            seen[last_heading] += 1
            n = seen[last_heading]
            name = f"{last_heading} (table{' ' + str(n) if n > 1 else ''})"
            out.append(f'<div class="tablewrap" role="region" tabindex="0" '
                       f'aria-label="{e(name)}"><table>')
        pos = m.end()
    out.append(body[pos:])
    body = "".join(out).replace("</table>", "</table></div>")
    body = re.sub(r'<th(?=[\s>])(?![^>]*scope)', '<th scope="col"', body)
    return body


def checklists(body):
    """Render Markdown task list items ("- [ ] text") as a styled checklist."""
    body = re.sub(r"<li>\[ \]\s*", '<li class="todo"><span class="box" aria-hidden="true"></span>', body)
    body = re.sub(r"<li>\[x\]\s*", '<li class="todo done"><span class="box" aria-hidden="true"></span>', body)
    body = re.sub(r"<ul>(\s*<li class=\"todo)", r'<ul class="checklist">\1', body)
    return body


def render_md(src_rel):
    text = (ROOT / src_rel).read_text(encoding="utf-8")
    text = strip_sections(text, SKIP_SECTIONS.get(src_rel, set()))
    md = markdown.Markdown(extensions=["tables", "toc", "sane_lists"])
    body = md.convert(text)

    def fix_link(m):
        return f'href="{e(resolve(src_rel, html.unescape(m.group(1))))}"'

    body = re.sub(r'href="([^"]+)"', fix_link, body)
    body = friendly_link_text(body)
    body = label_tables(body)
    body = checklists(body)
    title_m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    title = re.sub(r"<[^>]+>", "", title_m.group(1)) if title_m else SITE_NAME
    para = re.search(r"<p>(.*?)</p>", body, re.S)
    desc = re.sub(r"<[^>]+>", "", para.group(1)) if para else ""
    return title, html.unescape(desc), body


# ---------------------------------------------------------------------------
# Page template
# ---------------------------------------------------------------------------

def page(out_name, title, desc, body, full_title=None, wide=False):
    full_title = full_title or f"{title} | {SITE_NAME}"
    head_extra = ""
    if SITE_URL:
        canon = SITE_URL + "/" + ("" if out_name == "index.html" else out_name)
        head_extra += f'<link rel="canonical" href="{e(canon)}"><meta property="og:url" content="{e(canon)}">'
    if GOATCOUNTER:
        head_extra += (f'<script data-goatcounter="https://{e(GOATCOUNTER)}.goatcounter.com/count" '
                       f'async src="https://gc.zgo.at/count.js"></script>')
    current = ' aria-current="page"'
    nav = "".join(
        f'<li><a href="{href}"{current if href == out_name else ""}>{e(label)}</a></li>'
        for href, label in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc[:300])}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc[:300])}">
<meta name="theme-color" content="#231b4d">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/site.css">
{head_extra}
</head>
<body>
<a class="skip" href="#main">Skip to main content</a>
<nav class="helpbar" aria-label="Get help now">
  <span class="hb-title">Help now</span>
  <a class="hb red" href="tel:911">{icon("alert")}<span><span class="sr">Call </span><b>911</b> <small>Emergency</small></span></a>
  <a class="hb green" href="tel:+18883737888">{icon("phone")}<span><span class="sr">Call the National Human Trafficking Hotline at </span><b>1-888-373-7888</b> <small aria-hidden="true">Trafficking hotline</small></span></a>
  <a class="hb blue" href="sms:233733">{icon("message")}<span><span class="sr">Text the trafficking hotline at </span><b>Text 233733</b></span></a>
  <a class="hb exit" href="https://www.weather.gov/" rel="noreferrer" data-exit>{icon("exit")}<span><b>Quick exit</b><span class="sr"> (leaves this site)</span></span></a>
</nav>
<header class="site">
  <a class="brand" href="index.html">{icon("logo", "ic logo")}<span>{SITE_NAME}</span></a>
  <button type="button" class="navtoggle" aria-expanded="false" aria-controls="site-nav" hidden>{icon("menu")}<span>Menu</span></button>
  <nav id="site-nav" aria-label="Main"><ul>{nav}</ul></nav>
</header>
<main id="main"{' class="wide"' if wide else ""}>
{body}
</main>
<footer class="site">
  <p><strong>{SITE_NAME}</strong> is an independent, non-explicit guide for customers, dancers, club operators and advocates. Ratings are never for sale.</p>
  <p>General information from public sources. It is not legal advice. Allegations are labeled as allegations: a lawsuit is not a finding, and a settlement is not an admission.</p>
  <ul class="footlinks">
    <li><a href="about.html">About and corrections</a></li>
    <li><a href="method.html">How we rate clubs</a></li>
    <li><a href="data.html">Data files</a></li>
    <li><a href="about.html#privacy">Privacy</a></li>
  </ul>
</footer>
<script src="assets/site.js" defer></script>
</body>
</html>
"""


def write(name, content):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Generated pages
# ---------------------------------------------------------------------------

def states_in_data():
    return sorted({c["state"] for c in CLUBS}, key=lambda s: STATE_NAMES.get(s, s))


def source_links(sources):
    links = []
    for i, url in enumerate([s.strip() for s in sources.split("|") if s.strip()], 1):
        host = re.sub(r"^www\.", "", re.sub(r"^https?://([^/]+).*$", r"\1", url))
        links.append(f'<a href="{e(url)}">{e(host)}<span class="sr"> (source {i})</span></a>')
    return ", ".join(links) if links else "None"


def directory_page():
    clubs = sorted(CLUBS, key=lambda c: (STATE_NAMES.get(c["state"], c["state"]), c["city"], c["name"]))
    st_counts = Counter(c["status"] for c in CLUBS)
    rows = []
    for c in clubs:
        s_label, s_icon, s_tone = STATUS.get(c["status"], (c["status"], "question", "muted"))
        f_label, f_icon, f_tone = FLAG.get(c["overall_flag"], (c["overall_flag"], "question", "muted"))
        n = len(RECORDS_BY_CLUB.get(c["id"], []))
        recs = (f'<a href="records.html#{e(c["id"])}">{n} record{"s" if n != 1 else ""}'
                f'<span class="sr"> for {e(c["name"])}</span></a>') if n else "None yet"
        operator = f'<span class="sub">Operator: {e(c["operator"])}</span>' if c["operator"] else ""
        address = f'<span class="sub">{e(c["address"])}</span>' if c["address"] else ""
        notes = f'<span class="sub">{e(c["notes"])}</span>' if c["notes"] else ""
        search_text = " ".join([c["name"], c["city"], c["state"], STATE_NAMES.get(c["state"], ""),
                                c["operator"]]).lower()
        rows.append(
            f'<tr id="{e(c["id"])}" data-state="{e(c["state"])}" data-status="{e(c["status"])}" '
            f'data-text="{e(search_text)}">'
            f'<th scope="row"><span class="clubname">{e(c["name"])}</span>{address}{operator}{notes}</th>'
            f'<td>{e(c["city"])}</td><td><abbr title="{e(STATE_NAMES.get(c["state"], c["state"]))}">{e(c["state"])}</abbr></td>'
            f'<td>{badge(s_label, s_icon, s_tone)}</td><td>{badge(f_label, f_icon, f_tone)}</td>'
            f'<td>{recs}</td><td class="srcs">{source_links(c["sources"])}</td></tr>')
    state_opts = "".join(f'<option value="{s}">{e(STATE_NAMES.get(s, s))}</option>' for s in states_in_data())
    status_opts = "".join(f'<option value="{k}">{e(v[0])}</option>' for k, v in STATUS.items())
    status_legend = "".join(
        f'<li>{badge(v[0], v[1], v[2])} {e(desc)}</li>' for (k, v), desc in zip(STATUS.items(), [
            "Confirmed operating in the current review.",
            "A news, government or company source from the last 24 months says it's operating.",
            "A source names the club and city. We haven't confirmed it's operating.",
            "There's a specific reason to doubt it's still operating.",
            "A source reports it closed.",
        ]))
    flag_legend = "".join(
        f'<li>{badge(v[0], v[1], v[2])} {e(desc)}</li>' for (k, v), desc in zip(FLAG.items(), [
            "No full review yet. Most clubs are here for now.",
            "Reviewed, and no qualifying record in the last 5 years. Not a guarantee.",
            "A finding or settlement, or two or more open allegations, in the last 5 years.",
            "A conviction, a trafficking charge or finding, a permit revoked for illegal activity, or repeated violence, in the last 5 years.",
        ]))
    body = f"""
<h1>Club directory</h1>
<p class="lead">{len(CLUBS)} clubs in {len(states_in_data())} states so far, built state by state from public records. Ohio is first. Every listing links to its source.</p>
<div class="callout">{icon("info")}<p>A listing is not an endorsement, and "not reviewed" means we haven't finished checking, not that a club is safe or unsafe. See <a href="method.html">how we rate clubs</a>. Something wrong? <a href="about.html#corrections">Send a correction</a>.</p></div>

<form id="filters" class="filters" hidden role="search" aria-label="Filter the directory">
  <div><label for="f-state">State</label><select id="f-state" name="state"><option value="">All states</option>{state_opts}</select></div>
  <div><label for="f-status">Status</label><select id="f-status" name="status"><option value="">Any status</option>{status_opts}</select></div>
  <div class="grow"><label for="f-q">Name, city or operator</label><input id="f-q" name="q" type="search" autocomplete="off"></div>
</form>
<p id="shown" role="status" class="shown">Showing all {len(CLUBS)} clubs.</p>

<div class="tablewrap" role="region" tabindex="0" aria-labelledby="clubs-cap">
<table id="clubs" class="dir">
<caption id="clubs-cap">Clubs by state and city ({st_counts.get("reported-open", 0) + st_counts.get("verified", 0)} reported or verified open, {st_counts.get("unverified", 0)} not yet confirmed, {st_counts.get("unknown", 0)} unknown, {st_counts.get("closed", 0)} closed)</caption>
<thead><tr><th scope="col">Club</th><th scope="col">City</th><th scope="col">State</th><th scope="col">Status</th><th scope="col">Rating</th><th scope="col">Public records</th><th scope="col">Sources</th></tr></thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
</div>

<h2 id="status-key">What the status means</h2>
<ul class="legend">{status_legend}</ul>
<h2 id="rating-key">What the rating means</h2>
<ul class="legend">{flag_legend}</ul>
<p>Download the data: <a href="data/clubs.csv" download>clubs.csv</a> and <a href="data/evidence.csv" download>evidence.csv</a>. Field definitions are on the <a href="data.html">data page</a>.</p>
"""
    return page("directory.html", "Club directory",
                f"A sourced directory of {len(CLUBS)} U.S. strip clubs, with status and public records for each.", body,
                wide=True)


def records_page():
    sections = []
    for club_id, recs in sorted(RECORDS_BY_CLUB.items(),
                                key=lambda kv: (CLUB_BY_ID.get(kv[0], {}).get("state", ""),
                                                CLUB_BY_ID.get(kv[0], {}).get("city", ""),
                                                CLUB_BY_ID.get(kv[0], {}).get("name", kv[0]))):
        club = CLUB_BY_ID.get(club_id, {"name": club_id, "city": "", "state": ""})
        rows = []
        for r in sorted(recs, key=lambda r: r["date"] or "0", reverse=True):
            src = (f'<a href="{e(r["source_url"])}">{e(SOURCE_TYPE.get(r["source_type"], r["source_type"]))}'
                   f'<span class="sr"> source for {e(r["evidence_id"])}</span></a>')
            checked = "Yes" if r["primary_confirmed"] == "yes" else "Not yet"
            rows.append(
                f'<tr><td>{e(r["date"] or "Date to confirm")}</td>'
                f'<td>{e(DIMENSION.get(r["dimension"], r["dimension"]))}</td>'
                f'<td><span class="rtype {e(r["type"])}">{e(RECORD_TYPE.get(r["type"], r["type"]))}</span></td>'
                f'<td>{e(r["summary"])}</td><td>{src}</td><td>{checked}</td></tr>')
        where = ", ".join(x for x in [club.get("city", ""), club.get("state", "")] if x)
        sections.append(f"""
<section aria-labelledby="{e(club_id)}">
<h2 id="{e(club_id)}">{e(club["name"])} <span class="where">{e(where)}</span></h2>
<div class="tablewrap" role="region" tabindex="0" aria-label="Records for {e(club["name"])}">
<table class="records"><thead><tr><th scope="col">Date</th><th scope="col">Area</th><th scope="col">Type</th><th scope="col">What the record says</th><th scope="col">Source</th><th scope="col">Checked against the primary record</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
<p class="back"><a href="directory.html#{e(club_id)}">Back to {e(club["name"])} in the directory</a></p>
</section>""")
    types = Counter(r["type"] for r in EVIDENCE)
    type_list = ", ".join(f"{n} {RECORD_TYPE.get(t, t).lower()}{'s' if n != 1 else ''}" for t, n in types.most_common())
    body = f"""
<h1>Public records</h1>
<p class="lead">{len(EVIDENCE)} records for {len(RECORDS_BY_CLUB)} clubs: {e(type_list)}. Each one links to its source.</p>
<div class="callout">{icon("scale")}<p>A lawsuit or a charge is an allegation, not a finding. A settlement is not an admission unless the record says so. Records older than 5 years are history and don't set a rating. Clubs can <a href="about.html#corrections">respond to any record</a>.</p></div>
{"".join(sections)}
"""
    return page("records.html", "Public records",
                f"{len(EVIDENCE)} sourced public records (lawsuits, settlements, permit actions and convictions) tied to specific clubs.",
                body, wide=True)


def readme_section(title):
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    m = re.search(rf"^## {re.escape(title)}\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        return ""
    body = markdown.markdown(m.group(1), extensions=["sane_lists"])
    body = re.sub(r'href="([^"]+)"', lambda mm: f'href="{e(resolve("README.md", html.unescape(mm.group(1))))}"', body)
    return friendly_link_text(body)


def home_page():
    st = Counter(c["status"] for c in CLUBS)
    oh = sum(1 for c in CLUBS if c["state"] == "OH")
    tiles = [
        ("etiquette.html", "person", "Customers", "How to act, what to tip, and how not to get ripped off"),
        ("dancers.html", "heart", "Dancers", "Your rights, fees, tips, and where to get help"),
        ("trafficking.html", "shield", "Stop trafficking", "The signs, and what to do when you see them"),
        ("operators.html", "building", "Club owners", "Cut legal risk, protect dancers, earn a better rating"),
        ("directory.html", "list", "Club directory", f"{len(CLUBS)} clubs with sources and public records"),
        ("laws.html", "scale", "Laws by state", "Age limits, touching, fees and worker protections"),
        ("standard.html", "checkbox", "Club Safety Standard", "The checklist any club can meet"),
        ("how-clubs-work.html", "dollar", "How clubs work", "Who earns what, and why clubs end up in court"),
    ]
    tile_html = "".join(
        f'<li><a class="tile" href="{href}"><span class="pic">{icon(ic)}</span>'
        f'<span class="tl">{e(t)}</span><span class="th">{e(sub)}</span></a></li>' for href, ic, t, sub in tiles)
    body = f"""
<div class="hero">
<h1>Strip Club Etiquette</h1>
<p class="lead">How to be a good customer, what fair treatment looks like for dancers, and how to spot and stop human trafficking. Plain English, every claim sourced.</p>
</div>

<section aria-labelledby="start-h">
<h2 id="start-h">Start here</h2>
<ul class="tiles">{tile_html}</ul>
</section>

<section aria-labelledby="why-h" class="panel">
<h2 id="why-h">Why this exists</h2>
<p>Most dancers are adults working by choice, and dancing is not trafficking. But it's an industry where wage theft, unsafe rooms and, sometimes, trafficking happen out of sight. Visibility keeps clubs honest: clear rules for customers, known rights for dancers, a public record of how clubs operate, and a simple way to report when something is wrong.</p>
</section>

<section aria-labelledby="see-h">
<h2 id="see-h">If something seems wrong</h2>
<p>If a dancer seems afraid, controlled by someone else, or under 18, don't confront anyone or try a rescue. Note what you saw, then:</p>
<ul class="actions">
<li><a href="tel:+18883737888">{icon("phone")}<span>Call the National Human Trafficking Hotline: <b>1-888-373-7888</b></span></a></li>
<li><a href="sms:233733">{icon("message")}<span>Text <b>233733</b></span></a></li>
<li><a href="tel:911">{icon("alert")}<span>Call <b>911</b> if someone is in immediate danger</span></a></li>
</ul>
<p>In Ohio you can also report to 844-END-OHHT (844-363-6448). <a href="trafficking.html#signs-to-watch-for">See the signs to watch for</a>.</p>
</section>

<section aria-labelledby="now-h">
<h2 id="now-h">Where the directory stands</h2>
<ul class="stats">
<li><b>{len(CLUBS)}</b> <span>clubs listed in {len(states_in_data())} states</span></li>
<li><b>{oh}</b> <span>in Ohio, where the build started</span></li>
<li><b>{len(EVIDENCE)}</b> <span>public records tied to {len(RECORDS_BY_CLUB)} clubs</span></li>
<li><b>{st.get("reported-open", 0) + st.get("verified", 0)}</b> <span>reported or verified open</span></li>
</ul>
<p>The U.S. has roughly 3,900 strip clubs, so this is a state-by-state build. <a href="coverage.html">See the coverage plan</a>.</p>
</section>

<section aria-labelledby="rules-h">
<h2 id="rules-h">Ground rules</h2>
{readme_section("Ground rules")}
</section>
"""
    return page("index.html", SITE_NAME,
                "How to be a good strip club customer, dancer rights, and how to spot and report human trafficking. A sourced, non-explicit guide and club directory.",
                body, full_title=f"{SITE_NAME}: customer etiquette, dancer rights, and stopping trafficking")


def about_page():
    if CONTACT_EMAIL:
        contact = (f'Email <a href="mailto:{e(CONTACT_EMAIL)}?subject=Correction">{e(CONTACT_EMAIL)}</a>, '
                   f'or open an issue on <a href="{REPO_URL}/issues">the project\'s GitHub page</a>.')
    else:
        contact = f'Open an issue on <a href="{REPO_URL}/issues">the project\'s GitHub page</a>.'
    if GOATCOUNTER:
        privacy = ("This site counts visits with GoatCounter, which sets no cookies and doesn't collect personal "
                   "information. It sees the page, the referring site, and a rough location and device type.")
    else:
        privacy = "This site doesn't use cookies, ads or trackers."
    body = f"""
<h1>About</h1>
<p class="lead">{SITE_NAME} is an independent, non-explicit guide to how strip clubs work: for customers, dancers, club operators and the people working to stop trafficking.</p>

<h2 id="what">What we do</h2>
<ul>
<li>Plain-English guides on <a href="etiquette.html">etiquette</a>, <a href="dancers.html">dancer rights</a>, <a href="trafficking.html">trafficking</a> and <a href="laws.html">the law</a>.</li>
<li>A <a href="directory.html">directory</a> of clubs with a <a href="records.html">public record</a> of how they operate: lawsuits, settlements, permit actions and convictions, each linked to its source.</li>
<li>A <a href="standard.html">Club Safety Standard</a> any club can meet, and a <a href="method.html">rating method</a> that judges clubs on records, not rumor.</li>
</ul>

<h2 id="rules">Ground rules</h2>
{readme_section("Ground rules")}

<h2 id="corrections">Corrections and responses</h2>
<p>Any club, dancer or member of the public can ask for a correction. Send the club, what's wrong, and a source. A club can also send a short written response to any record, and we'll link it next to that record.</p>
<p>{contact}</p>

<h2 id="privacy">Privacy</h2>
<p>{privacy} We never publish personal information about dancers, staff or customers.</p>

<h2 id="not-advice">Not legal advice</h2>
<p>Everything here is general information from public sources, with the date it was checked. Laws change and differ by state and city. Check the linked source, or talk to a lawyer, before you act.</p>
"""
    return page("about.html", "About", f"What {SITE_NAME} is, how corrections work, and privacy.", body)


def not_found_page():
    body = """
<h1>Page not found</h1>
<p>That page doesn't exist or has moved. Try the <a href="index.html">home page</a> or the <a href="directory.html">club directory</a>.</p>
"""
    return page("404.html", "Page not found", "That page doesn't exist.", body)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT)
    (OUT / "data").mkdir(exist_ok=True)
    shutil.copy(ROOT / "data/clubs.csv", OUT / "data/clubs.csv")
    shutil.copy(ROOT / "data/evidence.csv", OUT / "data/evidence.csv")
    (OUT / ".nojekyll").write_text("")

    pages = ["index.html", "directory.html", "records.html", "about.html"]
    for src, (out_name, _label, _icon) in MD_PAGES.items():
        title, desc, body = render_md(src)
        write(out_name, page(out_name, title, desc, body))
        pages.append(out_name)

    write("index.html", home_page())
    write("directory.html", directory_page())
    write("records.html", records_page())
    write("about.html", about_page())
    write("404.html", not_found_page())

    robots = "User-agent: *\nAllow: /\n"
    if SITE_URL:
        today = date.today().isoformat()
        urls = "".join(
            f"<url><loc>{e(SITE_URL)}/{'' if p == 'index.html' else e(p)}</loc><lastmod>{today}</lastmod></url>"
            for p in pages)
        write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
              f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
        robots += f"Sitemap: {SITE_URL}/sitemap.xml\n"
        if SITE_URL.startswith("https://") and not SITE_URL.endswith(".github.io"):
            write("CNAME", SITE_URL.split("://", 1)[1] + "\n")
    write("robots.txt", robots)
    print(f"Built {len(pages) + 1} pages into {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
