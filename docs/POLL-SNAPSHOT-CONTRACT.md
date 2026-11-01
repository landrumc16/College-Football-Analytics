# Published poll snapshot contract

The dashboard optionally reads `poll-snapshot.json` from the same GitHub Pages
base path as `season-report.json`. No poll rankings are fabricated or inferred.

## Expected JSON

```json
{
  "season": 2026,
  "week": 9,
  "source": "Verified publication or CFBD poll endpoint, with retrieval date",
  "ap_top25": [{"team": "Verified school name", "rank": 1}],
  "coaches_top25": [{"team": "Verified school name", "rank": 1}]
}
```

Do not publish the example as actual poll data. Populate both arrays from
verified, same-week AP and Coaches polls. Use the model's canonical school
names or retain unmatched names visibly; never guess team aliases. Store the
source URL and publication date in the source string. Do not compare different
poll weeks as though simultaneous.

A missing snapshot leaves the optional comparison hidden. The live 2026
model rankings are a current snapshot, not necessarily a reconstruction of
the rankings as of the poll publication date. Historical agreement metrics
require dated model snapshots, not today's rankings.
