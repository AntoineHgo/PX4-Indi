# Item 2 split at the motor fault, S223 (draw 264 `joint`, 4 runs, no new flights)

Question: is the G3 item 2 failure (2.0 Hz line on body rates) before the motor fault (scenario/plant property shared by both stacks) or after it?

## Method
Neither scorer has a window option: `g3_checks.py` (key 1) and `g3_checks_key2.py` (key 2) run item 2 over the whole airborne span; `--t0/--t1` only move item 3. New wrapper `indi_flight/bench/g3_item2_split.py` (scorers unchanged, imported) crops the truth arrays to `[0, fault)` and `[fault, end]` and calls key 1 `load`+`evaluate` and key 2 `load_run`+`osc_rates`. Self-test (`--self-test`, docker): 2 Hz 15 deg/s sine on p only before the cut is flagged pre-cut and not post-cut by both keys. Run: `run_split.sh` in this folder, in docker; raw output `split_*.json` (also contains a whole-run check).
- Fault time = first `EC_MAX` parameter change in the log (same rule as `../scripts/tilt.py`), converted to seconds since ulog start (the keys' time base). It is within 0.04 s of the `traj` event start, where the `motor_fault` override begins (below).
- All times below are seconds since ulog start. The whole-run lines reported earlier as "from 21 s" are offsets from the airborne start (about 19.5-20.2 s), i.e. 41-48 s in this base.
- The cropped range starts with ground-level lead-in samples when it does not start at the log start, so the scorers' own airborne test works. Key-1 `pass` here is item 2 only (rates plus its position limit cycle); key-2 `pass` is its rate part only (its position limit cycle uses the hold window, not evaluated in a crop).
- Whole-run values from the wrapper reproduce the earlier key results (pid key1 FAIL q 2.0 Hz, key2 pass; p1 key1 p / key2 q; p2 both).

## Results (item 2; peak frequency 2.0 Hz = lowest bin of the 2-40 Hz band)
fault f; "line" = sustained line (Hz, first window start s, 3 windows); rms = line rms at max ratio / max flagged [deg/s]; flag floor 5 deg/s.

| run | f [s] | window | key 1 | key 2 |
|---|---|---|---|---|
| indi_joint (ACT_BLD 1.0, LOC) | 42.55 | whole (18.9-44.4) | pass | pass |
| | | pre [0,f) | pass; p/q/r rms max 0.1/0.4/0.0 | pass; 0.1/0.3/0.0 |
| | | post [f,end] | pass, but only 1.8 s airborne: no 4 s window | not scorable (airborne < 4 s) |
| pid_joint | 43.68 | whole | FAIL q line 2.0 Hz from 41.2 (rms 2.6 / 22.0); position limit cycle True | pass |
| | | pre | pass; rms max p 0.0, q 0.1, r 0.0 | pass; 0.1/0.1/0.0 |
| | | post | FAIL: no rate line (rms max 2.4/3.2/1.1 < 5); position limit cycle True | pass (no line) |
| p1_bld015 | 43.71 | whole | FAIL p line 2.0 Hz from 42.5 (14.5 / 15.5) | FAIL q line from 41.7 |
| | | pre | pass; rms max 0.2/0.2/0.0 | pass; 0.2/0.2/0.0 |
| | | post | FAIL: no rate line (rms up to 16/10/15); position limit cycle True | pass (no sustained line) |
| p2_nomeas | 43.29 | whole | FAIL p from 48.1, q from 41.1 and 48.1 | FAIL p from 48.2, q from 41.2 |
| | | pre | pass; rms max 0.1/0.2/0.0 | pass; 0.2/0.2/0.0 |
| | | post | FAIL p and q 2.0 Hz from 48.3 (13.7 / 13.7) | FAIL p and q 2.0 Hz from 48.3 (13.7) |

Position limit cycle (key 1 item 2, position): False pre-fault, True post-fault on pid_joint, p1, p2.

## Findings
1. Pre-fault, no run has any rate line above the 5 deg/s floor: all four, both keys, pass; line rms at most 0.4 deg/s (peak/median ratios of 1e3-1e4 are just a quiet spectrum). There is no 2 Hz oscillation in the hover/takeoff/settle part for either stack. It is not a scenario or plant property of the pre-fault flight.
2. The whole-run lines on pid_joint, p1 (and early ones on p2) start at 41.1-42.5 s, 1-2.6 s before the fault. A detector window is 4 s, so those windows (e.g. 41.2-45.2 s) contain the fault transient. They are fault-transient energy in windows that straddle the fault, not a pre-fault oscillation. Cropped at the fault they disappear on pid_joint (both keys) and p1 (both keys). After the fault there are fewer than 3 consecutive windows that satisfy the line criteria within the crop, so the post-fault crop does not sustain a line there.
3. p2_nomeas keeps a sustained 2.0 Hz line on p and q from 48.3 s (5 s after the fault) in the post-fault crop on both keys: a genuine post-fault oscillation of INDI without measured torque.
4. Peak frequency 2.0 Hz is the lowest bin of the 2-40 Hz detector band, so these "lines" are probably low-frequency energy (fault transient or large-amplitude slow motion) at the band edge, not a resolved 2 Hz tone. Inferred from the band definition, not tested with a different band.
5. Verdict: item 2 failures are post-fault (or fault-straddling windows), none is pre-fault. PID (pid_joint) key 1 FAIL is carried by straddling windows and the post-fault position limit cycle, so the PID stack is not an independent "clean" reference for rates around the fault. The original INDI joint run (ACT_BLD 1.0) shows no pre-fault line (pre rms at most 0.4 deg/s); it was an LOC abort (INVALID in chain_score.json, never scored by the keys) and has 1.8 s of airborne data after the fault.

## Scenario and saturation override
All four: scenario `o1_lemniscate`. Ulog-time phases: climb/takeoff ramp from the airborne start (about 19-20 s) to `settle` (hover, 3 s, starts 39.5 / 40.6 / 40.7 / 40.3 s for joint / pid / p1 / p2), then `traj` (the lemniscate, 17.8 s) from 42.5 / 43.6 / 43.7 / 43.2 s, then `hold` (3 s, only flown by the non-LOC runs, 61.5 / 61.5 / 61.1). The 41-49 s span of the whole-run lines is therefore the end of settle plus the first ~5 s of the lemniscate. Before about 40 s the vehicle is on takeoff/climb/hover only.
`g3_scenario_overrides.json` (identical in all four): `motor_fault` with `segment: traj`: all four motors thrust_scale 0.351 and motor 3 additionally 0.708998, both starting at the `traj` segment, not from the start of the flight. `g3_draw.json` factors list saturation (scale 0.351, on) and weak_motor (motor 3, 0.709, on) as the draw, but they are applied only from the traj start (the fault). Hence sat 0.351 is active only from the fault, which is why the pre-fault part is clean.

## Unverified
- Fault time taken from the `EC_MAX` parameter change, not from an independent log of the override application.
- The 2.0 Hz band-edge reading (finding 4) was not tested.
- Key 2 post-crop on indi_joint not scorable; single flights, no repeat.
