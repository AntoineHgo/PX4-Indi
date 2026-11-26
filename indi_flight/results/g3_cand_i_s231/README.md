# G3 candidate (i) S231: MC_INDI_ACT_BLD 0.10 s, 4 pass-line flights (event hover scenario)

Pass line: DECISIONS.md D-RATE-BLD-2 bullet "S226 ACTIVE" (+ D-RATE-BLD-2-C1). Gate binary build/px4_sitl_default/bin/px4 sha256 903eae63ceb1 (checked before start; no rebuild). No other docker container was running at start.

## Candidate params
`cand_i.params` = `g5_freeze_s157/params.params` with one line changed. Diff:
```
31c31
< MC_INDI_ACT_BLD 1.0
---
> MC_INDI_ACT_BLD 0.10
```
(`g3_run.py --samples ... --require-actc` replaces MC_INDI_ACT_TC with the drawn value on the sample draws, as in all S212 re-flies.)

## Draw definitions (checked)
- joint: `g3_refly_actc_s212/restore264/samples_joint` idx 24 (as indi_joint / falsifier_s222 / blend_s223), seed 1528771325.
- 264: C212 run_024 = `g3_refly_actc_s212/samples` idx 24 (source_run 264), seed 1528771325.
- 262: C212 run_022 = `g3_refly_actc_s212/samples` idx 22 (index.json source_run 262), seed 662687257. NOTE: the S230 FREEZE-10 baseline `g3_pretest_s230/indi_d262` was flown WITHOUT samples (campaign draw 262): same seed and plant factors but no ACT_TC (`actc`) draw (g3_draw.json differs by the actc block only). The baseline therefore is not the same ACT_TC as the pass-line draw 262; see SCORES.md.
- 283: g3_campaign_f10 run_283 = plain campaign draw (--seed 173 --n 300 --start 283, no samples), seed 1555206049; identical to S230 `indi_d283` draw.

## Flights
`chain.sh` (setsid, sequential, timeout 1700 s each), same g3_run.py command as g3_pretest_s230/chain.sh plus `--samples <dir> --require-actc` for joint, 264, 262; `--speed 1`, `--base-params cand_i.params`. Status: STATUS.txt. Raw .ulg not for git.

## Result (S231)
Scored: see SCORES.md. joint PASS, 264 MISS, 262 MISS, 283 MISS (key 1) / not worse (key 2).
