# Methodology

How clubs get into the directory, how we confirm they exist and are open, and how we judge their reputations without guessing or defaming anyone.

## 1. What counts as a strip club

**Included:** businesses whose main draw is live nude or semi-nude dance performance on a regular schedule. That covers gentlemen's clubs, adult cabarets, topless bars, nude juice bars (no alcohol), and male revues with regular hours.

**Excluded:** adult bookstores and video stores, massage businesses, escort services, online platforms, one-off private parties, and drag or burlesque shows.

## 2. Listing status

| Status | Meaning |
|---|---|
| `unverified` | A source names the club and its city, but we haven't confirmed it's operating. This is the default for new entries. |
| `reported-open` | A news, government or company source dated within the last 24 months indicates it's operating. |
| `verified` | Confirmed operating during the current review cycle through at least one of: an active liquor permit or local adult-entertainment license, a club website or social account with recent activity, direct contact with the club, or an in-person visit. |
| `unknown` | There's a specific reason to doubt it's still operating (a revoked or denied permit, or no record in 5+ years) but no closure report. |
| `closed` | A source reports it closed. Date and source go in the notes and the evidence log. |

Names we've seen without a confirmed city stay in the state research file as leads (for Ohio, see [research/ohio.md](research/ohio.md#open-leads)) until they're located.

## 3. Sources, strongest first

1. **Government records:** court dockets and opinions, liquor control orders and permit databases, city or county adult-entertainment licenses, prosecutor and attorney general releases, SEC filings.
2. **The club's own statements:** website, published policies, filings.
3. **Established news outlets.**
4. **Settlement notices and summaries.** Confirm against the court docket when possible.
5. **Directories and review sites:** leads only. Never the sole basis for a listing status or a record. We don't copy their data, ratings or review text.

## 4. Reputation review

A review searches every source type above for the club's name, address and legal entity, and records what it finds in [data/evidence.csv](data/evidence.csv). Each club is judged on five dimensions:

| Dimension | What goes in it |
|---|---|
| **Dancer pay and treatment** | Wage-and-hour lawsuits, settlements and judgments; fee and fine practices; worker classification; published fee schedules |
| **Safety and security** | Violence on the premises, nuisance actions, security practices, panic buttons |
| **Legal and licensing** | Liquor violations, permit objections, revocations and denials, criminal charges against the business |
| **Trafficking and exploitation** | Trafficking, prostitution or child-exploitation charges or convictions tied to the club; anti-trafficking programs |
| **Customer fairness** | Billing and credit card disputes or fraud findings; posted pricing |

Each dimension gets one flag:

| Flag | Rule |
|---|---|
| `not-reviewed` | No full review yet. This is the default. |
| `none-found` | Reviewed, and no qualifying record in the last 5 years. It means nothing turned up, not that the club is safe. |
| `concern` | In the last 5 years: at least one finding or settlement, or two or more open allegations. |
| `serious` | In the last 5 years: a criminal conviction of the business, or of its owner or manager, tied to the club; a trafficking charge or finding; a permit revoked for illegal activity; or repeated findings of violence or nuisance. |

The club's overall flag is the worst of its five. Records older than 5 years stay visible as history but don't set a flag.

**One exception to "review first":** a criminal conviction for trafficking-related crimes connected to the club sets the trafficking dimension to `serious` immediately.

**Positive records count.** A published fee schedule, completed staff training, or meeting the [Club Safety Standard](standards/club-safety-standard.md) gets recorded and shown.

**Ownership changes.** When a club changes hands, earlier records stay in its history but don't set flags for the new owner. We record the change and its source.

## 5. Wording rules

- Say what the record says, and attribute it: "named as a defendant in," "charged with," "convicted of," "settled for," "liquor permit revoked by."
- A lawsuit is an allegation. A settlement is not an admission of liability unless the record says so. Charged is not convicted.
- No guessing at motives, no loaded adjectives, no conclusions the record doesn't support.
- Quote sparingly and link to the source.

## 6. People

- No personal information about dancers, staff or customers: no names, stage names, photos, social accounts or locations.
- The directory doesn't name individuals. Records refer to roles ("the club's owner") and link to the public source.

## 7. Review cycle

- Ohio clubs: every 90 days.
- Clubs in other states: every 180 days.
- Closed clubs: once a year, to catch reopenings.

