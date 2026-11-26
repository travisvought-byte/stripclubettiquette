#!/usr/bin/env python3
"""Check the built site in _site/ for broken links and common accessibility problems.

Run after build.py:  python3 _build/check.py
Exits with an error if anything fails, so it can gate a pull request.
"""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "_site"

# Text pairs (foreground, background) that must meet WCAG AA 4.5:1.
CONTRAST_PAIRS = {
    "light body text": ("#1c1a24", "#ffffff"),
    "light secondary text": ("#4a4658", "#ffffff"),
    "light secondary on panel": ("#4a4658", "#f5f3fb"),
    "light link": ("#4b2fb4", "#ffffff"),
    "light link on panel": ("#4b2fb4", "#f5f3fb"),
    "light heading": ("#231b4d", "#f5f3fb"),
    "dark body text": ("#ecebf3", "#14121c"),
    "dark secondary text": ("#c3c0d1", "#1f1c2b"),
    "dark link": ("#b9a8ff", "#14121c"),
    "dark link on panel": ("#b9a8ff", "#1f1c2b"),
    "dark heading": ("#d9d0ff", "#1f1c2b"),
    "help bar red": ("#ffffff", "#b3261e"),
    "help bar green": ("#ffffff", "#0b6b5c"),
    "help bar blue": ("#ffffff", "#1f4fa3"),
    "help bar title": ("#ffffff", "#18122f"),
    "quick exit": ("#18122f", "#ffffff"),
    "badge ok": ("#0f5132", "#e3f4ea"),
    "badge info": ("#1d3f87", "#e6eefc"),
    "badge muted": ("#3d3a4b", "#eeedf2"),
    "badge warn": ("#6e4300", "#fff1d6"),
    "badge bad": ("#8c1d18", "#fde4e4"),
    "dark badge ok": ("#9be3b5", "#12321f"),
    "dark badge info": ("#b4ccff", "#17284d"),
    "dark badge muted": ("#d4d1e0", "#2a2738"),
    "dark badge warn": ("#ffd58a", "#3d2a05"),
    "dark badge bad": ("#ffb4ae", "#431514"),
}


def luminance(hex_color):
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    la, lb = sorted([luminance(a), luminance(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.headings = set(), [], []
        self.labels_for, self.controls = set(), []
        self.lang = None
        self.title = ""
        self._in_title = False
        self.problems = []
        self.svg_use_ok = True
        self._svg_stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                self.problems.append(f"duplicate id {a['id']!r}")
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "title":
            self._in_title = True
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag == "img" and not a.get("alt") and a.get("alt") != "":
            self.problems.append("img without alt")
        if tag == "svg":
            self._svg_stack.append(a)
            if a.get("aria-hidden") != "true" and "role" not in a and "aria-label" not in a:
                self.problems.append("inline svg without aria-hidden or a label")
        if tag == "label" and "for" in a:
            self.labels_for.add(a["for"])
        if tag in ("input", "select", "textarea") and a.get("type") != "hidden":
            self.controls.append(a.get("id"))
        if tag == "th" and "scope" not in a:
            self.problems.append("th without scope")
        if tag == "a" and a.get("target") == "_blank":
            self.problems.append("link opens a new window without warning")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "svg" and self._svg_stack:
            self._svg_stack.pop()

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def main():
    failures = []
    for name, (fg, bg) in CONTRAST_PAIRS.items():
        ratio = contrast(fg, bg)
        if ratio < 4.5:
            failures.append(f"contrast: {name} is {ratio:.2f}:1, needs 4.5:1")

    pages = {}
    for path in sorted(SITE.rglob("*.html")):
        p = Page()
        p.feed(path.read_text(encoding="utf-8"))
        pages[path.relative_to(SITE).as_posix()] = p

    for name, p in pages.items():
        for prob in p.problems:
            failures.append(f"{name}: {prob}")
        if p.lang != "en":
            failures.append(f"{name}: missing lang")
        if not p.title.strip():
            failures.append(f"{name}: empty title")
        if p.headings.count(1) != 1:
            failures.append(f"{name}: has {p.headings.count(1)} h1 elements, needs 1")
        for prev, cur in zip(p.headings, p.headings[1:]):
            if cur > prev + 1:
                failures.append(f"{name}: heading jumps from h{prev} to h{cur}")
        for ctl in p.controls:
            if not ctl or ctl not in p.labels_for:
                failures.append(f"{name}: form control {ctl!r} has no label")
        for href in p.links:
            if re.match(r"^(https?:|mailto:|tel:|sms:)", href):
                continue
            target, _, anchor = href.partition("#")
            target = target.split("?", 1)[0]
            target_name = target or name
            if target_name.endswith(".csv"):
                if not (SITE / target_name).exists():
                    failures.append(f"{name}: broken link {href}")
                continue
            if target_name not in pages:
                failures.append(f"{name}: broken link {href}")
            elif anchor and anchor not in pages[target_name].ids:
                failures.append(f"{name}: missing anchor {href}")

    if failures:
        print("\n".join(failures))
        print(f"\n{len(failures)} problem(s) found.")
        sys.exit(1)
    print(f"Checked {len(pages)} pages and {len(CONTRAST_PAIRS)} color pairs: no problems found.")


if __name__ == "__main__":
    main()
