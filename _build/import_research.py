"""Merge research CSVs into data/clubs.csv and data/evidence.csv.

Usage:
    python3 _build/import_research.py CLUBS_CSV RECORDS_CSV [--dry-run]

CLUBS_CSV has the columns
    state,city,name,address,status,operator,alcohol,nudity,website,sources,last_researched,notes
RECORDS_CSV has the columns
    club_name,city,state,operator_entity,date,dimension,type,summary,source_url,
    source_type,primary_confirmed,case_or_docket,added,notes
Pass "-" for either file to skip it.

Safe to run again on the same or newer files: clubs already listed (same state,
same name once punctuation and words like "gentlemen's club" are set aside, and
the same city) are left alone, and records already in evidence.csv (same club,
source and summary, or same club, source, date and type, so a summary reworded
by hand in evidence.csv is not added again) are skipped. Only records checked against the primary
record (primary_confirmed = yes) are published. The rest stay out of the
repository until someone checks them.
"""
import csv
import re
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLUBS_FILE = ROOT / "data/clubs.csv"
EVIDENCE_FILE = ROOT / "data/evidence.csv"
TODAY = date.today()
NEXT_REVIEW = "2027-02-24"

STATUS = {"unverified", "reported-open", "verified", "unknown", "closed"}
ALCOHOL = {"yes", "no", "byob", "unknown"}
NUDITY = {"topless", "nude", "unknown"}
DIMENSION = {"dancer-pay", "safety", "licensing", "trafficking", "customer", "status"}
RTYPE = {"allegation", "government-action", "finding", "settlement", "conviction", "incident", "closure", "positive"}
SOURCE_TYPE = {"court", "agency", "company-filing", "news", "settlement-notice"}
STATES = set("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM "
             "NY NC ND OH OK OR PA PR RI SC SD TN TX UT VT VA VI WA WV WI WY".split())
# Records that name no single club can't be tied to a listing.
NO_CLUB = re.compile(r"^unnamed|affiliated clubs|multi-?state", re.I)
# Research names that refer to a club already listed under another name or city:
# (state, research name, research city) -> (listed name, listed city). Lowercase keys.
ALIASES = {
    ("CT", "the electric blue", "tolland"): ("Electric Blue Cafe", "Tolland"),
    ("FL", "tootsie's cabaret miami", "miami gardens"): ("Tootsie's Cabaret", "Miami Gardens"),
    ("GA", "the follies", "chamblee"): ("Follies", "Atlanta"),
    ("NV", "sapphire gentlemen's club", "las vegas"): ("Sapphire Las Vegas", "Las Vegas"),
    ("OR", "sassy's", "portland"): ("Sassy's Bar and Grill", "Portland"),
    ("PA", "penthouse club", "philadelphia"): ("The Penthouse Club Philadelphia", "Philadelphia"),
}
GENERIC = re.compile(r"\b(gentle?m[ae]n'?s'? club|gentlem[ae]ns club|men'?s club|show ?club|cabaret|"
                     r"night ?club|club|lounge|go-?go bar|topless|bar)\b")


def norm_name(name):
    n = re.sub(r"\([^)]*\)", " ", name.lower())
    n = n.replace("&", " and ").replace("’", "'")
    n = re.sub(r"^the\s+", "", n.strip())
    n = GENERIC.sub(" ", n)
    n = re.sub(r"[^a-z0-9]", "", n)
    return n or re.sub(r"[^a-z0-9]", "", name.lower())


def norm_city(city):
    c = re.sub(r"\([^)]*\)", " ", city.lower())
    c = re.sub(r"\b(area|county|metro)\b", " ", c)
    return re.sub(r"[^a-z]", "", c)


def vague_city(city):
    return not city.strip() or bool(re.search(r"\b(area|county|metro)\b|\(", city, re.I))