## 8. Club-supplied details

Clubs can add their own hours, prices and dancer terms to their listing, free.

- **Who counts as the club:** we confirm the sender by calling the club's publicly listed number, or by matching them to the liquor permit holder or the business filing. We record how.
- **How it's shown:** under "What the club says," in the club's words, with the date. Details copied from a club's own website are labeled that way until the club claims the listing.
- **Ratings:** club-supplied details never change a rating. Ratings come from public records and published policies only (section 4).
- **Hiring notices:** shown only when the club also publishes how dancers are classified, its house fee and its tip-out. Fake job offers are a known way traffickers recruit, so a hiring notice without terms isn't published.
- **What we won't publish:** names, stage names, photos or contact details for dancers or staff; prices for anything beyond the posted menu (cover, drinks, dances, VIP time); anything explicit or suggesting anything beyond legal entertainment.
- **Booking line and audition hours:** how dancers get on the schedule, shown only from a club we've confirmed (a claimed listing) that also publishes its dancer terms. The booking line is the club's own public number, never a personal phone, and audition details name a role to ask for, never a person. We never take these from dancer reports or copy them from other sites.
- **Freshness:** details older than 180 days are marked as possibly out of date. We remove details we find to be false.

## 9. Dancer reports

Dancers can report what a club charges them, anonymously. These rules keep reports safe for the dancer and fair to the club.

- **Anonymous:** the form asks for no name, stage name, email or phone number, and we don't build dancer accounts. It runs on Tally, a form service, which like most websites can log technical data such as IP addresses. The form says so, and suggests cellular data or a VPN for extra privacy.
- **Numbers only:** the club (picked from a list), roughly when the shift was, the shift (weekday or weekend, day or night), arrival time, the house fee and whether it goes up for arriving later, total tips to staff, the price of one private dance and what the dancer kept, whether the club charged fines, and whether the club pays dancers as employees or contractors. Every answer is a number, a time or a choice from a list. There's no free-text box, so there's nowhere to put a name.
- **No names, ever:** not the dancer's, and not a manager's, staff member's, customer's or another dancer's. A report that somehow carries one is dropped.
- **Three-report minimum:** a club's numbers appear only after 3 separate reports from the last 12 months. We show the range and the middle value, never a single report, and a field shows only when at least 3 reports answered it.
- **Reviewed first:** we read every report before it goes into [data/dancer-reports.csv](data/dancer-reports.csv), and set aside spam, outliers we can't explain, and bursts that look like a pile-on.
- **Kept apart from ratings:** dancer numbers appear under "What dancers report," never change a club's rating, and never stand in for a public record. Reports of abuse, harassment or trafficking aren't published from the form. They're leads to research, and the person reporting is pointed to the help lines.

## 10. The stay-away list

The [stay-away list](data/stay-away.csv) names strip clubs, hostess bars and cantinas tied to trafficking, forced labor, prostitution run or allowed by the business, or a minor exploited there. Each place is listed only on a primary record: a court record, a conviction or guilty plea, a closure or nuisance order, a license action, or a government release. News stories, reviews, social media and anonymous tips never list a place on their own; they are leads until a primary record turns up.

- **Stay away** needs at least one conviction or guilty plea tied to the place, a court closure or nuisance order, or a license revoked or given up, on those grounds.
- **Use caution** is for a charge, a license suspension or a temporary order on the same grounds, or a conviction on other counts where the record describes sex for money at the place. Charged is not convicted, and a charge may end with no finding.
- **Reopened or kept operating** needs a record that shows the same address. A similar name somewhere else isn't enough.
- Every record carries its date, its type and a link to its source. Convictions and charges are labeled apart. Agreed orders say there was no admission when the order says so.
- Records older than 5 years are marked as history. A place listed for an old case may be under new owners; each entry says what the record shows about that.
- Places and companies only. Never dancers, other workers or customers, and no individual owners by name.
- A listed place or its new owner can [respond or send a correction](#corrections-and-responses), and we'll add the response or a newer record.

## Corrections and responses

Any club, dancer or member of the public can request a correction. Send the club, what's wrong, and a source. A club can also submit a short written response to any record, and we'll link it next to that record.

Ratings are never for sale. Sponsorship or advertising, if the project ever takes any, will never change a listing or a flag.
