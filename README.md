# Strip Club Etiquette

A national directory of U.S. strip clubs, a public-records method for judging how they operate, and plain-English guides on etiquette, the business model, and stopping human trafficking.

> **In danger right now? Call 911.**
>
> **National Human Trafficking Hotline:** call 1-888-373-7888, text 233733, or chat at [humantraffickinghotline.org/chat](https://humantraffickinghotline.org/chat). Free, confidential, 24/7, in 200+ languages.
>
> **Ohio Human Trafficking Hotline:** 844-END-OHHT (844-363-6448), or text ENDOHHT to 847411. Tips go to law enforcement.

## Who this is for

- **Customers:** how to act, what to expect, how to avoid getting ripped off, and how to spot trouble.
- **Dancers:** your rights, what fair treatment looks like, and where to get help. See [guides/for-dancers.md](guides/for-dancers.md).
- **Club owners and managers:** how the money really works, where clubs lose money and licenses, and what the best-run clubs do differently.
- **Advocates and officials:** trafficking indicators, model policies, and a sourced record of how clubs operate.

## What's here

| Path | What it is |
|---|---|
| [guides/etiquette.md](guides/etiquette.md) | Customer etiquette: before you go, tipping, private dances, VIP rooms, what not to do |
| [guides/for-dancers.md](guides/for-dancers.md) | For dancers: contractor or employee, tips, fees, filing a wage claim, harassment, organizing, getting out |
| [guides/how-strip-clubs-work.md](guides/how-strip-clubs-work.md) | The business model: who earns what, fees, the contractor vs. employee fight, regulation |
| [guides/for-club-operators.md](guides/for-club-operators.md) | Playbook for owners and managers: cut legal risk, protect dancers, earn a better rating |
| [guides/human-trafficking.md](guides/human-trafficking.md) | Recognizing and reporting trafficking, for customers, staff, dancers and advocates |
| [guides/laws-by-state.md](guides/laws-by-state.md) | Key laws by state: age limits, touching, alcohol, worker protections |
| [standards/club-safety-standard.md](standards/club-safety-standard.md) | The checklist clubs can meet: dancer safety, fair pay, anti-trafficking, honest pricing |
| [METHODOLOGY.md](METHODOLOGY.md) | How clubs get listed, verified and rated, and how corrections work |
| [data/clubs.csv](data/clubs.csv) | The directory |
| [data/evidence.csv](data/evidence.csv) | Public records (lawsuits, permit actions, convictions) tied to specific clubs |
| [data/README.md](data/README.md) | Field definitions for both data files |
| [research/national.md](research/national.md) | National scope, counts and build plan |
| [research/ohio.md](research/ohio.md) | Ohio coverage, sources, key cases and open leads |
| [_build/](_build/) | The website build: turns the guides and data into a static, accessible site |

## Where things stand (November 22, 2026)

- The U.S. has roughly 3,900 strip club businesses (IBISWorld estimated 3,889 in 2025), so this is a state-by-state build.
- **Ohio:** first pass done. 34 clubs listed, most still unverified, plus a list of leads to run down.
- **National:** 59 clubs run by RCI Hospitality, the largest public operator, from its FY2025 annual report, plus one closed New York club whose owner was convicted of sex trafficking conspiracy. 94 clubs total.
- **Ratings:** no club has had a full review yet, so all but one show "not reviewed." The evidence log holds 32 records (lawsuits, settlements, permit actions, convictions, closures) for 20 clubs so far.

## Ground rules

1. Every listing and every claim about a club links to a source.
2. Allegations are labeled as allegations. A settlement is not an admission. Charged is not convicted.
3. No personal information about dancers, staff or customers. No stage names, no photos of people.
4. Clubs can correct their listing or respond to any record. See [METHODOLOGY.md](METHODOLOGY.md#corrections-and-responses).
5. Ratings are never for sale.
6. Most dancers are adults working by choice, and dancing is not trafficking. The goal is safer, fairer clubs, and real trafficking that's easier to spot and stop.

## Website

The guides and data are published as a static website. The Markdown and CSV files are the source; the site is generated from them.

- Build: `pip install -r _build/requirements.txt`, then `python3 _build/build.py`. The site lands in `_site/`.
- Check: `python3 _build/check.py` fails on broken links, missing anchors, missing labels, heading jumps or low color contrast. GitHub Actions runs the build and the check on every pull request and every push to `main`.
- Accessibility: built to WCAG 2.1 AA. Every page has a skip link, a help bar with the hotline (call and text) and a quick exit button, labeled landmarks, scrollable tables with headers, icons paired with words, light and dark mode, and works without JavaScript.
- Settings at the top of `_build/build.py`: `SITE_URL` (turns on canonical links and the sitemap), `GOATCOUNTER` (visit counter code), `CONTACT_EMAIL`.
- Publishing is off. To go live: make the repository public (GitHub Pages on a private repository needs a paid plan), set Pages to deploy from GitHub Actions, and set the repository variable `PAGES_ENABLED` to `true`.
- Not published on the site: the Ohio "Open leads" list, which holds unconfirmed addresses.

## Corrections and contributions

Open an issue in this repository with the club, the correction, and a source.

Contact email: to be added.
