# Freeze-8 pre-test (S181): cruise_typ seeds 2, 3 and G2-STEP attitude cell, firmware at HEAD
Not a gate run. Not committed. Raw .ulg untracked (git-ignored).

## Provenance
- HEAD 0335c60a7e (head.txt). `git diff 1d9ae87085 HEAD -- src` is empty, so the firmware equals the candidate (9dd5f76382 + d65111154b + d2f3845292, MC_INDI_XY_P yaml default 1.2). Tree dirty only in bench/doc files (STATE.md, attitude_break_check.py, margins_models.py, a test), not firmware.
- Build: `indi_project/docker/run.sh -n s181build -t 2400 -- make px4_sitl_default` rc=0 (build.log, 715/715), rebuilt at HEAD. No stray containers at start.
- f4_probe_s180 flew with `g55_gain_probe_s179/params_xyp12.params`, which sets MC_INDI_XY_P 1.2 and MC_INDI_XY_VP 3.6 explicitly. This pre-test does NOT: `params_freeze.params` = `g5_freeze_s157/params.params` without comments, no XY_P/XY_VP line (the freeze file has none; `diff` against xyp12 is exactly those 2 lines).
- Confirmed from the flight logs (params_check.py): cruise_typ_s2 and s3 initial parameters MC_INDI_XY_P = 1.2 (1.2000000477), MC_INDI_XY_VP = 3.6, i.e. the new yaml defaults.

## Commands (repo root, fly.sh)
- cruise: `timeout 1300 indi_project/docker/run.sh -n s181_cruise_s$s -t 1300 -- python3 indi_flight/bench/run_scenario.py --controller indi --model quad5in --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 --seed $s --scenario traj_lemniscate --params $R/params_freeze.params --out $R/cruise_typ_s$s` (the f4 cruise_typ_s1 command from g55 fly_rest.sh stream c, with seed and params changed). rc=0 both (done.txt).
- steps: `... run_scenario.py --scenario step_{roll,pitch,yaw} --controller indi --model quad5in --sim v2 --rate-hz 800 --seed 1 --speed 4 --params indi_flight/results/g2_step_s64/indi.params --out $R/steps_seed1/<sc>_indi`, timeout 900, as g2_step_s64 fly.sh.ref. rc=0 all.
- scoring: `sh score.sh` in docker (copy of f4 score.sh, s2+s3, RAW=$R/chatter_raw_<run>.txt; tracked g4_gate_s169 raw untouched, `git status --short indi_flight/results/g4_gate_s169` empty). Output score_out.txt, skip_key1.md. Per-motor lines: lines.py -> lines_out.txt. Steps: `bench/g2_step_metrics.py` -> g2_step_primary.json, step_out.txt; second key `bench/t127_step_metrics_key.py` -> key2_{roll,pitch,yaw}.md.

## Item 1: cruise_typ s2, s3 (window 35.2-53.5 s log time, lemniscate cruise incl. ramp/hold end, as f4's 36-53.5)
Per-motor line RMS (+-2 Hz, 4 s windows hop 1 s, max over the 15 windows). Both keys (key1 fixed +-2 Hz uniform grid, key2 k2 grid) agree to 3 digits; key1 shown.
| run | 89 Hz m0/m1/m2/m3 | 33.5 Hz m0/m1/m2/m3 | flagged windows (ratio>20 and RMS>=5e-4), key1 / key2 |
|---|---|---|---|
| s2 | 4.04 / 3.83 / 4.16 / 3.92 e-4 | 2.60 / 3.19 / 2.64 / 3.26 e-4 | 0/15 per motor / 0/15 per motor |
| s3 | 4.12 / 3.86 / 4.12 / 3.86 e-4 | 2.68 / 3.22 / 2.66 / 3.06 e-4 | 0/15 per motor / 0/15 per motor |
f4 s1 for comparison: 89 Hz 3.88-4.16e-4, 0 of 14 flagged. Limit 5e-4: max 4.16e-4 (83 %), PASS.
Official detectors (score_out.txt, skip_key1.md): sustained chatter 0/0/0 (key1 fixed, key1 old, key2) in every span variant; skip_key1 table: cruise window 0/51 flagged, key1 peak 89.3 Hz 4.15e-4 (s2, m0), 88.8 Hz 4.20e-4 (s3, m0), chatter no; key2 chatter no (s2 peak 22.2 Hz 1.48e-4, s3 peak 88.8 Hz 4.19e-4). Only flagged span in each run is AUTO_LAND (64.5-72 s, 20 Hz, 2.5e-3 s2 / 2.1e-3 s3, 8/139 and 5/138 windows), outside the cruise window, same as f4 s1 (2.1e-3, 3/137) and F2 (1.9e-3). takeoff/loiter, pre-traj, ramp, cruise, hold: 0 flagged windows in both.
G4 table (cruise): R20 0.022 / 0.021 % (limit typ 1.5 % x1.5 cruise = 2.25 % per GATES lines 356,360), C20 6.6e-4 / 6.5e-4 (0.006 x1.5 = 0.009), R4 0.314 / 0.303 %, clip 0.0000 both. Item 2 PASS both, item 1 (loss of control) PASS both. Item 3: s2 FAIL, s3 PASS; f4 s1 FAIL: the known steady-state window artefact for the lemniscate (RECONCILE_S180.md: PID shows the same 0.295 m offset). s2 item 3 not re-investigated here (UNVERIFIED that it is the same artefact; the s1 reconcile covers s1 only).
Loss-of-control signs: none (clip 0, item1 pass, item2 pass, no nav_state failsafe, takeoff to landing completed, gc_landed at 90-91 s).
Verdict item 1: PASS both seeds.

## Item 2: G2-STEP attitude cell (GATES.md:171; last run results/g2_clean_s68, S64 first test), seed 1, 800 Hz, HEAD binary
Limits: roll/pitch est overshoot <= 5 %, 2 % settle <= 450 ms; yaw overshoot <= 5 %, settle <= 1350 ms; truth overshoot <= 5 %.
| axis | rise ms | est OS % | est settle ms | truth OS % | pass |
|---|---|---|---|---|---|
| roll 15 deg | 190.7 | 0.47 | 345.0 | 0.21 | yes |
| pitch 15 deg | 187.8 | 0.83 | 326.3 | 0.85 | yes |
| yaw 45 deg | 611.1 | 0.07 | 1138.8 | 0.00 | yes |
Second key (key2_*.md) AGREES on rise/OS/settle (roll 191.2/0.47/345.0, yaw 611.2/0.07/1138.8). Verdict: PASS 3/3 (one seed only; the gate needs >= 3 seeds).
Notes: (a) params are g2_step_s64/indi.params (ACT_TC 0.05, POS_EN 0, G1 derived), the gate's defined cell, not the freeze params: attitude mode, so MC_INDI_XY_P is not exercised and the XY_P change is not tested by this cell; flight log shows XY_P absent. (b) Yaw rise 611 ms / settle 1139 ms against S64 544 ms / 913-923 ms: slower than S64 but within 1350 ms (84 % of limit); cause not investigated (firmware changed since S64). Margin warning for the re-fly.
