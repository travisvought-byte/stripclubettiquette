# Data files

Two CSV files: UTF-8, comma-separated, with double quotes around any field that contains a comma.

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
