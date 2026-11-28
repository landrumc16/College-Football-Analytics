# Rapid-source access decision — November 27, 2026

Issue #74 remains open. This is the narrow access decision for the recovered multi-source lifecycle, not a replacement source inventory. No vendor was contacted, account created, trial started, subscription purchased or live endpoint tested. Published capabilities are not measured production performance.

## ESPN: retain default-off

Disney's current terms cover ESPN. Section 2.B.x requires express written permission for scripted monitoring/extraction; section 2.A restricts consumer reuse. Buying an ESPN viewing subscription does not establish data rights. The 2012 Developer Center announcement describes historical partner access, not a current self-service license. No current signup route, data-license price, access approval or rate-limit contract was established.

Practical next step: use the verified [ESPN Fan Support entry point](https://support.espn.com/) to request routing to the authorized ESPN digital-data/licensing team. This is a routing request, not an identified licensing desk or promise that access is offered. Do not invent a sales email or treat a support response as a license amendment: Disney's terms say customer-service representatives cannot modify them. A written agreement from the authorized rights holder must cover automated FBS scoreboard/basic-stat retrieval, approved endpoint, batching, polling cadence, public display, derived analytics, retention and corrections, attribution, price and termination rights. Until then `ESPN_FINAL_SIGNALS_AUTHORIZED` remains unset.

Official references:
- https://disneytermsofuse.com/english/ (sections 1.D, 2.A and 2.B.x)
- https://espnpressroom.com/press-release/espn-launches-developer-center-and-api-program/ (March 5, 2012; historical only)

## Conditional self-service choice: BALLDONTLIE NCAAF

The official October 20, 2026 terms expressly permit lawful personal/commercial apps, media and analytics without a separate provider license or attribution requirement, unless separately agreed. Offering a substitute sports-data API is prohibited. The provider expressly does not clear third-party rights or claim official league endorsement; its data can aggregate third-party sources. This is a provider permission grant, not proof of upstream independence or comprehensive rights clearance.

| NCAAF plan | Published USD monthly | Published annual billing | Relevant entitlement |
| --- | ---: | ---: | --- |
| ALL-STAR | $9.99 | $95.90/year | Games, rankings and play-by-play; 60 requests/minute; no team/player-stat endpoints |
| GOAT | $39.99 | $383.90/year | Games and team/player statistics; 600 requests/minute |

Prices are per league. GOAT is the minimum documented option meeting both scores and basic-statistics requirements directly. Six monthly payments would be $239.94; that arithmetic assumes cancellation/restart availability and is not a quoted seasonal plan. Taxes or checkout charges were not established.

Access requires an account, server-held API key and the selected NCAAF entitlement. The seven-day GOAT trial requires payment details and converts to paid access; starting it is not authorized. The docs describe real-time team-game statistics, batched `game_ids`/date filters and cursor pagination up to 100 rows. Game IDs need explicit crosswalking to existing canonical event identities. No numeric source-availability SLA or measured latency was established.

Before enabling, ask the documented support address `hello@balldontlie.io` to confirm upstream families for scores/statistics (especially ESPN/CFBD overlap), complete FBS/conference championship/bowl/CFP coverage, permitted permanent retention after subscription ends, and expected final-score/statistics latency. Do not count this feed and CFBD as independent confirmation until provenance is established. The recovered system can still label an authorized single-source result provisional.

Official references:
- https://www.balldontlie.io/terms.html (sections 6 and 11; permissions and third-party limits)
- https://ncaaf.balldontlie.io/ (Account Tiers, Authentication, Games, Team Stats)
- https://www.balldontlie.io/docs/ (support address)

## Negotiated-license fallback: SportsDataIO commercial CFB

SportsDataIO explicitly offers commercial public display, ingestion/caching and analytics rights within the purchased license scope. Public-facing products require commercial access; Discovery Lab is not the public-app license. Post-termination retention and attribution must be set in the agreement. Its official requirements/contact form is the practical quote route. Prices are tailored to competition, feeds and use; no published defensible dollar minimum was established. Request CFB schedules/status/final scores and team box scores only, excluding markets and optional enrichment. Require FBS postseason coverage, batching, final-score latency and permanent confirmed-data retention in the quote. No quote requested.

- https://sportsdata.io/help/data-rights-and-licensing-questions
- https://sportsdata.io/pricing
- https://sportsdata.io/contact-us

## Excluded shortcut

API-Sports publishes NCAA endpoints and inexpensive plans, but its terms expressly say it does not provide publication licensing or commercial competition rights and puts necessary permissions on the user. It therefore cannot be presented as an already authorized shortcut. https://api-sports.io/terms

## Decision

Complete and test the provider-neutral lifecycle now. Keep all live rapid acquisition disabled until documented entitlement and use rights are attached to its source policy. BALLDONTLIE GOAT is the most concrete self-service candidate identified for an owner-authorized evaluation; SportsDataIO is the clearest negotiated-license fallback. Neither has been production-accepted. ESPN permission uncertainty must not block fixture-based implementation, and no purchase follows from this document.
