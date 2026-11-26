# Data files

Five CSV files: UTF-8, comma-separated, with double quotes around any field that contains a comma.

To add new research, run `python3 _build/import_research.py CLUBS_CSV RECORDS_CSV` (pass `-` to skip either file, and add `--dry-run` to see the counts first). It merges new clubs into `clubs.csv` and records into `evidence.csv`, skips anything already there, publishes only records checked against the primary record, and stops without writing anything if a row has a value outside the lists below. Running it again on the same files adds nothing.

## clubs.csv

One row per club.

| Field | Meaning |
|---|---|
| `id` | State code plus a number, such as `OH-0001`. Never reused. |
| `state` | Two-letter postal code |
| `city` | City as given by the source |
| `name` | Name the club operates under |
| `address` | Street address, only when a source gives it |
| `status` | `unverified`, `reported-open`, `verified`, `unknown`, `closed` (see [METHODOLOGY.md](../METHODOLOGY.md#2-listing-status)) |
| `operator` | Legal entity or company, only when a public record names it. Never an individual. |
| `alcohol` | `yes`, `no`, `byob`, or `unknown` |
| `nudity` | `topless`, `nude`, or `unknown` |
| `website` | Official site, once confirmed |
| `sources` | Source URLs, separated by ` \| ` |
| `last_researched` | Date of the last research pass (YYYY-MM-DD) |
| `next_review` | When the next pass is due |
| `overall_flag` | `not-reviewed`, `none-found`, `concern`, `serious` |
| `notes` | Short plain-English notes |

## evidence.csv

One row per record per club. A lawsuit that names five clubs gets five rows.

| Field | Meaning |
|---|---|
| `evidence_id` | `E-0001` and up. Never reused. |
| `club_id` | Matches `id` in `clubs.csv` |
| `date` | Date of the event (YYYY-MM-DD, YYYY-MM or YYYY). Blank if the source doesn't give one. |
| `dimension` | `dancer-pay`, `safety`, `licensing`, `trafficking`, `customer`, or `status` |
| `type` | See below |
| `summary` | One or two neutral sentences, attributed to the source |
| `source_url` | Link |
| `source_type` | `court`, `agency`, `company-filing`, `news`, `settlement-notice` |
| `primary_confirmed` | `yes` if checked against the primary record (docket, agency order, official release); `no` if from a secondary source only |
| `added` | Date added (YYYY-MM-DD) |

Record types:

| Type | Meaning |
|---|---|
| `allegation` | A lawsuit filed, charges filed, or claims reported in the news |
| `government-action` | An official objection, citation, raid or investigation that isn't a final ruling |
| `finding` | A court judgment or agency ruling (fines, revocations, denials) |
| `settlement` | A case resolved with payment. Not an admission unless stated. |
| `conviction` | A criminal conviction or sentence |
| `incident` | A violent incident on the premises reported by police or news, with no finding against the club |
| `closure` | The club closed |
| `positive` | A published policy, completed training, or standard met |

## club-info.csv

Details a club gives us itself: one row per club, only for clubs that have sent details or post them on their own site. The website shows them under "What the club says," with the date, beside our own record. They never change a rating. See [METHODOLOGY.md](../METHODOLOGY.md#8-club-supplied-details).

| Field | Meaning |
|---|---|
| `id` | Matches `id` in `clubs.csv` |
| `claimed` | `yes` if the club sent the details and we confirmed who sent them; `no` if we copied them from the club's own website |
| `verified_by` | How we confirmed the sender speaks for the club, such as a call to the club's listed number. Required when `claimed` is `yes`. |
| `source_url` | The club's own page the details came from. Required when `claimed` is `no`. |
| `updated` | Date the details were sent or checked (YYYY-MM-DD). Older than 180 days shows as possibly out of date. |
| `hours`, `cover`, `dress_code`, `alcohol`, `payment` | Short text, in the club's words |
| `min_age` | `18`, `21`, or blank |
| `card_fee` | Surcharge on cards or club currency |
| `private_dance`, `vip` | Posted prices |
| `worker_status` | `employee`, `contractor`, `both`, or blank |
| `house_fee`, `tip_out` | What dancers pay per shift, in the club's words. "None" is an answer. |
| `hiring` | `yes`, `no`, or blank |
| `apply_url` | The club's own page for applying (https only) |
| `booking_line` | The club's own public number for getting on the schedule, as a 10-digit U.S. number. Only from a claimed listing. Never a personal phone. |
| `audition_hours` | When auditions run and the role to ask for, such as "Tuesdays 2 to 5 p.m., ask for the day manager." Only from a claimed listing. Never a name. |
| `security_private_rooms`, `trafficking_training`, `hotline_posted` | `yes`, `no`, or blank |

A hiring notice (`hiring`, `apply_url`, `booking_line` or `audition_hours`) is only allowed when `worker_status`, `house_fee` and `tip_out` are all filled in, and `booking_line` and `audition_hours` need `claimed` = `yes`. The build stops if a row breaks a rule.

## house-fees.csv

What clubs have charged dancers to work, from laws, court records and the news. Shown on the dancer pay page. No dancers are named.

| Field | Meaning |
|---|---|
| `state` | Two-letter code; several codes separated by `;`; or `multi-state (N)` for a case covering N states |
| `city`, `club_name` | Where, and the club, only when the source names it. `statewide` for a state law. |
| `year` | Year or years the figure applies to. Blank if the source doesn't say. |
| `item` | What the charge or rule is, in plain words |
| `amount` | The figure, as the source gives it |
| `conditions` | When it applied, such as per shift or weekend nights |
| `basis` | What the figure rests on: `law`, `court-finding`, `settlement`, `alleged` (from a lawsuit; shown as "Alleged"), `dancer-account`, or `news` |
| `outcome` | What happened in the case, if anything, in one short sentence |
| `source_url`, `source_type` | Link, and the kind of source |

## dancer-reports.csv

Anonymous reports from dancers about what a club charges. Numbers and dates only: no names and no free text. A club's numbers show on its page only once it has 3 reports from the last 12 months, as ranges. See [METHODOLOGY.md](../METHODOLOGY.md#9-dancer-reports).

| Field | Meaning |
|---|---|
| `report_id` | `R-0001` and up. Never reused. |
| `club_id` | Matches `id` in `clubs.csv` |
| `month` | Month worked (YYYY-MM) |
| `shift` | `weekday-day`, `weekday-night`, `weekend-day`, `weekend-night`, or blank |
| `house_fee`, `tip_out` | Whole dollars for that shift. `tip_out` is the total tipped to staff. |
| `dance_price`, `dancer_share` | Whole dollars: the price of one private dance, and what the dancer kept from it |
| `fines` | `yes`, `no`, or blank: whether the club charged fines |
| `added` | Date the report was reviewed and added (YYYY-MM-DD) |

The build stops if a row breaks a rule.