def clean_name(name):
    """Drop a trailing research note such as "(Hallandale Beach)" from a club name."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", name).strip() or name.strip()


def clean_city(city):
    """"North Hollywood (Los Angeles)" -> "North Hollywood"."""
    return re.sub(r"\s*\([^)]*\)", "", city).strip()


def clean_operator(op):
    """Keep the legal entity; drop research notes such as "(per site copyright)"."""
    return re.sub(r"\s*\((?:per|holding)[^)]*\)", "", op).strip()


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


class Clubs:
    def __init__(self, rows):
        self.rows = rows
        self.by_state = {}
        for r in rows:
            self.by_state.setdefault(r["state"], []).append(r)

    def find(self, state, name, city):
        alias = ALIASES.get((state, name.strip().lower(), city.strip().lower()))
        if alias:
            name, city = alias
        key = norm_name(name)
        cands = [r for r in self.by_state.get(state, []) if norm_name(r["name"]) == key]
        for r in cands:
            if norm_city(r["city"]) == norm_city(city) and norm_city(city):
                return r
        if len(cands) == 1 and (vague_city(city) or vague_city(cands[0]["city"])):
            return cands[0]
        return None

    def next_id(self, state):
        nums = [int(r["id"].split("-")[1]) for r in self.by_state.get(state, []) if re.fullmatch(r"[A-Z]{2}-\d{4}", r["id"])]
        return f"{state}-{(max(nums) if nums else 0) + 1:04d}"

    def add(self, row):
        row["id"] = self.next_id(row["state"])
        self.rows.append(row)
        self.by_state.setdefault(row["state"], []).append(row)
        return row


def check(cond, errs, where, msg):
    if not cond:
        errs.append(f"{where}: {msg}")


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    clubs_in, records_in = argv[1], argv[2]
    dry = "--dry-run" in argv
    clubs_fields = list(read(CLUBS_FILE)[0].keys())
    ev_fields = list(read(EVIDENCE_FILE)[0].keys())
    clubs = Clubs(read(CLUBS_FILE))
    evidence = read(EVIDENCE_FILE)
    errs, added_clubs, added_recs, skipped = [], 0, 0, []

    if clubs_in != "-":
        for n, r in enumerate(read(clubs_in), 2):
            where = f"{clubs_in} line {n}"
            check(r["state"] in STATES, errs, where, f"unknown state {r['state']!r}")
            check(r["status"] in STATUS, errs, where, f"status {r['status']!r}")
            check(r["alcohol"] in ALCOHOL, errs, where, f"alcohol {r['alcohol']!r}")
            check(r["nudity"] in NUDITY, errs, where, f"nudity {r['nudity']!r}")
            check(r["name"].strip() and r["city"].strip(), errs, where, "needs a name and a city")
            check(r["sources"].strip(), errs, where, "needs a source")
            if clubs.find(r["state"], r["name"], r["city"]):
                continue
            clubs.add({
                "state": r["state"], "city": clean_city(r["city"]), "name": clean_name(r["name"]),
                "address": r["address"].strip(), "status": r["status"], "operator": clean_operator(r["operator"]),
                "alcohol": r["alcohol"], "nudity": r["nudity"], "website": r["website"].strip(),
                "sources": r["sources"].strip(), "last_researched": r["last_researched"] or TODAY.isoformat(),
                "next_review": NEXT_REVIEW, "overall_flag": "not-reviewed", "notes": r["notes"].strip(),
            })
            added_clubs += 1

    if records_in != "-":
        seen = {(x["club_id"], x["source_url"], x["summary"]) for x in evidence}
        seen |= {(x["club_id"], x["source_url"], x["date"], x["type"]) for x in evidence}
        nums = [int(x["evidence_id"].split("-")[1]) for x in evidence]
        next_e = max(nums) + 1 if nums else 1
        for n, r in enumerate(read(records_in), 2):
            where = f"{records_in} line {n}"
            check(r["dimension"] in DIMENSION, errs, where, f"dimension {r['dimension']!r}")
            check(r["type"] in RTYPE, errs, where, f"type {r['type']!r}")
            check(r["source_type"] in SOURCE_TYPE, errs, where, f"source_type {r['source_type']!r}")
            check(r["primary_confirmed"] in ("yes", "no"), errs, where, "primary_confirmed must be yes or no")
            check(r["source_url"].startswith("http"), errs, where, "needs a source URL")
            check(r["state"] in STATES, errs, where, f"unknown state {r['state']!r}")
            if r["primary_confirmed"] != "yes":
                continue
            if NO_CLUB.search(r["club_name"]):
                skipped.append(f"{where}: names no single club ({r['club_name']})")
                continue
            club = clubs.find(r["state"], r["club_name"], r["city"])
            if not club:
                closed = r["type"] == "closure"
                club = clubs.add({
                    "state": r["state"], "city": clean_city(r["city"]) or "City to confirm",
                    "name": clean_name(r["club_name"]), "address": "",
                    "status": "closed" if closed else "unverified",
                    "operator": clean_operator(r["operator_entity"]), "alcohol": "unknown", "nudity": "unknown",
                    "website": "", "sources": r["source_url"], "last_researched": TODAY.isoformat(),
                    "next_review": NEXT_REVIEW, "overall_flag": "not-reviewed",
                    "notes": ("Closed, per the public record." if closed else
                              "Named in public records; not yet confirmed operating."),
                })
                added_clubs += 1
            key = (club["id"], r["source_url"], r["summary"].strip())
            key2 = (club["id"], r["source_url"].strip(), r["date"], r["type"])
            if key in seen or key2 in seen:
                continue
            seen.add(key)
            seen.add(key2)
            evidence.append({
                "evidence_id": f"E-{next_e:04d}", "club_id": club["id"], "date": r["date"],
                "dimension": r["dimension"], "type": r["type"], "summary": r["summary"].strip(),
                "source_url": r["source_url"].strip(), "source_type": r["source_type"],
                "primary_confirmed": "yes", "added": r["added"] or TODAY.isoformat(),
            })
            next_e += 1
            added_recs += 1

    if errs:
        raise SystemExit("Import stopped, nothing written:\n" + "\n".join(errs))

    # The one rating set before a full review (METHODOLOGY section 4): a trafficking-related
    # conviction tied to the club in the last 5 years makes the club "serious".
    cutoff = (TODAY - timedelta(days=5 * 365)).isoformat()
    for x in evidence:
        if x["dimension"] == "trafficking" and x["type"] == "conviction" and (x["date"] or "") >= cutoff:
            for c in clubs.rows:
                if c["id"] == x["club_id"]:
                    c["overall_flag"] = "serious"

    clubs.rows.sort(key=lambda c: (c["state"], int(c["id"].split("-")[1])))
    if not dry:
        write(CLUBS_FILE, clubs.rows, clubs_fields)
        write(EVIDENCE_FILE, evidence, ev_fields)
    print(f"{'Would add' if dry else 'Added'} {added_clubs} clubs and {added_recs} records. "
          f"Now {len(clubs.rows)} clubs and {len(evidence)} records.")
    for s in skipped:
        print("Skipped", s)


if __name__ == "__main__":
    main(sys.argv)
