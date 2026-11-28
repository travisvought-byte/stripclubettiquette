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
# Full address of the live site with no trailing slash. It turns on canonical
# links, the sitemap and the CNAME file. Leave empty to build with none of them.
SITE_URL = "https://stripclubguide.org"
# GoatCounter site code: "stripclubguide" counts at stripclubguide.goatcounter.com.
# Leave empty to build with no counter.
GOATCOUNTER = "stripclubguide"
# Where corrections go. The issues page works once the repository is public.
CONTACT_EMAIL = ""
REPO_URL = "https://github.com/travisvought-byte/stripclubettiquette"
# Where club claims go. Set one: CLAIM_FORM_URL is a form service's address that
# takes a POST; CLAIM_EMAIL opens the visitor's email app with the claim filled
# in. With neither set, the claim page lists what we'll ask for and says claims
# open soon. Claims go to Travis's Gmail, his choice.
CLAIM_FORM_URL = ""
CLAIM_EMAIL = "veteranhomeguardians@gmail.com"
# Club-supplied details older than this many days are marked as possibly out of date.
CLUB_INFO_STALE_DAYS = 180
# Where dancers send anonymous pay reports: a Tally form that asks for no names,
# emails or phone numbers. Club pages add ?club_id= so the club is filled in. Leave
# empty and the dancer pay page lists what the form will ask and says reports open soon.
DANCER_FORM_URL = "https://tally.so/r/2jPKQ9"
# A club's dancer-reported numbers show only once at least this many separate
# reports from the last DANCER_REPORT_MONTHS months are in data/dancer-reports.csv.
DANCER_REPORT_MIN = 3
DANCER_REPORT_MONTHS = 12

