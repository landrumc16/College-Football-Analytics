# V9 Device Testing: Real-Device Options and Release Confidence

The owner asked to avoid manual testing. This records what real-device cloud testing is available at no cost, what was
automated instead, and whether the evidence is sufficient for release. **No physical hardware was tested. Every
result below is emulation**: real browser engines with device viewports, touch and mobile user agents, but no physical
phone.

## Real-device cloud services (researched November 26, 2026)

| Service | Real iPhone and Android hardware | Cost and access | Owner action needed |
| --- | --- | --- | --- |
| BrowserStack Open Source | Yes (large real-device cloud) | Free for qualifying open-source projects; [program page](https://www.browserstack.com/open-source), first announced [2018](https://www.browserstack.com/press/browserstack-announces-its-open-source-program-to-drive-community-innovation). Current eligibility not published | Apply with the public repository; once approved, store the access key as a GitHub secret |
| TestingBot open source | Advertised, including real iOS/Android | [Free open-source plan](https://testingbot.com/open-source.md), 2 concurrent tests (vendor claim) | Apply; add a secret |
| Sauce Labs Open Sauce | Unconfirmed for real devices ([program](https://saucelabs.com/resources/blog/announcing-open-sauce-free-unlimited-testing-for-open-source-projects)); its [Real Device Cloud](https://saucelabs.com/platform/real-device-cloud) is paid, with a 28-day trial | Free OSS tier; real devices paid | Apply or start a trial |
| AWS Device Farm | Yes | [One-time 1,000 free device minutes](https://aws.amazon.com/device-farm/pricing), then $0.17/min | AWS account with a payment method |
| Firebase Test Lab | Android physical devices ([Spark: 5 physical runs/day](https://firebase.google.com/docs/test-lab/usage-quotas-pricing)) | Free quota | Built for Android app packages, not website/PWA testing; would need a wrapper app |
| LambdaTest / TestMu AI | Real devices limited on the free tier ([pricing summary](https://www.capterra.com/p/170732/LambdaTest/pricing/)) | About 100 automation minutes on the free plan | Account; real-device minutes unclear |

**Conclusion:** every real-hardware option requires the owner to create an account. That means an open-source
application, or a trial with a payment method. The access key then has to be stored as a GitHub Actions secret, which
the owner must add (it must never be pasted into chat). None of this could be done autonomously. Nothing was
purchased and no account was created.

If the owner wants hardware coverage with no further manual testing, the lowest-effort path is:
1. Apply to BrowserStack Open Source (or TestingBot).
2. Add the key as a repository secret.
3. Point the automation below at that service. It is already written as Playwright scripts, which both services can
   run on real devices.

## What was automated instead (no cost)

Temporary branch `v9-device-acceptance` (GitHub Actions run 45760268721): the V9 checklist automated on the offline
V9 review build.

| Profile | Engine | Navigation, five destinations | Favorites (save, browse another school, reload) | Rankings filter, trajectory, matchup, projections, Offense & Defense, calibration, Market | Playoffs what-if override and exact reset | Overflow and small targets |
| --- | --- | --- | --- | --- | --- | --- |
| iPhone SE (320 px) | **WebKit (Safari engine)** | Pass | Pass | Pass | Pass (98.1% to 91.1%, exact reset) | None |
| iPhone 13 (390 px) | WebKit | Pass | Pass | Pass | Pass | None |
| iPhone 14 Pro Max (430 px) | WebKit | Pass | Pass | Pass | Pass | None |
| iPad Mini (768 px) | WebKit | Pass | Pass | Pass | Pass | None |
| Pixel 7 (412 px) | Chromium | Pass | Pass | Pass | Pass | None |
| Galaxy S9+ (320 px) | Chromium | Pass | Pass | Pass | Pass | None |

This is the first V9 test of the **Safari/WebKit engine**; all earlier evidence used Chromium. The Chromium profiles
add to the existing five-width Chromium acceptance, `mobile-smoke` with its Android offline-app checks, and
`adversarial-reliability` (34 scenarios, including offline-cache recovery).

**Offline app (PWA):**
- **Chromium (Android profiles):** worker registration, control, the offline page when offline, online recovery and
  the update notice with old-cache removal are verified (`docs/V9-INDEPENDENT-ACCEPTANCE.md`, re-checked here on the
  Pixel 7 profile). One reading in the long device run was blank; it does not reproduce and is treated as a harness
  timing artefact, not a verified failure.
- **WebKit:** the worker registers. Headless Linux WebKit then crashes on any later page load, which is a known
  limitation of the test engine, so offline and update behaviour on iPhone remain **unverified**.

## Remaining risk without hardware

| Risk | Likelihood and impact | Mitigation in place |
| --- | --- | --- |
| iPhone offline and update behaviour (installed app) | Medium likelihood of minor differences. Low impact: football data is never cached, and the worker only serves an offline page | The worker logic is simple and engine-agnostic; Chromium lifecycle fully verified |
| "Add to Home Screen" install flow (Android prompt, iOS share sheet) | Low; driven by a valid manifest and icons (verified) | Manifest, icons and standalone mode checked |
| Real touch precision, fonts and hardware rendering | Low; layouts are fluid with no overflow across seven widths and two engines | Touch-emulated taps pass; targets meet 24 px except pre-existing favorites controls |
| Device performance on low-end phones | Low; under 4x CPU throttling, first contentful paint 0.45 s and largest contentful paint 0.83 s | Throttled measurements |

## Recommendation

The automated evidence gives **sufficient confidence to release V9** without owner manual testing or paid services:
- two browser engines;
- seven phone and tablet widths;
- every checklist journey automated;
- full offline-app lifecycle verification on Chromium;
- the CI and production live checks on every deploy.

The one residual gap, iPhone offline and update behaviour, is low-impact and does not affect data accuracy.

After release, production's deploy job already runs the live mobile checks automatically. If the owner later wants
hardware coverage, the BrowserStack/TestingBot open-source route above needs only an application and one secret.
The temporary `v9-device-acceptance` branch can then be deleted, or kept as the starting point.
