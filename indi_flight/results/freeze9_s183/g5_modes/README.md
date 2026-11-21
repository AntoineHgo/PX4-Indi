# G5.1 / G5.2 / G5.7 re-fly at freeze-9 (INDI only)

Why: DECISIONS.md D-FREEZE-9-GAP. These rows were last flown at freeze-6 (results/g5_freeze_s157, keyed S159) and must be
re-flown on the current frozen firmware before the G5 verdict. Nothing here was flown by the author of this file; the batch
is chained behind the G3 pre-test (pid 825021).

## Rows and tests
| row | scenario / mode | seeds | GATES.md |
|---|---|---|---|
| G5.1 | stick_steps `--stick-mode acro --stick-pilot` (tag `_acro`), `--stick-mode stabilized --stick-pilot` (tag `_stab`) | 1 2 3 | "G5.1 exact test" (~l.422) |
| G5.2 | stick_pos_steps `--stick-mode altctl` / `posctl` | 1 2 3 | "G5.2 exact test" (~l.439); S175 Q10 B z settle band max(2 % d, 0.10 m) (~l.545) |
| G5.7 | mode_switch10 `--stick-mode posctl` | 1 2 3 | "G5.7 exact test" (~l.470) |

Flights: G5.1 6 + G5.2 6 + G5.7 3 = **15**, serial. No PID reference, no firmware-default (fwdef) cell (S158 fwdef probe is not a freeze row).

## S157 source commands (reused unchanged except --out)
- Flight: `g5_freeze_s157/fly.sh` (quad5in, `--speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0`,
  `--params g5_freeze_s157/params.params`, `timeout 1000 ... run.sh -t 900`); args per row from `batch.sh` (G5.1, G5.2) and `batch2.sh` (G5.7).
- Key 1: `g5_freeze_s157/checks.sh` -> `bench/g51_check.py DIR`, `bench/g52_check.py DIR`, `bench/g57_check.py --validity leaveP DIR`.
- Key 2 (S159): `bench/g51_g52_key2.py <g51|g52> DIR` (key2_g51_g52.md), `bench/g55_g57_key2.py g57 DIR` (key2_g55_g57.md).
- INDI start trap: params.params has `MC_INDI_EN 1`; run_scenario.py (S131) aliases it to `MC_RATE_CTL_TYPE 1`, as at S157. fly_all.sh checks
  run.json `params_applied` MC_INDI_ID_OK == 1 and MC_RATE_CTL_TYPE == 1 per flight and logs a WARN line otherwise (flight kept).
- Checkers already carry the S175 amendments (commit 315cdad412); the S157 numbers (e.g. posctl z settle 4.15 s) used the old 2 % band.

## Exact commands
Run: `bash indi_flight/results/freeze9_s183/g5_modes/fly_all.sh` (any cwd). Per flight, e.g. G5.1 acro seed 1:
```
timeout 1000 indi_project/docker/run.sh -n f9modes_stick_steps_s1_acro -t 900 -- python3 indi_flight/bench/run_scenario.py --controller indi \
  --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
  --params indi_flight/results/g5_freeze_s157/params.params --scenario stick_steps --stick-mode acro --stick-pilot \
  --out indi_flight/results/freeze9_s183/g5_modes/stick_steps_s1_acro
```
Output tags: stick_steps_s{1,2,3}_{acro,stab}, stick_pos_steps_s{1,2,3}_{altctl,posctl}, mode_switch10_s{1,2,3}.
Only containers named `f9modes_*` are stopped by the script (never the G3 `g3p187_*` containers).

## Launch (done S183, detached, chained after the G3 pre-test pid 825021)
```
nohup bash -c 'while kill -0 825021 2>/dev/null; do sleep 30; done; bash indi_flight/results/freeze9_s183/g5_modes/fly_all.sh' \
  > indi_flight/results/freeze9_s183/g5_modes/batch.nohup.log 2>&1 &
```
Progress: `batch_status.txt` (lines `fly <tag> rc=`, `key1/key2 <tag> rc=`, `FLY_DONE`, `SCORE_DONE`).

## Expected wall time
S157 flights took ~35-40 s of flight wall time each (run.json wall_time_s ~34 s for acro; log timestamps ~35-40 s between the G5.1/G5.2
flights, ~40 s for mode_switch10) plus container start-up: about 1 min per flight, 15 flights = **~15-20 min**, scoring ~2-3 min.
Starts when the G3 chain ends (~40 min after its launch).

## Resume
Rerun the same `fly_all.sh` (flights with an existing `<tag>/flight.ulg` are skipped; scoring always re-runs). If the waiting
`bash -c` was lost, start fly_all.sh directly once no G3 container is running. `NOFLY=1 bash .../fly_all.sh` scores only.
A flight that failed leaves a partial dir without flight.ulg or with a bad run.json: delete that tag directory by hand and rerun.

## Scoring commands (written by fly_all.sh, text next to each flight dir)
| row | key 1 (`<tag>.key1.txt`) | key 2 (`<tag>.key2.txt`) |
|---|---|---|
| G5.1 | `python3 bench/g51_check.py DIR` | `python3 bench/g51_g52_key2.py g51 DIR` |
| G5.2 | `python3 bench/g52_check.py DIR` | `python3 bench/g51_g52_key2.py g52 DIR` |
| G5.7 | `python3 bench/g57_check.py --validity leaveP DIR` | `python3 bench/g55_g57_key2.py g57 DIR` |

S157 had no scorer json for these rows (text only), so none is written. Raw ulg, rootfs, sticks.csv and *.log are covered by
indi_flight/.gitignore (checked with git check-ignore); key*.txt, run.json, batch_status.txt are committed with the results.

## PID reference (S188)
Why: G5.7 failed 3/3 (both keys) for INDI, and the owner rule is that a failing gate row is first flown with the PID reference,
same scenario and seed. Script `fly_pid_g57.sh`: mode_switch10 seeds 1-3, `--controller pid_default` with no `--params` (the INDI
params file would start INDI), all other flags as fly_all.sh; outputs `pid_mode_switch10_s<seed>/` plus `.key1.txt`/`.key2.txt`
(same scorers as fly_all.sh), containers `f9g57pid_*`, `PID_G57_DONE` touched at the end, progress in batch_status.txt.
Command (detached, chained after the G3 PID chain pid 965041):
```
nohup bash -c 'while kill -0 965041 2>/dev/null; do sleep 30; done; bash indi_flight/results/freeze9_s183/g5_modes/fly_pid_g57.sh' \
  > indi_flight/results/freeze9_s183/g5_modes/pid_g57.nohup.log 2>&1 &
```
Resume: rerun `bash .../fly_pid_g57.sh` (flights with flight.ulg skipped, scoring re-runs); delete a failed run's dir first.
`DRYRUN=1` prints the seed-1 command.