# ---------------------------------------------------------------------------
# Pages made from Markdown files: source -> (output, short label, icon)
# ---------------------------------------------------------------------------
MD_PAGES = OrderedDict([
    ("guides/etiquette.md", ("etiquette.html", "Etiquette", "person")),
    ("guides/for-dancers.md", ("dancers.html", "For dancers", "heart")),
    ("guides/dancer-safety.md", ("dancer-safety.html", "Looking out for each other", "person")),
    ("guides/human-trafficking.md", ("trafficking.html", "Stop trafficking", "shield")),
    ("guides/why-it-keeps-happening.md", ("why-it-keeps-happening.html", "Why it keeps happening", "alert")),
    ("guides/for-club-operators.md", ("operators.html", "For clubs", "building")),
    ("guides/model-policies.md", ("model-policies.html", "Model policies", "file")),
    ("guides/how-strip-clubs-work.md", ("how-clubs-work.html", "How clubs work", "dollar")),
    ("guides/laws-by-state.md", ("laws.html", "Laws by state", "scale")),
    ("guides/whats-working.md", ("whats-working.html", "What's working", "check-circle")),
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
    "data/club-info.csv": "claim.html",
    "data/house-fees.csv": "dancer-pay.html",
    "data/dancer-reports.csv": "dancer-pay.html#dancer-reports",
    "data/stay-away.csv": "stay-away.html",
    "data/stay-away-records.csv": "stay-away.html",
}

# Titles for pages, used when a link's text is a bare file name such as "laws-by-state.md".
PAGE_TITLES = {"index.html": "the home page", "directory.html": "the club directory",
               "records.html": "the public records", "dancer-pay.html": "dancer pay and house fees",
               "stay-away.html": "the places to stay away from"}
for _src, (_out, _label, _icon) in MD_PAGES.items():
    _m = re.search(r"^# (.+)$", (ROOT / _src).read_text(encoding="utf-8"), re.M)
    PAGE_TITLES[_out] = _m.group(1).strip() if _m else _label

# Anchors that exist on GitHub but not on the site (sections left off the site).
DROP_ANCHORS = {("research/ohio.md", "open-leads")}

# Sections left off the published page, by source file and heading text.
SKIP_SECTIONS = {"research/ohio.md": {"Open leads"}}

NAV = [
    ("visit.html", "Visiting"),
    ("work.html", "Dancers"),
    ("clubs.html", "Clubs"),
    ("learn.html", "Learn"),
    ("directory.html", "Directory"),
    ("trafficking.html", "Trafficking"),
    ("about.html", "About"),
]

# ---------------------------------------------------------------------------
# One starting page for each kind of visitor. Each group is a heading and a
# list of (link, icon, label, short line). "ask" is a checklist of questions
# to put to a club, and "help" is the role's own help line.
# ---------------------------------------------------------------------------
ROLES = OrderedDict([
    ("visit.html", {
        "door": ("person", "I'm visiting a club", "What to know before you go, how to act, and how to keep your money safe"),
        "title": "Visiting a club",
        "desc": "What to know before you visit a strip club: age limits, cover, cash, tipping, private dances, VIP rooms, and how to avoid getting overcharged.",
        "lead": "Going for the first time, or bringing a group? Here's what to check before you go, how to act once you're there, and how to keep your money safe.",
        "groups": [
            ("Plan your visit", [
                ("etiquette.html#before-you-go", "list", "Before you go", "Age limits, hours, cover, cash and a budget"),
                ("laws.html", "scale", "Know the local rules", "Touching, nudity and alcohol rules change by state"),
                ("directory.html", "map", "Find a club", "Check it's open and see its public record"),
                ("stay-away.html", "octagon", "Places to stay away from", "Clubs and bars tied to trafficking in court and agency records"),
            ]),
            ("At the club", [
                ("etiquette.html#at-the-door", "building", "At the door", "ID, cover and security"),
                ("etiquette.html#at-the-stage", "dollar", "At the stage", "How tipping works"),
                ("etiquette.html#private-dances", "person", "Private dances", "Agree on the price before it starts"),
                ("etiquette.html#vip-and-champagne-rooms", "file", "VIP rooms", "Get the price and the time in writing"),
                ("etiquette.html#talking-with-dancers", "message", "Talking with dancers", "Privacy, boundaries and taking no for an answer"),
                ("etiquette.html#phones-photos-and-privacy", "shield", "Phones and photos", "Never photograph dancers or customers"),
            ]),
            ("Protect yourself", [
                ("etiquette.html#protect-your-money", "dollar", "Protect your money", "Surcharges, ATM fees and padded tabs"),
                ("etiquette.html#alcohol-and-behavior", "alert", "Alcohol and behavior", "Stay in control of your night"),
                ("etiquette.html#groups-and-bachelor-parties", "list", "Groups and parties", "Set the budget and the rules up front"),
                ("etiquette.html#women-and-couples", "heart", "Women and couples", "What's different, and what isn't"),
            ]),
        ],
        "ask_title": "Ask the club before you go",
        "ask": [
            "What's the cover charge, and does it change later in the night?",
            "Is it 18 and up, or 21 and up? Is there a dress code?",
            "Cash only, or cards too? What's the surcharge on cards or club currency?",
            "What does a private dance cost, and how long is one?",
            "What does the VIP room cost, for how long, and is there a drink minimum?",
        ],
        "help": ("etiquette.html#if-something-seems-wrong", "If something seems wrong while you're there"),
    }),
    ("work.html", {
        "door": ("heart", "I dance or work in a club", "Your pay, tips, safety and rights, and free places to get help"),
        "title": "Dancing or working in a club",
        "desc": "For dancers and club staff: contractor or employee, tips, house fees and fines, wage complaints, harassment, and getting out of a controlling situation.",
        "lead": "Your pay, your tips, your safety and your rights, with free places to get help. Nothing on this site asks for your name.",
        "groups": [
            ("Get help now", [
                ("dancers.html#get-help-now", "phone", "Free help lines", "Wages, harassment and trafficking, with no cost to call"),
                ("dancers.html#if-someone-else-is-in-control", "shield", "If someone else is in control", "The signs, and help that doesn't depend on immigration status"),
                ("dancers.html#your-rights-at-a-glance", "scale", "Your rights at a glance", "Tips, fees, safety and speaking up, in short"),
            ]),
            ("Look out for each other", [
                ("dancer-safety.html#a-buddy-system-at-work", "person", "Buddy system", "Check-ins, signals and leaving together"),
                ("dancer-safety.html#customers-to-watch", "alert", "Customers to watch", "Red flags to pass on to security and coworkers"),
                ("dancer-safety.html#getting-home-safely", "map", "Getting home safely", "Walking out, rides, and what to do if you're followed"),
                ("dancer-safety.html#protect-your-privacy", "shield", "Protect your privacy", "Stage name, accounts, photos and stalking"),
                ("dancer-safety.html#when-a-coworker-seems-controlled-or-in-danger", "heart", "When a coworker is in trouble", "The signs, and how to help without making it worse"),
                ("dancer-safety.html#after-an-assault", "phone", "After an assault", "Getting safe, support and your options"),
            ]),
            ("Your money", [
                ("dancers.html#contractor-or-employee", "scale", "Contractor or employee?", "What decides it, and why it matters"),
                ("dancers.html#your-tips-are-yours", "dollar", "Your tips are yours", "What a club can and can't take"),
                ("dancers.html#house-fees-tip-outs-and-fines", "file", "House fees and fines", "What's legal and what isn't"),
                ("dancer-pay.html", "dollar", "House fees by state", "What clubs have charged, from court records, laws and the news"),
                ("dancer-pay.html#dancer-reports", "list", "Report your club's fees", "Anonymous, numbers only, no names"),
                ("dancers.html#keep-a-record", "list", "Keep a record", "What to write down and where to keep it"),
                ("dancers.html#how-to-file-a-wage-complaint", "checkbox", "File a wage complaint", "Where to file and the deadlines"),
                ("dancers.html#money-basics-taxes-and-savings", "dollar", "Taxes and savings", "Self-employment tax, quarterly payments, and the tips deduction"),
            ]),
            ("Your safety", [
                ("dancers.html#harassment-assault-and-safety", "alert", "Harassment and safety", "What a club owes you, and where to report"),
                ("dancers.html#health-and-safety-at-work", "check-circle", "Health and safety at work", "OSHA complaints and low-cost health care"),
                ("dancers.html#acting-together", "person", "Acting together", "Your right to organize with coworkers"),
                ("trafficking.html#signs-to-watch-for", "shield", "Signs of trafficking", "For you or someone you work with"),
                ("trafficking.html#reporting-safely", "phone", "Report safely", "Anonymous options, and what happens to your information"),
            ]),
            ("Before you audition", [
                ("directory.html", "map", "Look up the club", "Lawsuits, settlements and permit actions, with sources"),
                ("stay-away.html", "octagon", "Places to stay away from", "Where trafficking and forced prostitution are on the record"),
                ("why-it-keeps-happening.html#the-patterns", "alert", "Too good to be true", "Fake job offers, debts and held IDs"),
                ("laws.html", "scale", "Your state's rules", "Fee caps, training and age limits"),
                ("standard.html", "check-circle", "What a well-run club does", "The Club Safety Standard"),
            ]),
        ],
        "ask_title": "Ask a club before you audition",
        "ask": [
            "Will I be an employee or a contractor?",
            "What are the house fee and tip-out, in writing? Do they change by shift?",
            "Who sets dance prices, and what share do I keep?",
            "Are fines written down? What are they for?",
            "Is there security on the floor and in the private rooms?",
            "How and when am I paid?",
        ],
        "help": ("dancers.html#get-help-now", "Free help lines for dancers"),
    }),
    ("clubs.html", {
        "door": ("building", "I run a club", "Cut legal risk, protect dancers and earn a better rating"),
        "title": "Running a club",
        "desc": "For strip club owners and managers: cut wage and liability risk, protect dancers and customers, meet the Club Safety Standard, and keep your listing accurate.",
        "lead": "Cut legal risk, keep dancers and customers safe, and earn a better rating. Ratings here come from public records and the Club Safety Standard. They are never for sale.",
        "groups": [
            ("Start here", [
                ("operators.html#why-this-matters-to-your-bottom-line", "dollar", "Why it pays", "What wage suits and bad nights cost a club"),
                ("operators.html#the-playbook", "list", "The playbook", "Nine practices that cut risk"),
                ("standard.html", "checkbox", "Club Safety Standard", "The checklist any club can meet"),
                ("model-policies.html", "file", "Model policies", "A policy and procedure template to adopt"),
                ("whats-working.html", "check-circle", "What's working", "Fee rules, safety steps and business models with a record"),
            ]),
            ("Your listing", [
                ("claim.html", "checkbox", "Claim your listing", "Add your hours, prices, dancer terms and booking line, free"),
                ("directory.html", "map", "See your listing", "Status, records and sources"),
                ("method.html", "search", "How we rate clubs", "Records, not rumor"),
                ("about.html#corrections", "file", "Correct or respond", "Fix a listing or answer a record"),
            ]),
            ("Protect your dancers", [
                ("model-policies.html#roles-and-responsibilities", "person", "Roles and responsibilities", "Safety duties for owners, managers, security, house moms, DJs and bar staff"),
                ("model-policies.html#3-customer-conduct-warnings-ejection-and-bans", "octagon", "Customer conduct and bans", "Warnings, removal and the ban list"),
                ("model-policies.html#5-incident-reports-and-records", "file", "Incident reports", "What to write down, and the form"),
                ("model-policies.html#6-id-and-age-checks", "checkbox", "ID and age checks", "In person, and never hold a dancer's ID"),
                ("model-policies.html#8-fees-tips-and-pay", "dollar", "Fees, tips and pay", "Written, capped, no debt, tips stay with the dancer"),
                ("model-policies.html#9-staff-training", "list", "Staff training", "Topics, who takes them, and how often"),
            ]),
            ("Trafficking and the law", [
                ("trafficking.html#what-clubs-should-do", "shield", "What clubs should do", "ID checks, training, posted hotlines and no retaliation"),
                ("model-policies.html#7-anti-trafficking-screening-and-response", "shield", "Screening and response", "Signs at hiring and on shift, and the steps to take"),
                ("laws.html", "scale", "Laws by state", "Classification, fees, training and age rules"),
            ]),
        ],
        "ask_title": "What customers and dancers will ask you",
        "ask": [
            "Cover charge, age limit, dress code and hours",
            "Card surcharges and the price of dances and VIP time",
            "Employee or contractor, and the house fee in writing",
            "Security on the floor and in private rooms",
        ],
        "help": ("trafficking.html#what-clubs-should-do", "How to handle a suspected trafficking case"),
    }),
    ("learn.html", {
        "door": ("search", "I'm looking into the industry", "For families, reporters, officials, advocates, researchers and lenders"),
        "title": "Learning about the industry",
        "desc": "How strip clubs work, the laws in each state, how trafficking shows up and how it doesn't, and a sourced public record of clubs.",
        "lead": "For families, reporters, local officials, advocates, researchers, and the banks and insurers that serve clubs.",
        "groups": [
            ("How it works", [
                ("how-clubs-work.html", "dollar", "How clubs work", "Who earns what, and where the money goes"),
                ("how-clubs-work.html#the-contractor-vs-employee-fight", "scale", "The contractor fight", "Why clubs keep ending up in court"),
                ("laws.html", "scale", "Laws by state", "What each state allows and requires"),
                ("laws.html#the-age-21-debate", "person", "The age-21 debate", "Laws raising the minimum age to dance"),
                ("whats-working.html", "check-circle", "What's working", "What the record shows helps dancers and clubs"),
                ("dancer-pay.html", "file", "House fees by state", "What clubs have charged dancers, with sources"),
            ]),
            ("Trafficking", [
                ("trafficking.html#what-trafficking-is", "shield", "What trafficking is", "The legal definition, in plain English"),
                ("trafficking.html#dancing-is-not-trafficking", "heart", "Dancing is not trafficking", "Why the difference matters"),
                ("trafficking.html#signs-to-watch-for", "alert", "Signs to watch for", "What to look for in a club"),
                ("trafficking.html#reporting-safely", "phone", "Reporting safely", "Anonymous options, and what the hotline does with a tip"),
                ("trafficking.html#advocacy-what-helps", "check-circle", "What helps", "Advocacy that works"),
                ("why-it-keeps-happening.html", "alert", "Why it keeps happening", "The patterns, why it's hard to stop, and where to get help"),
                ("stay-away.html", "octagon", "Places to stay away from", "Places tied to trafficking in court and agency records"),
            ]),
            ("The record", [
                ("directory.html", "map", "Club directory", "Clubs with status and sources"),
                ("directory.html#by-state", "map", "Clubs by state", "One page for each state"),
                ("records.html", "file", "Public records", "Convictions, findings, settlements and lawsuits"),
                ("stay-away.html", "octagon", "Stay away list", "Places closed or convicted over trafficking, and where they came back"),
                ("method.html", "search", "How we rate", "The rating method"),
                ("data.html", "list", "Data files", "Download the data"),
                ("coverage.html", "map", "Coverage plan", "Where the build goes next"),
            ]),
        ],
        "ask_title": "",
        "ask": [],
        "help": ("trafficking.html#get-help-or-report", "How to report suspected trafficking"),
    }),
])

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
    "VA": "Virginia", "VI": "U.S. Virgin Islands", "GU": "Guam", "MP": "Northern Mariana Islands", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
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

# Details a club gives us itself ("club says"). Shown beside our own record and
# never used in a rating. Field order here is the order on the page.
CLUB_INFO_GROUPS = [
    ("Visiting", "person", [
        ("hours", "Hours"), ("cover", "Cover charge"), ("min_age", "Age limit"),
        ("dress_code", "Dress code"), ("alcohol", "Drinks"), ("payment", "Payment"),
        ("card_fee", "Fee on cards or club currency"), ("private_dance", "Private dance"),
        ("vip", "VIP room"),
    ]),
    ("Dancers", "heart", [
        ("worker_status", "Dancers work as"), ("house_fee", "House fee"), ("tip_out", "Tip-out"),
        ("hiring", "Hiring now"), ("apply_url", "How to apply"),
        ("booking_line", "Booking line"), ("audition_hours", "Auditions"),
    ]),
    ("Safety", "shield", [
        ("security_private_rooms", "Security in private rooms"),
        ("trafficking_training", "Staff trained on trafficking every year"),
        ("hotline_posted", "Trafficking hotline posted for dancers and staff"),
    ]),
]
YES_NO_FIELDS = {"hiring", "security_private_rooms", "trafficking_training", "hotline_posted"}
WORKER_STATUS = {"employee": "Employees", "contractor": "Independent contractors",
                 "both": "Some employees, some contractors"}
TERMS_FIELDS = ("worker_status", "house_fee", "tip_out")
# How dancers get on the schedule. Shown only from a club we've confirmed (claimed = yes)
# that also publishes its dancer terms, and never taken from a dancer report.
CLUB_ONLY_FIELDS = ("booking_line", "audition_hours")
# Fields that count as a hiring notice: allowed only with the dancer terms published.
HIRING_FIELDS = ("hiring", "apply_url", "booking_line", "audition_hours")

# ---------------------------------------------------------------------------
# Stay away list: places tied to trafficking or sexual exploitation in primary
# records. stay-away.csv has one row per place; stay-away-records.csv one row
# per record. A place goes on "stay-away" only with a conviction, a closure or
# nuisance order, or a license revocation; anything less is "caution".
# ---------------------------------------------------------------------------
SA_LISTS = OrderedDict([
    ("stay-away", ("Stay away", "octagon", "bad")),
    ("caution", ("Use caution", "alert", "warn")),
])
SA_KINDS = {"club": "Strip club", "hostess-bar": "Hostess bar or cantina", "bar": "Bar or cantina"}
SA_TYPES = OrderedDict([
    ("conviction", ("Conviction or guilty plea", "bad")),
    ("closure-order", ("Closure or nuisance order", "bad")),
    ("license-revocation", ("License revoked or given up", "bad")),
    ("reopening", ("Reopened or kept operating", "bad")),
    ("finding", ("Agency finding", "warn")),
    ("temporary-order", ("Temporary court order", "warn")),
    ("license-suspension", ("License suspended", "warn")),
    ("charge", ("Charged, not convicted", "warn")),
    ("filing", ("Lawsuit filed", "warn")),
    ("status", ("Status", "muted")),
])
SA_STRONG = {"conviction", "closure-order", "license-revocation"}
SA_PLACES = read_csv("data/stay-away.csv")
SA_RECORDS = read_csv("data/stay-away-records.csv")
SA_RECS_BY_PLACE = OrderedDict()
SA_BY_CLUB = {}


def check_stay_away():
    ids = set()
    for pl in SA_PLACES:
        pid = pl["place_id"]
        if not re.fullmatch(r"SA-\d{3}", pid) or pid in ids:
            raise SystemExit(f"stay-away.csv: bad or repeated place_id {pid!r}")
        ids.add(pid)
        if pl["list"] not in SA_LISTS or pl["kind"] not in SA_KINDS:
            raise SystemExit(f"stay-away.csv: {pid} has list {pl['list']!r} or kind {pl['kind']!r} outside the lists")
        if pl["state"] not in STATE_NAMES:
            raise SystemExit(f"stay-away.csv: {pid} has unknown state {pl['state']!r}")
        if pl["club_id"]:
            if pl["club_id"] not in CLUB_BY_ID:
                raise SystemExit(f"stay-away.csv: {pid} names club {pl['club_id']!r}, not in clubs.csv")
            if pl["club_id"] in SA_BY_CLUB:
                raise SystemExit(f"stay-away.csv: club {pl['club_id']} is on the list twice")
            SA_BY_CLUB[pl["club_id"]] = pl
        if not pl["why"].strip():
            raise SystemExit(f"stay-away.csv: {pid} has no why")
        SA_RECS_BY_PLACE[pid] = []
    for r in SA_RECORDS:
        if r["place_id"] not in ids:
            raise SystemExit(f"stay-away-records.csv: unknown place {r['place_id']!r}")
        if r["type"] not in SA_TYPES or r["source_type"] not in SOURCE_TYPE:
            raise SystemExit(f"stay-away-records.csv: {r['place_id']} has type {r['type']!r} or source {r['source_type']!r} outside the lists")
        if not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", r["date"]):
            raise SystemExit(f"stay-away-records.csv: {r['place_id']} has a bad date {r['date']!r}")
        if not r["source_url"].startswith("https://") or not r["summary"].strip():
            raise SystemExit(f"stay-away-records.csv: {r['place_id']} needs an https source and a summary")
        SA_RECS_BY_PLACE[r["place_id"]].append(r)
    for pl in SA_PLACES:
        types = {r["type"] for r in SA_RECS_BY_PLACE[pl["place_id"]]}
        if not types:
            raise SystemExit(f"stay-away.csv: {pl['place_id']} has no records")
        if pl["list"] == "stay-away" and not types & SA_STRONG:
            raise SystemExit(f"stay-away.csv: {pl['place_id']} is on stay-away without a conviction, closure order or revocation")


check_stay_away()

CLUB_INFO = read_csv("data/club-info.csv")
INFO_BY_CLUB = {}


def check_club_info():
    """Stop the build on club-supplied rows that break the rules in data/README.md."""
    errs = []
    for n, row in enumerate(CLUB_INFO, 2):
        where = f"data/club-info.csv line {n}"
        cid = row["id"]
        if cid not in CLUB_BY_ID:
            errs.append(f"{where}: id {cid!r} isn't in clubs.csv")
        if cid in INFO_BY_CLUB:
            errs.append(f"{where}: {cid} appears more than once")
        try:
            date.fromisoformat(row["updated"])
        except ValueError:
            errs.append(f"{where}: updated must be a real date, YYYY-MM-DD")
        if row["claimed"] not in ("yes", "no"):
            errs.append(f"{where}: claimed must be yes or no")
        if row["claimed"] == "yes" and not row["verified_by"].strip():
            errs.append(f"{where}: a claimed listing needs verified_by")
        if row["claimed"] == "no" and not row["source_url"].startswith("https://"):
            errs.append(f"{where}: details not sent by the club need the club's own page in source_url")
        if row["min_age"] not in ("", "18", "21"):
            errs.append(f"{where}: min_age must be 18, 21 or blank")
        if row["worker_status"] not in ("", *WORKER_STATUS):
            errs.append(f"{where}: worker_status must be employee, contractor, both or blank")
        for f in YES_NO_FIELDS:
            if row[f] not in ("", "yes", "no"):
                errs.append(f"{where}: {f} must be yes, no or blank")
        if row["apply_url"] and not row["apply_url"].startswith("https://"):
            errs.append(f"{where}: apply_url must start with https://")
        if row["booking_line"] and not re.fullmatch(r"\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}", row["booking_line"].strip()):
            errs.append(f"{where}: booking_line must be a 10-digit U.S. phone number, such as 614-555-0100")
        if row["claimed"] != "yes" and any(row[f].strip() for f in CLUB_ONLY_FIELDS):
            errs.append(f"{where}: booking_line and audition_hours come only from a club we've confirmed (claimed = yes)")
        if (row["hiring"] == "yes" or any(row[f].strip() for f in HIRING_FIELDS[1:])) and \
                not all(row[f].strip() for f in TERMS_FIELDS):
            errs.append(f"{where}: a hiring notice, booking line or audition hours need worker_status, "
                        "house_fee and tip_out published")
        INFO_BY_CLUB[cid] = row
    if errs:
        raise SystemExit("Club info problems:\n" + "\n".join(errs))


check_club_info()

# Anonymous dancer pay reports: numbers and dates only, no names and no free text.
# See METHODOLOGY.md section 9. Nothing for a club is shown until it has
# DANCER_REPORT_MIN separate reports from the last DANCER_REPORT_MONTHS months.
DANCER_REPORTS = read_csv("data/dancer-reports.csv")
SHIFTS = OrderedDict([("weekday-day", "Weekday day"), ("weekday-night", "Weekday night"),
                      ("weekend-day", "Weekend day"), ("weekend-night", "Weekend night")])
REPORT_NUMBERS = [
    ("house_fee", "House fee for the shift"),
    ("tip_out", "Tips to staff for the shift (DJ, house mom, security and others)"),
    ("dance_price", "Price of one private dance"),
    ("dancer_share", "What the dancer kept from one private dance"),
]
FEE_RISES = OrderedDict([("yes", "yes"), ("no", "no"), ("unsure", "not sure")])
PAY_TYPES = OrderedDict([("employee", "employee"), ("contractor", "contractor"), ("unsure", "not sure")])
REPORTS_BY_CLUB = {}


def check_dancer_reports():
    errs, ids = [], set()
    for n, row in enumerate(DANCER_REPORTS, 2):
        where = f"data/dancer-reports.csv line {n}"
        if row["report_id"] in ids or not re.fullmatch(r"R-\d{4,}", row["report_id"]):
            errs.append(f"{where}: report_id must be unique, like R-0001")
        ids.add(row["report_id"])
        if row["club_id"] not in CLUB_BY_ID:
            errs.append(f"{where}: club_id {row['club_id']!r} isn't in clubs.csv")
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", row["month"]):
            errs.append(f"{where}: month must be YYYY-MM")
        if row["shift"] not in ("", *SHIFTS):
            errs.append(f"{where}: shift must be one of {', '.join(SHIFTS)} or blank")
        for f, _label in REPORT_NUMBERS:
            if row[f] and not re.fullmatch(r"\d{1,5}", row[f]):
                errs.append(f"{where}: {f} must be whole dollars or blank")
        if row["fines"] not in ("", "yes", "no"):
            errs.append(f"{where}: fines must be yes, no or blank")
        if row["arrival"] and not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", row["arrival"]):
            errs.append(f"{where}: arrival must be a 24-hour time like 21:30, or blank")
        if row["fee_rises_late"] not in ("", *FEE_RISES):
            errs.append(f"{where}: fee_rises_late must be one of {', '.join(FEE_RISES)} or blank")
        if row["pay_type"] not in ("", *PAY_TYPES):
            errs.append(f"{where}: pay_type must be one of {', '.join(PAY_TYPES)} or blank")
        try:
            date.fromisoformat(row["added"])
        except ValueError:
            errs.append(f"{where}: added must be a real date, YYYY-MM-DD")
        REPORTS_BY_CLUB.setdefault(row["club_id"], []).append(row)
    if errs:
        raise SystemExit("Dancer report problems:\n" + "\n".join(errs))


check_dancer_reports()


def report_cutoff():
    """The first month that still counts: DANCER_REPORT_MONTHS back from this month."""
    t = date.today()
    m = t.year * 12 + (t.month - 1) - (DANCER_REPORT_MONTHS - 1)
    return f"{m // 12:04d}-{m % 12 + 1:02d}"


def month_name(ym):
    y, m = ym.split("-")
    return f"{date(int(y), int(m), 1):%b} {y}"


def clock(minutes):
    """Minutes after midnight (may run past 24 hours) as a 12-hour time like 9:30 PM."""
    h, m = divmod(minutes % (24 * 60), 60)
    return f"{h % 12 or 12}{':%02d' % m if m else ''} {'AM' if h < 12 else 'PM'}"


def answer_counts(rows, field, labels):
    """Like "yes in 3, no in 1 (4 reports)", or None with fewer than DANCER_REPORT_MIN answers."""
    vals = [r[field] for r in rows if r[field]]
    if len(vals) < DANCER_REPORT_MIN:
        return None
    parts = [f"{label} in {vals.count(k)}" for k, label in labels.items() if vals.count(k)]
    return f"{', '.join(parts)} ({len(vals)} reports)"


def dancer_summary(club_id):
    """Ranges from recent reports, or None when there aren't enough to show anything."""
    recent = [r for r in REPORTS_BY_CLUB.get(club_id, []) if r["month"] >= report_cutoff()]
    if len(recent) < DANCER_REPORT_MIN:
        return None
    lines = []
    for f, label in REPORT_NUMBERS:
        vals = sorted(int(r[f]) for r in recent if r[f])
        if len(vals) < DANCER_REPORT_MIN:
            continue
        half = len(vals) // 2
        mid = vals[half] if len(vals) % 2 else (vals[half - 1] + vals[half]) / 2
        lines.append((label, f"${vals[0]:,} to ${vals[-1]:,}, middle ${mid:,.0f} ({len(vals)} reports)"))
    fines = [r["fines"] for r in recent if r["fines"]]
    if len(fines) >= DANCER_REPORT_MIN:
        lines.append(("Fines charged", f"{fines.count('yes')} of {len(fines)} reports"))
    rises = answer_counts(recent, "fee_rises_late", FEE_RISES)
    if rises:
        lines.append(("House fee goes up for arriving later", rises))
    # Arrival times before 6 AM count as the end of the night before, so a range
    # like 9 PM to 1 AM sorts the way a night shift runs.
    arrive = sorted(int(a[:2]) * 60 + int(a[3:]) + (24 * 60 if a < "06:00" else 0)
                    for a in (r["arrival"] for r in recent) if a)
    if len(arrive) >= DANCER_REPORT_MIN:
        lines.append(("Arrival times reported", f"{clock(arrive[0])} to {clock(arrive[-1])} ({len(arrive)} reports)"))
    paid = answer_counts(recent, "pay_type", PAY_TYPES)
    if paid:
        lines.append(("Paid as", paid))
    months = sorted(r["month"] for r in recent)
    return {"count": len(recent), "span": f"{month_name(months[0])} to {month_name(months[-1])}",
            "lines": lines}


def club_page_name(club_id):
    return f"club-{club_id.lower()}.html"


def has_terms(info):
    return bool(info) and all(info[f].strip() for f in TERMS_FIELDS)


def info_is_stale(info):
    return (date.today() - date.fromisoformat(info["updated"])).days > CLUB_INFO_STALE_DAYS


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


def state_page_name(st):
    return f"state-{st.lower()}.html"


def state_links():
    counts = Counter(c["state"] for c in CLUBS)
    return '<ul class="statelist">' + "".join(
        f'<li><a href="{state_page_name(s)}">{e(STATE_NAMES.get(s, s))}</a> '
        f'<span class="n">{plural(counts[s], "club")}</span></li>' for s in states_in_data()) + "</ul>"


_LAW_ANCHORS = {}


def law_anchor(st):
    """The state's section of the laws guide, if it has one."""
    if not _LAW_ANCHORS:
        _t, _d, body = render_md("guides/laws-by-state.md")
        for hid, text in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body):
            text = re.sub(r"<[^>]+>", "", text)
            for code, name in STATE_NAMES.items():
                if text == name or text.startswith(name + " "):
                    _LAW_ANCHORS[code] = hid
        _LAW_ANCHORS.setdefault("", "")
    return _LAW_ANCHORS.get(st)


