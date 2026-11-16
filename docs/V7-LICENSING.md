# V7 data licensing record

## CollegeFootballData (CFBD): historical betting lines

**Status: authorized in writing, for the scope below.**

| Item | Record |
| --- | --- |
| Source | Direct written response from a CollegeFootballData.com administrator to the project owner |
| Recorded | 2026-11-16, the date the owner relayed it to the project. The email's own date and full text are kept with the private evidence. |
| Evidence location | Private repository `cfb-analytics-private-data`, path `licensing/cfbd-betting-lines-authorization/`. The original email is stored there unmodified, with its SHA-256 recorded alongside. It is not stored here and not published. |

Personal email metadata (addresses, headers, signatures) is deliberately not
reproduced in this public repository.

### Authorized

1. One provider's **closing spread** and **closing total** per FBS game, from
   2016 onward.
2. The provider's name shown alongside each line.
3. Browser-accessible JSON files that support team and game pages.
4. Derived team-level ATS and over/under statistics.

### Restriction

Historical lines must stay integrated into team and game pages. They must
**not** be published or offered as a standalone dataset, a bulk download or a
substitute data feed.

### How the implementation enforces this

- **Per-team files:** `web/public/v7-team-lines/<team>.json` contains one file
  per current FBS program. Each game carries exactly one closing spread and one
  closing total, each with the selected provider named and a status.
  - There is no combined all-games file, no index of files and no download
    link.
  - The files exist to back team and game pages only.
- **Never published:**
  - other providers' values, opening lines and moneylines;
  - provider-disagreement magnitudes;
  - raw API responses and private snapshots.
- **Guards:** `assert_team_lines_safe` (per-game files) and `assert_public_safe`
  (team statistics) run on every build. Tests reject:
  - unauthorized fields;
  - a line without a named provider, or with more than one;
  - duplicate games;
  - extra file-level keys such as download links.
- **Private data:** raw multi-provider responses stay in the private snapshot
  repository (or the runner's temporary storage), never in this repository, its
  artifacts, caches or logs.
- **Attribution:** "Data provided by CollegeFootballData.com" and the
  permission note travel with every public file.

### Still governed by the CFBD Terms

- Keep the API key server-side.
- No resale or substitute data service.
- Attribution recommended.

## Kalshi

**Blocked.** Developer Agreement v1.1 §3/§3.1 and the Data Terms require prior
written authorization for display, caching, aggregation or redistribution. A
request was sent; no authorization has been received. No Kalshi data is
retrieved, stored or published.
