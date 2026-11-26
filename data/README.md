# Data files

Three CSV files: UTF-8, comma-separated, with double quotes around any field that contains a comma.

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
| `security_private_rooms`, `trafficking_training`, `hotline_posted` | `yes`, `no`, or blank |

A hiring notice (`hiring` or `apply_url`) is only allowed when `worker_status`, `house_fee` and `tip_out` are all filled in. The build stops if a row breaks a rule.