def source_links(sources):
    links = []
    for i, url in enumerate([s.strip() for s in sources.split("|") if s.strip()], 1):
        host = re.sub(r"^www\.", "", re.sub(r"^https?://([^/]+).*$", r"\1", url))
        links.append(f'<a href="{e(url)}">{e(host)}<span class="sr"> (source {i})</span></a>')
    return ", ".join(links) if links else "None"


def info_badges(club_id):
    info = INFO_BY_CLUB.get(club_id)
    if not info:
        return ""
    out = badge("Club details", "info", "info")
    if has_terms(info):
        out += " " + badge("Dancer terms published", "check-circle", "ok")
    return f'<span class="sub">{out}</span>'


def sa_badge(club_id):
    pl = SA_BY_CLUB.get(club_id)
    if not pl:
        return ""
    label, ic, tone = SA_LISTS[pl["list"]]
    return (f'<span class="sub"><a href="stay-away.html#{e(pl["place_id"])}">{badge(label, ic, tone)}'
            f'<span class="sr"> list: see why</span></a></span>')


def directory_page():
    clubs = sorted(CLUBS, key=lambda c: (STATE_NAMES.get(c["state"], c["state"]), c["city"], c["name"]))
    st_counts = Counter(c["status"] for c in CLUBS)
    rows = []
    for c in clubs:
        s_label, s_icon, s_tone = STATUS.get(c["status"], (c["status"], "question", "muted"))
        f_label, f_icon, f_tone = FLAG.get(c["overall_flag"], (c["overall_flag"], "question", "muted"))
        n = len(RECORDS_BY_CLUB.get(c["id"], []))
        recs = (f'<a href="{club_page_name(c["id"])}#record">{plural(n, "record")}'
                f'<span class="sr"> for {e(c["name"])}</span></a>') if n else "None yet"
        operator = f'<span class="sub">Operator: {e(c["operator"])}</span>' if c["operator"] else ""
        address = f'<span class="sub">{e(c["address"])}</span>' if c["address"] else ""
        notes = f'<span class="sub">{e(c["notes"])}</span>' if c["notes"] else ""
        search_text = " ".join([c["name"], c["city"], c["state"], STATE_NAMES.get(c["state"], ""),
                                c["operator"]]).lower()
        rows.append(
            f'<tr id="{e(c["id"])}" data-state="{e(c["state"])}" data-status="{e(c["status"])}" '
            f'data-text="{e(search_text)}">'
            f'<th scope="row"><a class="clubname" href="{club_page_name(c["id"])}">{e(c["name"])}</a>'
            f'{sa_badge(c["id"])}{info_badges(c["id"])}{address}{operator}{notes}</th>'
            f'<td>{e(c["city"])}</td><td><a href="{state_page_name(c["state"])}"><abbr title="{e(STATE_NAMES.get(c["state"], c["state"]))}">{e(c["state"])}</abbr></a></td>'
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
<p class="lead">{len(CLUBS)} clubs in {len(states_in_data())} states and territories so far, built from public records. Every listing links to its source.</p>
<div class="callout">{icon("info")}<p>A listing is not an endorsement, and "not reviewed" means we haven't finished checking, not that a club is safe or unsafe. See <a href="method.html">how we rate clubs</a>. Something wrong? <a href="about.html#corrections">Send a correction</a>.</p></div>
<p>{icon("octagon")} Clubs marked Stay away or Use caution are on our <a href="stay-away.html">list of places tied to trafficking or sexual exploitation</a> in court and agency records.</p>

<h2 id="by-state">Browse by state</h2>
{state_links()}

<h2 id="all-clubs">All clubs</h2>

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
<p>Download the data: <a href="data/clubs.csv" download>clubs.csv</a>, <a href="data/evidence.csv" download>evidence.csv</a>, <a href="data/club-info.csv" download>club-info.csv</a>, <a href="data/house-fees.csv" download>house-fees.csv</a> and <a href="data/dancer-reports.csv" download>dancer-reports.csv</a>. Field definitions are on the <a href="data.html">data page</a>.</p>
"""
    return page("directory.html", "Club directory",
                f"A sourced directory of {len(CLUBS)} U.S. strip clubs, with status and public records for each.", body,
                wide=True)


RECORD_GROUPS = [
    ("conviction", "Convictions", "octagon",
     "The most serious record. A criminal court found guilt or passed sentence."),
    ("finding", "Court and agency findings", "scale",
     "A ruling on the facts. A court judgment, an agency fine, or a permit revoked or denied."),
    ("government-action", "Government and license actions", "building",
     "Not a final ruling. An agency objected, cited, raided or investigated."),
    ("settlement", "Settlements", "file",
     "A settlement isn't an admission. The case ended with a payment, and nobody was found liable unless the record says so."),
    ("allegation", "Lawsuits and charges", "alert",
     "Charged is not convicted. A lawsuit is a claim, not a finding."),
    ("incident", "Incidents", "info",
     "No finding against the club. Police or news reported it."),
    ("closure", "Closures", "x-circle", "Closed. A source reports the club closed."),
    ("positive", "Good practices on record", "check-circle",
     "Something done right. A published policy, completed training or a standard met."),
]


def plural(n, word, words=None):
    return f"{n:,} {word if n == 1 else (words or word + 's')}"


def records_page():
    groups = [g for g in RECORD_GROUPS if any(r["type"] == g[0] for r in EVIDENCE)]
    known = {g[0] for g in RECORD_GROUPS}
    other = [r for r in EVIDENCE if r["type"] not in known]
    if other:
        raise SystemExit(f"records page: no group for record type {other[0]['type']!r}")
    sections, toc = [], []
    for rtype, title, ic, plain in groups:
        recs = sorted((r for r in EVIDENCE if r["type"] == rtype), key=lambda r: r["date"] or "0", reverse=True)
        rows = []
        for r in recs:
            club = CLUB_BY_ID[r["club_id"]]
            src = (f'<a href="{e(r["source_url"])}">{e(SOURCE_TYPE.get(r["source_type"], r["source_type"]))}'
                   f'<span class="sr"> source for this record about {e(club["name"])}</span></a>')
            checked = "Yes" if r["primary_confirmed"] == "yes" else "Not yet"
            where = ", ".join(x for x in [club["city"], club["state"]] if x)
            rows.append(
                f'<tr data-state="{e(club["state"])}">'
                f'<th scope="row"><a class="clubname" href="{club_page_name(club["id"])}">{e(club["name"])}</a>'
                f'<span class="sub">{e(where)}</span></th>'
                f'<td>{e(r["date"] or "Date to confirm")}</td>'
                f'<td>{e(DIMENSION.get(r["dimension"], r["dimension"]))}</td>'
                f'<td>{e(r["summary"])}</td><td>{src}</td><td>{checked}</td></tr>')
        gid = f"g-{rtype}"
        toc.append(f'<li><a href="#{gid}">{e(title)}</a> <span class="n">{plural(len(recs), "record")}</span></li>')
        first, _, rest = plain.partition(". ")
        sections.append(f"""
<section aria-labelledby="{gid}" data-group>
<h2 id="{gid}">{icon(ic)} {e(title)} <span class="where" data-count>{plural(len(recs), "record")}</span></h2>
<p class="plain"><b>{e(first.rstrip(".") + ".")}</b> {e(rest)}</p>
<div class="tablewrap" role="region" tabindex="0" aria-label="{e(title)}">
<table class="records"><thead><tr><th scope="col">Club</th><th scope="col">Date</th><th scope="col">Area</th><th scope="col">What the record says</th><th scope="col">Source</th><th scope="col">Checked against the primary record</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
</section>""")
    rec_states = sorted({CLUB_BY_ID[r["club_id"]]["state"] for r in EVIDENCE}, key=lambda s: STATE_NAMES.get(s, s))
    opts = "".join(f'<option value="{s}">{e(STATE_NAMES.get(s, s))}</option>' for s in rec_states)
    body = f"""
<h1>Public records</h1>
<p class="lead">{len(EVIDENCE)} records tied to {len(RECORDS_BY_CLUB)} clubs, the most serious first: convictions, then findings, then government and license actions, then settlements, then lawsuits and charges. Each one links to its source.</p>
<div class="callout">{icon("scale")}<p>Charged is not convicted. A lawsuit is a claim, not a finding. A settlement isn't an admission unless the record says so. Records name clubs and companies, never dancers, staff or customers. Records older than 5 years are history and don't set a rating. Clubs can <a href="about.html#corrections">respond to any record</a>.</p></div>

<nav aria-labelledby="toc-h" class="panel"><h2 id="toc-h">On this page</h2><ul>{"".join(toc)}</ul></nav>

<form id="recfilter" class="filters" hidden role="search" aria-label="Filter the records">
  <div><label for="r-state">State</label><select id="r-state" name="state"><option value="">All states</option>{opts}</select></div>
</form>
<p id="rshown" role="status" class="shown">Showing all {len(EVIDENCE)} records.</p>
{"".join(sections)}
<p>Download the records: <a href="data/evidence.csv" download>evidence.csv</a>. Field definitions are on the <a href="data.html">data page</a>.</p>
"""
    return page("records.html", "Public records",
                f"{len(EVIDENCE)} sourced public records tied to specific clubs: convictions, findings, government actions, settlements and lawsuits.",
                body, wide=True)


MONTHS = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]


def nice_date(d):
    parts = d.split("-")
    if len(parts) == 3:
        return f"{MONTHS[int(parts[1]) - 1]} {int(parts[2])}, {parts[0]}"
    if len(parts) == 2:
        return f"{MONTHS[int(parts[1]) - 1]} {parts[0]}"
    return d


def sa_where(pl):
    return ", ".join(x for x in [pl["city"], STATE_NAMES.get(pl["state"], pl["state"])] if x)


def sa_name(pl):
    return pl["names"].split(";")[0].strip()


def sa_place(pl):
    pid = pl["place_id"]
    recs = sorted(SA_RECS_BY_PLACE[pid], key=lambda r: r["date"])
    label, ic, tone = SA_LISTS[pl["list"]]
    names = [n.strip() for n in pl["names"].split(";") if n.strip()]
    newest = max(r["date"] for r in recs)
    cutoff = str(date.today().year - 5) + date.today().isoformat()[4:]
    badges = [badge(label, ic, tone), badge(SA_KINDS[pl["kind"]], "building", "muted")]
    if newest < cutoff[:len(newest)]:
        badges.append(badge("History: newest record over 5 years old", "info", "muted"))
    facts = []
    if len(names) > 1:
        facts.append(("Other names on the record", e("; ".join(names[1:]))))
    if pl["address"]:
        facts.append(("Address on the record", e(pl["address"])))
    if pl["operators"]:
        facts.append(("Companies named", e(pl["operators"])))
    if pl["club_id"]:
        c = CLUB_BY_ID[pl["club_id"]]
        facts.append(("In our directory", f'<a href="{club_page_name(c["id"])}">{e(c["name"])}</a>'))
    dl = f'<dl class="facts">{"".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in facts)}</dl>' if facts else ""
    items = []
    for i, r in enumerate(recs, 1):
        tlabel, ttone = SA_TYPES[r["type"]]
        src = (f'<a href="{e(r["source_url"])}">{e(SOURCE_TYPE.get(r["source_type"], r["source_type"]))}'
               f'<span class="sr">: source for record {i} on {e(sa_name(pl))}</span></a>')
        items.append(f'<li><span class="when"><time datetime="{e(r["date"])}">{e(nice_date(r["date"]))}</time></span> '
                     f'<span class="rkind {ttone}">{e(tlabel)}</span> <span class="what">{e(r["summary"])}</span> '
                     f'<span class="src">Source: {src}</span></li>')
    return f"""<article class="sa {tone}" id="{e(pid)}" data-state="{e(pl["state"])}" aria-labelledby="{e(pid)}-h">
<h3 id="{e(pid)}-h">{e(sa_name(pl))} <span class="where">{e(sa_where(pl))}</span></h3>
<p class="badges">{" ".join(badges)}</p>
<p class="why">{e(pl["why"])}</p>
{dl}
<h4 class="sr">Records for {e(sa_name(pl))}, oldest first</h4>
<ol class="timeline">{"".join(items)}</ol>
</article>"""


def stay_away_page():
    def sort_key(pl):
        return (STATE_NAMES.get(pl["state"], pl["state"]), pl["city"], sa_name(pl))
    convicted = [pl for pl in SA_PLACES if pl["list"] == "stay-away"
                 and any(r["type"] == "conviction" for r in SA_RECS_BY_PLACE[pl["place_id"]])]
    closed = [pl for pl in SA_PLACES if pl["list"] == "stay-away" and pl not in convicted]
    caution = [pl for pl in SA_PLACES if pl["list"] == "caution"]
    reopened = [pl for pl in SA_PLACES if any(r["type"] == "reopening" for r in SA_RECS_BY_PLACE[pl["place_id"]])]
    n_stay = len(convicted) + len(closed)
    groups = [
        ("g-convicted", "Stay away: convictions", "octagon", convicted,
         "Someone was convicted or pleaded guilty over trafficking, forced labor or prostitution tied to the place. Each entry says who: the owner, a manager, or an outside trafficker who brought victims there."),
        ("g-closed", "Stay away: closure orders and revocations", "x-circle", closed,
         "A court or agency closed the place or took its license over prostitution, trafficking or exploiting a minor. Some were agreed orders without an admission, and each entry says so."),
        ("g-caution", "Use caution", "alert", caution,
         "There's a charge, a suspension or a temporary order, or a conviction on other counts, but no trafficking or prostitution conviction or final closure on the record we've read. Charged is not convicted, and a charge may end with no finding."),
    ]
    toc, sections = [], []
    for gid, title, ic, items, plain in groups:
        toc.append(f'<li><a href="#{gid}">{e(title)}</a> <span class="n">{plural(len(items), "place")}</span></li>')
        first, _, rest = plain.partition(". ")
        arts = "\n".join(sa_place(pl) for pl in sorted(items, key=sort_key))
        sections.append(f"""<section aria-labelledby="{gid}" data-sagroup>
<h2 id="{gid}">{icon(ic)} {e(title)} <span class="where" data-count>{plural(len(items), "place")}</span></h2>
<p class="plain"><b>{e(first.rstrip(".") + ".")}</b> {e(rest)}</p>
{arts}
</section>""")
    re_items = "".join(
        f'<li><a href="#{e(pl["place_id"])}">{e(sa_name(pl))}, {e(sa_where(pl))}</a>: '
        f'{e(next(r["summary"] for r in SA_RECS_BY_PLACE[pl["place_id"]] if r["type"] == "reopening"))}</li>'
        for pl in sorted(reopened, key=sort_key))
    states = sorted({pl["state"] for pl in SA_PLACES}, key=lambda s: STATE_NAMES.get(s, s))
    opts = "".join(f'<option value="{s}">{e(STATE_NAMES.get(s, s))}</option>' for s in states)
    n_recs = len(SA_RECORDS)
    body = f"""
<h1>Places to stay away from</h1>
<p class="lead">{len(SA_PLACES)} strip clubs, hostess bars and cantinas tied to trafficking or sexual exploitation in court and government records. Each one lists its records, oldest first, with a link to the source.</p>
<div class="callout">{icon("scale")}<p>We list a place only on a primary record: a conviction or guilty plea, a court or nuisance order, a license action, or a government release. Never on rumor, reviews or anonymous tips. Convictions and charges are labeled apart, because charged is not convicted. A place may have changed hands since, and each entry says what the record shows about that. Records name places and companies, never dancers or other workers. Owners can <a href="about.html#corrections">respond to any entry</a>.</p></div>

<ul class="stats">
<li><b>{n_stay}</b> <span>to stay away from</span></li>
<li><b>{len(caution)}</b> <span>to use caution with</span></li>
<li><b>{len(reopened)}</b> <span>reopened or kept operating</span></li>
<li><b>{n_recs}</b> <span>records, each with its source</span></li>
</ul>

<p>{icon("alert")} Why do these places keep coming back, and why is it so hard to stop? <a href="why-it-keeps-happening.html">Read how it works and how to get help</a>.</p>

<nav aria-labelledby="toc-h" class="panel"><h2 id="toc-h">On this page</h2><ul>
<li><a href="#g-reopened">Reopened or kept operating</a> <span class="n">{plural(len(reopened), "place")}</span></li>
{"".join(toc)}
<li><a href="#how-we-decide">How we decide</a></li>
<li><a href="#help">Get help or report</a></li>
</ul></nav>

<section aria-labelledby="g-reopened" class="panel">
<h2 id="g-reopened">{icon("alert")} Reopened or kept operating</h2>
<p>A court record shows these places opened again at the same address, or kept running after an order to shut. Both are also listed below.</p>
<ul>{re_items}</ul>
</section>

<form id="safilter" class="filters" hidden role="search" aria-label="Filter the list">
  <div><label for="sa-state">State</label><select id="sa-state" name="state"><option value="">All states and territories</option>{opts}</select></div>
</form>
<p id="sashown" role="status" class="shown">Showing all {len(SA_PLACES)} places.</p>

{"".join(sections)}

<section aria-labelledby="how-we-decide">
<h2 id="how-we-decide">How we decide</h2>
<ul>
<li><b>Stay away</b> needs a conviction or guilty plea tied to the place, a court closure or nuisance order, or a license revoked or given up, over trafficking, forced labor, prostitution run or allowed by the business, or a minor exploited there.</li>
<li><b>Use caution</b> is for a charge, a license suspension or a temporary order on the same grounds, or a conviction on other counts where the record describes sex for money at the place. A charge may end with no finding.</li>
<li><b>Reopened</b> needs a record that shows the same address, not just a similar name. A club with a similar name somewhere else isn't the same place.</li>
<li><b>Records older than 5 years</b> are marked as history. A place listed for an old case may be under new owners now.</li>
<li><b>Not here yet:</b> news reports name dozens more places. They wait until we find a court or agency record, because a news story alone doesn't list a place.</li>
</ul>
<p>The full rules are in <a href="method.html#10-the-stay-away-list">how we rate</a>. Download the list: <a href="data/stay-away.csv" download>stay-away.csv</a> and <a href="data/stay-away-records.csv" download>stay-away-records.csv</a>. Field definitions are on the <a href="data.html#stay-awaycsv">data page</a>.</p>
</section>

<section aria-labelledby="help" class="callout">
{icon("phone")}<div><h2 id="help">Get help or report</h2>
<p>If someone is in danger, call <a href="tel:911">911</a>. To report trafficking or get help, call the National Human Trafficking Hotline at <a href="tel:+18883737888">1-888-373-7888</a>, text <a href="sms:233733">233733</a>, or chat at <a href="https://humantraffickinghotline.org/">humantraffickinghotline.org</a>. It's free, confidential and open all day, every day.</p>
<p>To tip off federal investigators, call the HSI Tip Line at <a href="tel:+18663472423">1-866-347-2423</a>. For a child, call the National Center for Missing and Exploited Children at <a href="tel:+18008435678">1-800-843-5678</a>.</p>
<p><a href="why-it-keeps-happening.html#getting-help">More on what happens when you call</a></p></div>
</section>
"""
    return page("stay-away.html", "Places to stay away from",
                f"{n_stay} strip clubs, hostess bars and cantinas to stay away from and {len(caution)} to use caution with, from convictions, closure orders and license actions over trafficking and sexual exploitation. Every entry is sourced.",
                body, wide=True)


def records_table(club, recs):
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
    return (f'<div class="tablewrap" role="region" tabindex="0" aria-label="Records for {e(club["name"])}">'
            '<table class="records"><thead><tr><th scope="col">Date</th><th scope="col">Area</th>'
            '<th scope="col">Type</th><th scope="col">What the record says</th><th scope="col">Source</th>'
            '<th scope="col">Checked against the primary record</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def info_value(field, value):
    if field == "min_age":
        return f"{e(value)} and up"
    if field == "worker_status":
        return e(WORKER_STATUS[value])
    if field in YES_NO_FIELDS:
        return "Yes" if value == "yes" else "No"
    if field == "apply_url":
        host = re.sub(r"^www\.", "", re.sub(r"^https?://([^/]+).*$", r"\1", value))
        return f'<a href="{e(value)}">The club\'s application page<span class="sr"> on {e(host)}</span></a>'
    if field == "booking_line":
        digits = re.sub(r"\D", "", value)
        return f'<a href="tel:+1{digits}">{e(value)}</a> <span class="sub">The club\'s own line</span>'
    return e(value)


def club_info_section(c):
    info = INFO_BY_CLUB.get(c["id"])
    claim = f'claim.html?club={e(c["id"])}'
    if not info:
        return f"""<section aria-labelledby="says">
<h2 id="says">What the club says</h2>
<p>This club hasn't given us its hours, prices or dancer terms yet.</p>
<p><a class="btnlink" href="{claim}">{icon("building")}<span>Is this your club? Add your details, free</span></a></p>
</section>"""
    if info["claimed"] == "yes":
        origin = f'Sent by the club and confirmed by {e(info["verified_by"])}. Last updated {e(info["updated"])}.'
    else:
        host = re.sub(r"^www\.", "", re.sub(r"^https?://([^/]+).*$", r"\1", info["source_url"]))
        origin = (f'From the club\'s own page at <a href="{e(info["source_url"])}">{e(host)}</a>, '
                  f'checked {e(info["updated"])}. The club hasn\'t claimed this listing yet.')
    stale = (f'<p>{badge("May be out of date", "alert", "warn")} These details are more than '
             f'{CLUB_INFO_STALE_DAYS} days old.</p>') if info_is_stale(info) else ""
    groups = []
    for title, ic, fields in CLUB_INFO_GROUPS:
        items = [(label, info_value(f, info[f])) for f, label in fields if info[f].strip()]
        if title == "Dancers":
            hide = set()
            if not has_terms(info):
                hide |= set(HIRING_FIELDS)
            if info["claimed"] != "yes":
                hide |= set(CLUB_ONLY_FIELDS)
            items = [(label, info_value(f, info[f])) for f, label in fields
                     if info[f].strip() and f not in hide]
        if not items:
            continue
        dl = "".join(f"<dt>{e(label)}</dt><dd>{val}</dd>" for label, val in items)
        gid = "says-" + title.lower()
        groups.append(f'<h3 id="{gid}">{icon(ic)} {e(title)}</h3><dl class="facts">{dl}</dl>')
    terms = (f'<p>{badge("Dancer terms published", "check-circle", "ok")} This club has published how dancers '
             f'are classified, its house fee and its tip-out.</p>') if has_terms(info) else ""
    return f"""<section aria-labelledby="says">
<h2 id="says">What the club says</h2>
<div class="callout">{icon("info")}<p>These are the club's own words. We don't vouch for them, and they never change the rating. {origin}</p></div>
{stale}{terms}
{"".join(groups)}
<p><a href="{claim}">Is this your club? Update these details</a></p>
</section>"""


def club_page(c):
    s_label, s_icon, s_tone = STATUS.get(c["status"], (c["status"], "question", "muted"))
    f_label, f_icon, f_tone = FLAG.get(c["overall_flag"], (c["overall_flag"], "question", "muted"))
    where = ", ".join(x for x in [c["city"], STATE_NAMES.get(c["state"], c["state"])] if x)
    facts = [("Status", badge(s_label, s_icon, s_tone)), ("Rating", badge(f_label, f_icon, f_tone))]
    if c["address"]:
        facts.append(("Address", e(c["address"])))
    if c["operator"]:
        facts.append(("Operator", e(c["operator"])))
    if c["alcohol"] in ("yes", "no", "byob"):
        facts.append(("Alcohol", {"yes": "Serves alcohol", "no": "No alcohol", "byob": "Bring your own"}[c["alcohol"]]))
    if c["website"]:
        facts.append(("Website", f'<a href="{e(c["website"])}">{e(c["website"])}</a>'))
    facts.append(("Last researched", e(c["last_researched"] or "Not yet")))
    facts.append(("Sources", source_links(c["sources"])))
    if c["notes"]:
        facts.append(("Notes", e(c["notes"])))
    dl = "".join(f"<dt>{e(k)}</dt><dd>{v}</dd>" for k, v in facts)
    recs = RECORDS_BY_CLUB.get(c["id"], [])
    sa = SA_BY_CLUB.get(c["id"])
    if recs:
        rec_html = records_table(c, recs)
    elif sa:
        rec_html = (f'<p>Its court and agency records are on the '
                    f'<a href="stay-away.html#{e(sa["place_id"])}">stay-away list</a>.</p>')
    else:
        rec_html = "<p>No public records tied to this club yet.</p>"
    sa_html = ""
    if sa:
        label, ic, tone = SA_LISTS[sa["list"]]
        sa_html = (f'<div class="callout sa-note {tone}">{icon(ic)}<p><b>On our {e(label)} list.</b> {e(sa["why"])} '
                   f'<a href="stay-away.html#{e(sa["place_id"])}">See the records and sources</a>.</p></div>')
    body = f"""
<p class="back"><a href="directory.html#{e(c["id"])}">Back to the directory</a> <span aria-hidden="true">|</span> <a href="{state_page_name(c["state"])}">More clubs in {e(STATE_NAMES.get(c["state"], c["state"]))}</a></p>
<h1>{e(c["name"])}</h1>
<p class="lead">{e(where)}</p>

<section aria-labelledby="record">
<h2 id="record">Our record</h2>
{sa_html}
<dl class="facts">{dl}</dl>
<h3 id="records-h">Public records</h3>
{rec_html}
<p>A lawsuit or a charge is an allegation, not a finding. See <a href="method.html">how we rate clubs</a>, or <a href="about.html#corrections">send a correction</a>.</p>
</section>

{dancer_reports_section(c)}

{club_info_section(c)}
"""
    title = f'{c["name"]}, {c["city"]}' if c["city"] else c["name"]
    return page(club_page_name(c["id"]), title,
                f'{c["name"]} in {where}: listing status, public records, what dancers report, and details from the club itself.', body)


def dancer_reports_section(c):
    summary = dancer_summary(c["id"])
    if summary:
        dl = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in summary["lines"])
        inner = (f'<div class="callout">{icon("info")}<p>From {plural(summary["count"], "anonymous dancer report")}, '
                 f'{e(summary["span"])}. These are dancers\' numbers, not ours, and they never change the rating. '
                 f'One dancer\'s report is never shown on its own.</p></div><dl class="facts">{dl}</dl>')
    else:
        inner = (f"<p>Not enough reports yet. We show dancers' numbers for a club once {DANCER_REPORT_MIN} dancers "
                 f"have reported in the last {DANCER_REPORT_MONTHS} months.</p>")
    return f"""<section aria-labelledby="dancers-say">
<h2 id="dancers-say">What dancers report</h2>
{inner}
<p><a href="{report_link(c)}">Dance here? Report this club's fees anonymously</a></p>
</section>"""


def report_link(c):
    """The anonymous form with this club filled in, or the dancer pay page until the form is open."""
    return f"{DANCER_FORM_URL}?club_id={c['id']}" if DANCER_FORM_URL else "dancer-pay.html#dancer-reports"


CLAIM_ASK = [
    ("About you", [
        ("claimant_name", "Your name", "text", True),
        ("claimant_role", "Your role at the club", "text", True),
        ("claimant_phone", "Phone number", "tel", True),
        ("claimant_email", "Email", "email", True),
    ]),
    ("Visiting", [(f, label, "text", False) for f, label in CLUB_INFO_GROUPS[0][2]]),
    ("Dancers", [(f, label, "text", False) for f, label in CLUB_INFO_GROUPS[1][2]]),
    ("Safety", [(f, label, "text", False) for f, label in CLUB_INFO_GROUPS[2][2]]),
]
FIELD_HINTS = {
    "booking_line": "The club's own public number for getting on the schedule. Never anyone's personal phone.",
    "audition_hours": "Days and times, and the role to ask for, such as \u201cTuesdays 2 to 5 p.m., ask for the day manager.\u201d No names.",
}
SELECT_CHOICES = {
    "min_age": [("", "Choose"), ("18", "18 and up"), ("21", "21 and up")],
    "worker_status": [("", "Choose"), ("employee", "Employees"), ("contractor", "Independent contractors"),
                      ("both", "Some of each")],
    **{f: [("", "Choose"), ("yes", "Yes"), ("no", "No")] for f in YES_NO_FIELDS},
}


def claim_form():
    clubs = sorted(CLUBS, key=lambda c: (STATE_NAMES.get(c["state"], c["state"]), c["city"], c["name"]))
    opts = "".join(f'<option value="{e(c["id"])}">{e(c["name"])}, {e(c["city"])}, {e(c["state"])}</option>'
                   for c in clubs if c["status"] != "closed")
    fieldsets = [f"""<fieldset><legend>Your club</legend>
<div class="field"><label for="club">Club</label><select id="club" name="club" required><option value="">Choose your club</option>{opts}<option value="new">My club isn't listed</option></select></div>
<div class="field"><label for="club_new">If it isn't listed: club name, city and state</label><input id="club_new" name="club_new" type="text"></div>
</fieldset>"""]
    for legend, fields in CLAIM_ASK:
        rows = []
        for f, label, typ, req in fields:
            r = " required" if req else ""
            auto = {"claimant_name": "name", "claimant_phone": "tel", "claimant_email": "email"}.get(f)
            ac = f' autocomplete="{auto}"' if auto else ""
            if f in SELECT_CHOICES:
                o = "".join(f'<option value="{v}">{e(t)}</option>' for v, t in SELECT_CHOICES[f])
                ctl = f'<select id="{f}" name="{f}"{r}>{o}</select>'
            else:
                t = {"apply_url": "url", "booking_line": "tel"}.get(f, typ)
                ctl = f'<input id="{f}" name="{f}" type="{t}"{r}{ac}>'
            hint = ""
            if f in FIELD_HINTS:
                hint = f'<span class="hint" id="{f}-hint">{e(FIELD_HINTS[f])}</span>'
                ctl = ctl.replace(f'id="{f}"', f'id="{f}" aria-describedby="{f}-hint"', 1)
            rows.append(f'<div class="field"><label for="{f}">{e(label)}{" (required)" if req else ""}</label>{hint}{ctl}</div>')
        fieldsets.append(f'<fieldset><legend>{e(legend)}</legend>{"".join(rows)}</fieldset>')
    if CLAIM_FORM_URL:
        attrs = f'action="{e(CLAIM_FORM_URL)}" method="post"'
    else:
        attrs = f'action="mailto:{e(CLAIM_EMAIL)}?subject=Club%20listing%20claim" method="post" enctype="text/plain" data-mailto="{e(CLAIM_EMAIL)}"'
    return f"""<form id="claim" class="claimform" {attrs}>
{"".join(fieldsets)}
<p><button type="submit">Send my club's details</button></p>
</form>"""


def claim_page():
    if CLAIM_FORM_URL or CLAIM_EMAIL:
        note = ""
        if not CLAIM_FORM_URL:
            note = (f'<p>The button opens your email app with your details filled in. If it doesn\'t, email them to '
                    f'<a href="mailto:{e(CLAIM_EMAIL)}?subject=Club%20listing%20claim">{e(CLAIM_EMAIL)}</a>.</p>')
        form_html = f'<section aria-labelledby="form-h"><h2 id="form-h">Send your details</h2>{note}{claim_form()}</section>'
    else:
        asks = "".join(f'<li class="todo"><span class="box" aria-hidden="true"></span>{e(label)}</li>'
                       for _t, _i, fields in CLUB_INFO_GROUPS for _f, label in fields)
        form_html = f"""<section aria-labelledby="form-h" class="panel">
<h2 id="form-h">What we'll ask for</h2>
<p>The claim form opens soon. Every field is optional except who you are and how to reach you.</p>
<ul class="checklist">{asks}</ul>
</section>"""
    steps = [
        ("file", "Send your details", "Hours, prices and dancer terms, in the form below. It's free."),
        ("phone", "We confirm you speak for the club", "We call the club's public phone number, or match you to the liquor permit or business filing."),
        ("check-circle", "We publish them as the club's word", "Labeled \u201cWhat the club says,\u201d with the date, beside our own record."),
        ("list", "Keep them current", f"Send changes any time. Details older than {CLUB_INFO_STALE_DAYS} days are marked as possibly out of date."),
    ]
    step_html = "".join(f'<li><span class="pic">{icon(ic)}</span><span><b>{e(t)}</b> {e(d)}</span></li>' for ic, t, d in steps)
    body = f"""
<h1>Claim your club's listing</h1>
<p class="lead">Keep your hours, prices, dancer terms and booking line current in one place customers and dancers already check. It's free, and it never changes your rating.</p>

<section aria-labelledby="how-h">
<h2 id="how-h">How it works</h2>
<ol class="steps">{step_html}</ol>
</section>

<section aria-labelledby="rules-h">
<h2 id="rules-h">What we publish, and what we don't</h2>
<ul>
<li>Your details appear as your own words, never as our finding, and they never change your rating. <a href="method.html">Ratings come from public records</a>.</li>
<li>A hiring notice appears only when you also publish how dancers are classified, your house fee and your tip-out.</li>
<li>Your booking line and audition hours appear only after we confirm you speak for the club, and only with your dancer terms. Give the club's own number, never a personal phone, and a role to ask for, never a name. We never take these from dancer reports.</li>
<li>Prices are for what's on your posted menu: cover, drinks, dances and VIP time.</li>
<li>We never publish names, stage names, photos or contact details for dancers or staff.</li>
<li>We edit or remove anything false, explicit, or that suggests anything beyond legal entertainment.</li>
<li>Want to answer a public record instead? <a href="about.html#corrections">Send a response</a>.</li>
</ul>
</section>

{form_html}
"""
    return page("claim.html", "Claim your club's listing",
                "Club owners and managers: add your hours, prices and dancer terms to your listing, free. Your details never change your rating.",
                body)


def state_page(st):
    name = STATE_NAMES.get(st, st)
    clubs = sorted((c for c in CLUBS if c["state"] == st), key=lambda c: (c["city"], c["name"]))
    stc = Counter(c["status"] for c in clubs)
    open_n = stc.get("verified", 0) + stc.get("reported-open", 0)
    n_recs = sum(len(RECORDS_BY_CLUB.get(c["id"], [])) for c in clubs)
    with_recs = sum(1 for c in clubs if c["id"] in RECORDS_BY_CLUB)
    rows = []
    for c in clubs:
        s_label, s_icon, s_tone = STATUS.get(c["status"], (c["status"], "question", "muted"))
        f_label, f_icon, f_tone = FLAG.get(c["overall_flag"], (c["overall_flag"], "question", "muted"))
        n = len(RECORDS_BY_CLUB.get(c["id"], []))
        recs = (f'<a href="{club_page_name(c["id"])}#record">{plural(n, "record")}'
                f'<span class="sr"> for {e(c["name"])}</span></a>') if n else "None yet"
        operator = f'<span class="sub">Operator: {e(c["operator"])}</span>' if c["operator"] else ""
        rows.append(
            f'<tr><th scope="row"><a class="clubname" href="{club_page_name(c["id"])}">{e(c["name"])}</a>'
            f'{info_badges(c["id"])}{operator}</th><td>{e(c["city"])}</td>'
            f'<td>{badge(s_label, s_icon, s_tone)}</td><td>{badge(f_label, f_icon, f_tone)}</td><td>{recs}</td></tr>')
    anchor = law_anchor(st)
    if anchor:
        laws = f'<p>See <a href="laws.html#{anchor}">{e(name)} in our laws guide</a>: what the state allows and requires.</p>'
    else:
        laws = (f"<p>We haven't written up {e(name)}'s laws yet. Start with "
                f'<a href="laws.html#federal-baseline">the federal rules that apply everywhere</a>.</p>')
    extra = '<p>More on Ohio: <a href="ohio.html">our Ohio research notes</a>.</p>' if st == "OH" else ""
    records = ""
    if n_recs:
        records = (f'<section aria-labelledby="recs-h"><h2 id="recs-h">Public records</h2>'
                   f'<p>{plural(n_recs, "public record")} tied to {plural(with_recs, "club")} here. '
                   f'Each club\'s page lists its own. <a href="records.html?state={st}">See them on the records page</a>, '
                   f'most serious first.</p></section>')
    body = f"""
<p class="back"><a href="directory.html#by-state">All states</a></p>
<h1>Strip clubs in {e(name)}</h1>
<p class="lead">{plural(len(clubs), "club")} listed so far, {open_n} of them reported or verified open. Every listing links to its source.</p>
<ul class="stats">
<li><b>{len(clubs)}</b> <span>{"club" if len(clubs) == 1 else "clubs"} listed</span></li>
<li><b>{open_n}</b> <span>reported or verified open</span></li>
<li><b>{n_recs}</b> <span>public {"record" if n_recs == 1 else "records"}</span></li>
</ul>

<section aria-labelledby="clubs-h">
<h2 id="clubs-h">Clubs in {e(name)}</h2>
<div class="callout">{icon("info")}<p>A listing is not an endorsement, and "not reviewed" means we haven't finished checking, not that a club is safe or unsafe. See <a href="directory.html#status-key">what the status means</a> and <a href="directory.html#rating-key">what the rating means</a>.</p></div>
<div class="tablewrap" role="region" tabindex="0" aria-labelledby="state-cap">
<table class="dir">
<caption id="state-cap">Clubs in {e(name)}, by city</caption>
<thead><tr><th scope="col">Club</th><th scope="col">City</th><th scope="col">Status</th><th scope="col">Rating</th><th scope="col">Public records</th></tr></thead>
<tbody>{"".join(rows)}</tbody>
</table>
</div>
</section>
{records}
<section aria-labelledby="laws-h">
<h2 id="laws-h">The law in {e(name)}</h2>
{laws}
{extra}
</section>
<p>Know a club we're missing, or one that's closed? <a href="about.html#corrections">Send a correction</a>. Run one of these clubs? <a href="claim.html">Claim your listing</a>.</p>
"""
    return page(state_page_name(st), f"Strip clubs in {name}",
                f"{plural(len(clubs), 'strip club')} in {name}, with status, public records and sources for each.",
                body, wide=True)


HOUSE_FEES = read_csv("data/house-fees.csv")
FEE_BASIS = OrderedDict([
    ("law", "State law or rule"),
    ("court-finding", "Court finding"),
    ("settlement", "Settlement term. Not an admission."),
    ("alleged", "Alleged in a lawsuit"),
    ("dancer-account", "Dancers' account, as reported"),
    ("news", "News report"),
])


def fee_states(value):
    """Display name and sort key for the state column of house-fees.csv."""
    m = re.fullmatch(r"multi-state \((\d+)\)", value.strip())
    if m:
        return f"{m.group(1)} states", "~~"
    names = [STATE_NAMES.get(x.strip(), x.strip()) for x in value.split(";")]
    if len(names) == 1:
        return names[0], names[0]
    text = ", ".join(names[:-1]) + " and " + names[-1]
    return text, "~" + text


def check_house_fees():
    errs = []
    for n, r in enumerate(HOUSE_FEES, 2):
        where = f"data/house-fees.csv line {n}"
        if r["basis"] not in FEE_BASIS:
            errs.append(f"{where}: basis must be one of {', '.join(FEE_BASIS)}")
        if not r["source_url"].startswith("http"):
            errs.append(f"{where}: needs a source URL")
        for code in re.findall(r"\b[A-Z]{2}\b", r["state"]):
            if code not in STATE_NAMES:
                errs.append(f"{where}: unknown state {code}")
    if errs:
        raise SystemExit("House fee problems:\n" + "\n".join(errs))


check_house_fees()


def dancer_pay_page():
    rows = []
    for r in sorted(HOUSE_FEES, key=lambda r: (fee_states(r["state"])[1], r["year"] or "0000", r["club_name"])):
        st_name = fee_states(r["state"])[0]
        city = r["city"].strip()
        if r["club_name"]:
            place = f'{e(r["club_name"])}' + (f'<span class="sub">{e(city)}</span>' if city else "")
        elif city.lower() == "statewide":
            place = "Statewide"
        else:
            place = e(city) if city else "Club not named"
        alleged = "<b>Alleged:</b> " if r["basis"] == "alleged" else ""
        cond = f'<span class="sub">{e(r["conditions"])}</span>' if r["conditions"] else ""
        outcome = f'<span class="sub">{e(r["outcome"])}</span>' if r["outcome"] else ""
        rows.append(
            f'<tr><th scope="row">{e(st_name)}</th><td>{place}</td><td>{e(r["year"] or "Not given")}</td>'
            f'<td>{e(r["item"])}</td><td>{alleged}{e(r["amount"])}{cond}</td>'
            f'<td>{e(FEE_BASIS[r["basis"]])}{outcome}</td><td class="srcs">{source_links(r["source_url"])}</td></tr>')
    wa_law = "https://lawfilesext.leg.wa.gov/Biennium/2023-24/Pdf/Bill%20Reports/Senate/6105-S.E%20SBR%20FBR%2024.pdf"
    wa_rule = "https://lni.wa.gov/rulemaking-activity/AO24-09/2409CR103.pdf"
    wa_before = "https://www.cascadepbs.org/politics/2023/02/seattle-exotic-dancers-organize-improve-predatory-conditions"
    asks = [
        "The club, picked from a list",
        "Roughly when: this month, last month, 2 to 6 months ago, or 7 to 12 months ago",
        "The shift: weekday or weekend, day or night",
        "What time you arrived, and whether the house fee goes up for arriving later",
        "The house fee for that shift",
        "What you tipped out to staff that shift, in total",
        "The price of one private dance, and what you kept from it",
        "Whether the club fined you, and whether it pays you as an employee or a contractor",
    ]
    ask_html = "".join(f'<li class="todo"><span class="box" aria-hidden="true"></span>{e(a)}</li>' for a in asks)
    if DANCER_FORM_URL:
        host = re.sub(r"^www\.", "", re.sub(r"^https?://([^/]+).*$", r"\1", DANCER_FORM_URL))
        form = (f'<p><a class="btnlink" href="{e(DANCER_FORM_URL)}">{icon("file")}<span>Open the anonymous report form'
                f'</span></a></p><p>The form opens on {e(host)}, a form service. It takes about two minutes.</p>')
    else:
        form = ('<div class="panel"><h3 id="soon">Reports open soon</h3><p>The anonymous form isn\'t open yet. '
                'When it is, the button to it will be right here. Nothing on this site asks for your name.</p></div>')
    shown = [(c, dancer_summary(c["id"])) for c in CLUBS]
    shown = [(c, sm) for c, sm in shown if sm]
    if shown:
        trs = "".join(
            f'<tr><th scope="row"><a href="{club_page_name(c["id"])}#dancers-say">{e(c["name"])}</a>'
            f'<span class="sub">{e(c["city"])}, {e(c["state"])}</span></th><td>{sm["count"]}</td><td>{e(sm["span"])}</td></tr>'
            for c, sm in sorted(shown, key=lambda x: (x[0]["state"], x[0]["city"], x[0]["name"])))
        enough = ('<div class="tablewrap" role="region" tabindex="0" aria-label="Clubs with enough dancer reports">'
                  '<table><thead><tr><th scope="col">Club</th><th scope="col">Reports</th><th scope="col">Months</th>'
                  f'</tr></thead><tbody>{trs}</tbody></table></div>')
    else:
        enough = "<p>No club has enough reports yet.</p>"
    body = f"""
<h1>House fees and dancer pay</h1>
<p class="lead">What clubs have charged dancers to work: house fees, required tips to staff, fines and quotas, by state. The numbers come from state law, court records and the news. A number from a lawsuit is what the dancers alleged, unless a court found it.</p>
<div class="callout">{icon("scale")}<p><b>How to read this page.</b> &ldquo;Alleged in a lawsuit&rdquo; is the dancers' claim, not a finding. A settlement isn't an admission. &ldquo;Court finding&rdquo; is what a court ruled. &ldquo;Dancers' account&rdquo; is what dancers told reporters or a dancer group. No dancers are named here.</p></div>

<section aria-labelledby="wa-h">
<h2 id="wa-h">Washington caps house fees</h2>
<p>Since January 1, 2025, Washington law limits what a club can charge a dancer to work (<a href="{wa_law}">final bill report</a>):</p>
<ul>
<li>Over any 8 hours, the fee can't be more than $150 or 30% of what the dancer collected outside private rooms, whichever is less, plus 30% of what the dancer collected in private rooms.</li>
<li>The fee can't be more than the dancer took in during that time.</li>
<li>It has to be the same for every dancer, in a written contract that explains how the club estimates a dancer's take, and fixed for at least three months.</li>
<li>No late fees, no fee for missing a shift, and no unpaid fees carried forward as &ldquo;back rent.&rdquo;</li>
<li>A room fee charged when no dance happens doesn't count as money the dancer collected, and clubs must post signs saying dancers can't be made to hand over tips (<a href="{wa_rule}">state rules, December 2024</a>).</li>
</ul>
<p>Before the law, a state advisory committee put Washington house fees at $65 to $165 a shift, with the average above $100 (<a href="{wa_before}">Cascade PBS</a>). Other states' rules are in our <a href="laws.html">laws guide</a>, and <a href="dancers.html#how-to-file-a-wage-complaint">here's how to file a wage complaint</a>.</p>
</section>

<section aria-labelledby="fees-h">
<h2 id="fees-h">What clubs have charged, by state</h2>
<div class="tablewrap" role="region" tabindex="0" aria-labelledby="fees-cap">
<table>
<caption id="fees-cap">{len(HOUSE_FEES)} fees, prices and rules from {len({fee_states(r["state"])[0] for r in HOUSE_FEES})} states and groups of states</caption>
<thead><tr><th scope="col">State</th><th scope="col">Club</th><th scope="col">Year</th><th scope="col">What</th><th scope="col">Amount</th><th scope="col">What it rests on</th><th scope="col">Source</th></tr></thead>
<tbody>{"".join(rows)}</tbody>
</table>
</div>
<p>Download this table: <a href="data/house-fees.csv" download>house-fees.csv</a>. What a club says about its own fees is on its page, under &ldquo;What the club says.&rdquo;</p>
</section>

<section aria-labelledby="dancer-reports">
<h2 id="dancer-reports">Dancer reports</h2>
<p>Dancers know what clubs really charge. Tell us, anonymously, and we'll show the numbers once enough dancers agree.</p>
<h3 id="asks-h">What the form asks</h3>
<ul class="checklist">{ask_html}</ul>
<p>That's all. Every answer is a number, a time or a choice from a list. There's no comment box, so there's nowhere for a name to go.</p>
<h3 id="never-h">What we never collect</h3>
<ul>
<li>Your name or stage name</li>
<li>Your email or phone number</li>
<li>Anyone else's name: managers, staff, customers or other dancers</li>
</ul>
<p>The form runs on Tally, a form service. Like most websites, Tally can log technical data such as your IP address. For extra privacy, use cellular data or a VPN.</p>
<h3 id="when-h">When numbers appear</h3>
<ul>
<li>A club's numbers appear only after {DANCER_REPORT_MIN} separate reports from the last {DANCER_REPORT_MONTHS} months.</li>
<li>We show a range and the middle value, never one dancer's report.</li>
<li>We read every report before it counts, and set aside ones that look like spam or a pile-on.</li>
<li>Dancer numbers never change a club's rating. Ratings come from <a href="method.html">public records</a>.</li>
<li>Abuse, harassment and trafficking aren't published from this form. If it's happening to you, <a href="dancers.html#get-help-now">use the free help lines</a>.</li>
</ul>
{form}
<h3 id="enough-h">Clubs with enough reports</h3>
{enough}
</section>
"""
    return page("dancer-pay.html", "House fees and dancer pay",
                "What strip clubs have charged dancers to work, by state, from laws, court records and the news, and how to report your club's fees anonymously.",
                body, wide=True)


def readme_section(title):
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    m = re.search(rf"^## {re.escape(title)}\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        return ""
    body = markdown.markdown(m.group(1), extensions=["sane_lists"])
    body = re.sub(r'href="([^"]+)"', lambda mm: f'href="{e(resolve("README.md", html.unescape(mm.group(1))))}"', body)
    return friendly_link_text(body)


def tiles(items, cls="tiles"):
    return f'<ul class="{cls}">' + "".join(
        f'<li><a class="tile" href="{href}"><span class="pic">{icon(ic)}</span>'
        f'<span class="tl">{e(t)}</span><span class="th">{e(sub)}</span></a></li>'
        for href, ic, t, sub in items) + "</ul>"


def role_page(out_name, r):
    parts = []
    for i, (heading, items) in enumerate(r["groups"], 1):
        hid = f"g{i}"
        parts.append(f'<section aria-labelledby="{hid}"><h2 id="{hid}">{e(heading)}</h2>{tiles(items)}</section>')
    if r["ask"]:
        qs = "".join(f'<li class="todo"><span class="box" aria-hidden="true"></span>{e(q)}</li>' for q in r["ask"])
        parts.append(f'<section aria-labelledby="ask" class="panel"><h2 id="ask">{e(r["ask_title"])}</h2>'
                     f'<ul class="checklist">{qs}</ul></section>')
    href, text = r["help"]
    parts.append(f"""<section aria-labelledby="help" class="callout">
{icon("alert")}<div><h2 id="help">Help now</h2>
<p>If someone is in danger, call <a href="tel:911">911</a>. To report trafficking, call the National Human Trafficking Hotline at <a href="tel:+18883737888">1-888-373-7888</a> or text <a href="sms:233733">233733</a>.</p>
<p><a href="{href}">{e(text)}</a></p></div>
</section>""")
    body = f'<h1>{e(r["title"])}</h1>\n<p class="lead">{e(r["lead"])}</p>\n' + "\n".join(parts)
    return page(out_name, r["title"], r["desc"], body)


def home_page():
    st = Counter(c["status"] for c in CLUBS)
    oh = sum(1 for c in CLUBS if c["state"] == "OH")
    doors = [(href, ic, t, sub) for href, (ic, t, sub) in ((h, r["door"]) for h, r in ROLES.items())]
    door_html = tiles(doors, "tiles doors")
    more_html = tiles([
        ("directory.html", "list", "Club directory", f"{len(CLUBS)} clubs with sources and public records"),
        ("trafficking.html", "shield", "Stop trafficking", "The signs, and what to do when you see them"),
        ("stay-away.html", "octagon", "Places to stay away from", "Closed or convicted over trafficking, with sources"),
        ("laws.html", "scale", "Laws by state", "Age limits, touching, fees and worker protections"),
        ("standard.html", "checkbox", "Club Safety Standard", "The checklist any club can meet"),
    ])
    body = f"""
<div class="hero">
<h1>Strip Club Etiquette</h1>
<p class="lead">One place for the facts about strip clubs, for customers, dancers, club owners and anyone looking in. Plain English, non-explicit, every claim sourced.</p>
</div>

<section aria-labelledby="start-h">
<h2 id="start-h">Start with who you are</h2>
{door_html}
</section>

<section aria-labelledby="most-h">
<h2 id="most-h">Most used</h2>
{more_html}
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

<section aria-labelledby="states-h">
<h2 id="states-h">Clubs by state</h2>
{state_links()}
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
    shutil.copy(ROOT / "data/club-info.csv", OUT / "data/club-info.csv")
    shutil.copy(ROOT / "data/house-fees.csv", OUT / "data/house-fees.csv")
    shutil.copy(ROOT / "data/dancer-reports.csv", OUT / "data/dancer-reports.csv")
    shutil.copy(ROOT / "data/stay-away.csv", OUT / "data/stay-away.csv")
    shutil.copy(ROOT / "data/stay-away-records.csv", OUT / "data/stay-away-records.csv")
    (OUT / ".nojekyll").write_text("")

    pages = ["index.html", "directory.html", "records.html", "stay-away.html", "about.html"]
    for src, (out_name, _label, _icon) in MD_PAGES.items():
        title, desc, body = render_md(src)
        write(out_name, page(out_name, title, desc, body))
        pages.append(out_name)

    for out_name, r in ROLES.items():
        write(out_name, role_page(out_name, r))
        pages.append(out_name)
    for c in CLUBS:
        write(club_page_name(c["id"]), club_page(c))
        pages.append(club_page_name(c["id"]))
    write("claim.html", claim_page())
    pages.append("claim.html")
    for st in states_in_data():
        write(state_page_name(st), state_page(st))
        pages.append(state_page_name(st))
    write("dancer-pay.html", dancer_pay_page())
    pages.append("dancer-pay.html")

    write("index.html", home_page())
    write("directory.html", directory_page())
    write("records.html", records_page())
    write("stay-away.html", stay_away_page())
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
