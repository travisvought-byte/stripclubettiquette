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
| [guides/whats-working.md](guides/whats-working.md) | What's working: fee rules, safety steps and business models with a record, every point sourced |
| [standards/club-safety-standard.md](standards/club-safety-standard.md) | The checklist clubs can meet: dancer safety, fair pay, anti-trafficking, honest pricing |
| [METHODOLOGY.md](METHODOLOGY.md) | How clubs get listed, verified and rated, and how corrections work |
| [data/clubs.csv](data/clubs.csv) | The directory |
| [data/evidence.csv](data/evidence.csv) | Public records (lawsuits, permit actions, convictions) tied to specific clubs |
| [data/club-info.csv](data/club-info.csv) | Hours, prices, dancer terms, booking line and audition hours that clubs give us themselves, shown as "What the club says" |
| [data/house-fees.csv](data/house-fees.csv) | What clubs have charged dancers, by state, from laws, court records and the news |
| [data/dancer-reports.csv](data/dancer-reports.csv) | Anonymous dancer pay reports: numbers only, no names, shown once a club has 3 |
| [data/README.md](data/README.md) | Field definitions for the data files, and how to import new research |
| [research/national.md](research/national.md) | National scope, counts and build plan |
| [research/ohio.md](research/ohio.md) | Ohio coverage, sources, key cases and open leads |
| [_build/](_build/) | The website build: turns the guides and data into a static, accessible site. `import_research.py` merges new research into the data files. |

## Where things stand (November 26, 2026)

- The U.S. has roughly 3,900 strip club businesses (IBISWorld estimated 3,889 in 2025), so this is a state-by-state build.
- **Directory:** 494 clubs in 45 states and territories, from public sources. Most are still "not yet confirmed" open. Ohio has 38.
- **Records:** 92 public records (convictions, findings, settlements, lawsuits, permit actions, closures) tied to 75 clubs.
- **Ratings:** no club has had a full review yet. Three clubs are rated "serious" because of trafficking-related convictions tied to them, the one rating set before a review. The rest show "not reviewed."
- **Dancer reports:** the anonymous form isn't open yet. No club has reports.

## Ground rules

1. Every listing and every claim about a club links to a source.
2. Allegations are labeled as allegations. A settlement is not an admission. Charged is not convicted.
3. No personal information about dancers, staff or customers. No stage names, no photos of people.
4. Clubs can correct their listing or respond to any record. See [METHODOLOGY.md](METHODOLOGY.md#corrections-and-responses).
5. Ratings are never for sale.
6. Most dancers are adults working by choice, and dancing is not trafficking. The goal is safer, fairer clubs, and real trafficking that's easier to spot and stop.

## Website

The guides and data are published as a static website. The Markdown and CSV files are the source; the site is generated from them.

- Start pages: the home page opens with four doors, one for each kind of visitor: visiting a club (`visit.html`), dancing or working in one (`work.html`), running one (`clubs.html`), and looking into the industry (`learn.html`). Each one groups the guide sections that role needs, a list of questions to ask a club, and the help lines. They're defined in `ROLES` in `_build/build.py`.
- Build: `pip install -r _build/requirements.txt`, then `python3 _build/build.py`. The site lands in `_site/`.
- Check: `python3 _build/check.py` fails on broken links, missing anchors, missing labels, heading jumps or low color contrast. GitHub Actions runs the build and the check on every pull request and every push to `main`.
- Accessibility: built to WCAG 2.1 AA. Every page has a skip link, a help bar with the hotline (call and text) and a quick exit button, labeled landmarks, scrollable tables with headers, icons paired with words, light and dark mode, and works without JavaScript.
- Club pages: every club gets its own page (`club-oh-0001.html` and so on) with our record, what dancers report (once there are 3 reports), and, when the club has given them, its own hours, prices and dancer terms from `data/club-info.csv`. Booking line and audition hours show only from a claimed listing. Clubs claim their listing on `claim.html`.
- State pages: one per state with clubs (`state-oh.html` and so on), with each club's status and record count and a link to that state's section of the laws guide. Linked from the home page and the directory.
- Records page: `records.html` lists records most serious first (convictions, findings, government and license actions, settlements, then lawsuits and charges), with a state filter. Every record shows without JavaScript.
- Dancer pay page: `dancer-pay.html`, under Dancers, shows `data/house-fees.csv` by state and explains anonymous dancer reports.
- What's working: `whats-working.html`, under Clubs, from `guides/whats-working.md`.
- Settings at the top of `_build/build.py`: `SITE_URL` (turns on canonical links and the sitemap), `GOATCOUNTER` (visit counter code), `CONTACT_EMAIL`, `CLAIM_FORM_URL` or `CLAIM_EMAIL` (where club claims go; claims go by email to the address in `CLAIM_EMAIL`, and with neither set the claim page lists what we'll ask for and says claims open soon), and `DANCER_FORM_URL` (the anonymous dancer report form; empty shows "Reports open soon"). `DANCER_REPORT_MIN` (3) and `DANCER_REPORT_MONTHS` (12) set when dancer numbers show.
- New research: `python3 _build/import_research.py CLUBS_CSV RECORDS_CSV` merges it into `data/clubs.csv` and `data/evidence.csv`. See the [data README](data/README.md).
- Domain: `stripclubguide.org`, registered at Wix. The build writes canonical links, the sitemap and a `CNAME` file for it.
- Publishing: every push to `main` builds, checks and publishes the site to GitHub Pages. Pages deploys from GitHub Actions, with `stripclubguide.org` set as the custom domain in Settings, Pages (with Actions deploys, GitHub reads the domain from that setting, not from the `CNAME` file).
- DNS at Wix: four A records for the bare domain (`185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`) and a CNAME record for `www` pointing to `travisvought-byte.github.io`. HTTPS is enforced in Settings, Pages.
- Not published on the site: the Ohio "Open leads" list, which holds unconfirmed addresses.

## Corrections and contributions

Open an issue in this repository with the club, the correction, and a source.

Contact email: to be added.
