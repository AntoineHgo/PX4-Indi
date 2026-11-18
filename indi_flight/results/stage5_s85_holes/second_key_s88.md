# T188 second-key review: hole_report.py max-hole rule (commit dd9dd0705e)

Reviewer: second key (code vs specification). The first author's notes (fixes_s88.md) were not read.

## Verdict: AGREE WITH MINOR

S1 and S3 hold. S2 holds for topics at 50 Hz or faster. For slower topics the excess limit is not applied to gaps below 1.5 x median, and the reported max excess under-reports in that band.

## Spec check

- **S1 (raw max, before dup cancelling): AGREE.** `raw_gaps` (hole_report.py:74-82) sorts and uses the raw `np.diff` with no duplicate cancelling. Synthetic case D (50 Hz, 31 ms gap right after a duplicate stamp) FAILs with max_hole 31.00 ms.
- **S2 (median of raw dt, excess > 10 ms, verdict on excess): AGREE for >= 50 Hz, MINOR gap below.**
  - Median is taken from raw diffs in `find_gaps` (line 52) and `raw_gaps` (line 81). The verdict uses `exc` (lines 106-107).
  - Case B (50 Hz, 31 ms) FAILs and case A (50 Hz, 29 ms) PASSes, as specified.
  - Deviation: the gap test is `dt > GAP_FACTOR * med` (hole_report.py:53 and :82, GAP_FACTOR = 1.5). For median > 20 ms (rate < 50 Hz) an excess above 10 ms can sit below 1.5 x median and is never tested. Case E (20 Hz, 61 ms gap, excess 11 ms) returns PASS; the spec says FAIL.
- **S3 (count check unchanged): AGREE.** The commit's code diff touches only `raw_gaps`, `_stats`, the `analyse` max/excess plumbing, and `fmt`. `find_gaps`, `count_missing`, `gm`/`cm`/`tol`/`count_disagree` (lines 149-161) are unchanged. The only hole_report.py edits in the diff are the docstring and the new output columns.

## Findings

1. **MINOR (verdict, slow topics only), hole_report.py:82 and :53.** The gap filter uses only the 1.5 x median threshold, so the 10 ms excess limit cannot fire below that threshold. Suggested fix, not applied: include `dt > min(GAP_FACTOR * med, med + LIM_HOLE_MS * 1000)` in `raw_gaps`. For med <= 20 ms the existing condition is unchanged. No logged topic is known to run below 50 Hz; this is unverified against real logs.
2. **MINOR (reporting, S1), hole_report.py:105-106 with :82.** Same root cause. A sub-threshold gap is not in `raw`, so max_hole_ms and max_excess_ms do not include it. Case A (50 Hz, 29 ms gap, excess 9 ms) prints max_hole 0.00 and max_excess 0.00. The spec says the reported max is the largest raw dt, so this should read 29.00. The verdict is unaffected at <= 20 ms median.
3. **MINOR (pre-existing, not introduced by dd9dd0705e), hole_report.py:58.** If more than half the diffs are zero, median dt is 0 and `round(dt[i] / med)` divides by zero. The result is a RuntimeWarning and then `OverflowError` from `find_gaps`, which `analyse` calls at lines 124 and 141 before `raw_gaps`. This fails loudly rather than passing silently (case H). A guard for `med <= 0` would make the failure explicit.
4. **Note (no action needed), hole_report.py:125 and :142.** A topic with fewer than 3 samples is skipped entirely (no row, class n/a). Spec is silent. Three samples with a 31 ms gap is not a hole because the median of two diffs is 25.5 ms, which matches the spec.
5. **Units and sorting: AGREE.** Timestamps are us throughout; the /1000 conversion to ms (lines 105-106) matches LIM_HOLE_MS. Unsorted input is sorted in `find_gaps`, `raw_gaps` and `count_missing`; case C (shuffled) gives the same result.

## Evidence

- `python3 -B indi_flight/bench/tests/test_hole_report.py | tail -n 5`: 4 S88 lines shown, last line `ALL PASS`.
- Scratch script: `/tmp/claude-1001/t188_second_key.py`, with an extra offset check run inline.

| Case | Spec | Code | Result |
|---|---|---|---|
| A 50 Hz, 29 ms gap | PASS | PASS (max 0.00, exc 0.00) | ok, but reported max under-reported (finding 2) |
| B 50 Hz, 31 ms gap | FAIL | FAIL (max 31.00, exc 11.00) | ok |
| C 50 Hz, 31 ms, shuffled | FAIL | FAIL | ok |
| D 50 Hz, 31 ms, dup before gap | FAIL | FAIL (max 31.00) | ok |
| E 20 Hz, 61 ms gap (excess 11) | FAIL | PASS | MISMATCH (finding 1) |
| F 20 Hz, 51 ms gap (excess 1) | PASS | PASS | ok |
| G 3 samples, 31 ms, offset past 1 s | PASS (median 25.5 ms) | PASS | ok |
| H median dt = 0 | PASS (no crash) | OverflowError | MISMATCH (finding 3) |
| I 2 samples | n/a | class n/a | ok (finding 4) |

No commits were made and no simulations or docker were run.
