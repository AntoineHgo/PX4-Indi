# G3 route B re-fly (S239)

Route B per GATES.md "Owner amendment S225": FREEZE-10 kept, G3 300 fail-fast on gate binary 903eae63 (pinned by
bench/g3_chain.sh), the saturation-corner draws that also have a weak motor on are class (b), excluded, reported later.

## Exclusion mechanism
New chain option `--exclude-sat-weak` (bench only, no firmware change): at the first start it computes from
g3_sample.campaign(173, 300) the draws with saturation.on and weak_motor.on, pins them in DIR/chain_exclude.txt and
DIR/EXCLUDED_CLASS_B.json; the chain skips them (progress line "EXCLUDED class (b)"), status shows `excluded_class_b`.
Excluded: 262, 264, 269 (all corner C3; weak scale 0.990, 0.709, 0.929). The other 7 C3 draws (260, 261, 263, 265-268,
no weak motor) and all in-range draws (sag, weak >= 0.7) stay counted: 297 flights. Verified by status (remaining 3 on
range 260-264 with 262, 264 excluded) and a start/stop check; no self-test exists for g3_chain.sh.

## Pre-test (exact chain config, 903eae63, speed 1, MC_INDI_POS_EN as the chain sets it)
- draw 0 (pretest/): flight rc=0, result ok, 160 s, run.json and metrics.json present, both keys scored: pass / pass.
- draw 37 (pretest37/; weak motor 3, scale 0.743, in range): flight rc=0, result ok, 160 s, run.json and metrics.json
  present, both keys scored by the chain: key1 FAIL, key2 FAIL with empty failing-item lists (item breakdown not
  examined here; the scorer ran in both keys, so not a set-up fault).
- A first start on a scratch dir was stopped after 6 s (rc=143) and the dir removed; no flight result came of it.

## Campaign
- dir: indi_flight/results/g3_routeB_s239/campaign, started 2026-11-26 08:00:56, `--halt-on-fail` (fail-fast), serial, speed 1.
- launch: `bash indi_flight/bench/g3_chain.sh start indi_flight/results/g3_routeB_s239/campaign --halt-on-fail --exclude-sat-weak`
- PIDs: inhibit wrapper 1816871, chain 1816878 (the only waiter; flight timeouts 1700 s host / 1500 s container / 1200 s run are inside the chain).
- resume (after a halt or stop): if halted, remove CHAIN_HALTED and HALT_ON_FAIL.json in the dir; then the same start command (finished runs are skipped).
- status: `bash indi_flight/bench/g3_chain.sh status indi_flight/results/g3_routeB_s239/campaign`; also `tail -n 20` of campaign/progress.txt.
- stop: `bash indi_flight/bench/g3_chain.sh stop <dir>` (after the current run) or with `--now`.
- ETA about 11 h (297 flights).
