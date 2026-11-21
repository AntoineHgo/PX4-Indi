# G4 chatter, S175: time localisation, PID reference, key1 vs key2

Script: `chatter_s175.py` (uses `bench/g3_checks.py` key1 load/line_detector/uniform and `bench/g3_checks_key2.py` key2 psd_windows/sustained, unmodified). Raw per-run output: `chatter_s175_raw_indi.txt`, `chatter_s175_raw_pid.txt`.
Commands (repo root):
- `indi_project/docker/run.sh -n chat -t 900 -- python3 indi_flight/results/g4_gate_s169/chatter_s175.py` (6 INDI hover typ/harsh runs)
- `indi_project/docker/run.sh -n chatp -t 900 -- python3 indi_flight/results/g4_gate_s169/chatter_s175.py <4 PID run dirs>`
- PID typ flight (stock params, same flags as the A-56 PID harsh runs, `--vib-acc 10`): `run_scenario.py --controller pid --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --scenario hover_long --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 --out results/g4_gate_s169/pid_hover_typ_s1` (rc 0). Note: INDI uses the freeze params file, PID the stock params (as in A-54/A-56).

Per-window flag = Q14 (key1 definition: 4 s Hann window, hop 0.5 s, 20-100 Hz, peak > 20 x median, line RMS +-2 bins >= 5e-4), any motor. Window times are [start, end]; the flagged union starts up to 4 s before the event that causes it.
nav_state: 4 LOITER, 17 TAKEOFF, 14 OFFBOARD, 18 AUTO_LAND. Phases of every run: TAKEOFF (~7-14 s), LOITER (14-29), OFFBOARD hold (29 to ~96), AUTO_LAND (~96 to ~107, last change 18->14 = landed/disarm).

## 1. INDI hover, time localisation (s, log time)
| run | AUTO_LAND entry | landed (18->14) | flagged span near land (peak Hz, max line RMS) | flagged windows in OFFBOARD hold (t_off+3 .. land) | flagged span at take-off |
|---|---|---|---|---|---|
| hover_typ_s1 | 96.1 | 106.6 | 94.0-100.5 (22.3, 2.4e-03); 102.0-107.5 (20.0, 1.2e-03) | 0 of 121 | none |
| hover_typ_s2 | 95.9 | 106.6 | 94.0-101.5 (22.3, 1.7e-03); 102.0-107.0 (22.0, 7.5e-04) | 0 of 120 | none |
| hover_typ_s3 | 96.9 | 107.5 | 94.5-102.5 (22.3, 1.9e-03); 103.5-107.5 (21.0, 8.0e-04) | 0 of 122 | 18.5-22.5 (20.0, 5.2e-04), 1 window |
| hover_harsh_s1 | 96.0 | 107.0 | 94.5-98.5 (22.5, 5.6e-04); 97.5-105.5 (22.5, 2.0e-03); 103.0-107.5 (22.3, 9.2e-04) | 0 of 121 (max ratio>20 RMS 2.6e-04) | 9.5-20.0 (20-24 Hz, 5.6e-04 to 6.9e-04), 9 windows |
| hover_harsh_s2 | 96.0 | 106.9 | 94.5-105.0 (22.3, 3.9e-03) | 0 of 120 | 9.5-17.0 (20-22.5 Hz, 5.7e-04 to 6.1e-04), 6 windows |
| hover_harsh_s3 | 96.9 | 107.9 | 96.5-100.5 (20.3, 5.3e-04); 98.5-106.5 (22.5, 2.1e-03); 104.0-108.5 (20.4, 8.9e-04) | 0 of 122 | 9.5-20.5 (20-22.8 Hz, 6.3e-04 to 9.1e-04), 11 windows |

Reading:
- The ~22 Hz line begins with AUTO_LAND entry (first flagged window ends 1.5-2.5 s after entry... the 4 s window starting at 94 contains 2 s of descent), lasts the whole landing (~10 s) to touchdown/disarm, amplitude 1.7e-03 to 3.9e-03 (typ and harsh alike, peak at mid-descent).
- It is absent from the steady OFFBOARD hold: 0 of 120+ windows flagged in all 6 runs; the largest line RMS in a ratio>20 hold window is 1.0-1.1e-04 (typ) and 2.6e-04 (harsh), below the 5e-4 floor. Hold runs 29 s to AUTO_LAND (the 60 s nominal hold event is cut by AUTO_LAND at ~96 s).
- Harsh runs also show a weaker (5.6e-04 to 9.1e-04, 1.1-1.8x the floor) 20-24 Hz line during take-off/loiter (windows spanning ~9.5-20 s: take-off 7-14 s, then loiter). Typ shows it in 1 window of 1 run only.

## 2. PID reference, same profile and seed (Q14 flag, no skip)
| run | AUTO_LAND entry | landed | flagged windows | max line RMS (window span, Hz) | hold flagged | take-off flagged | chatter sustained key1/key2 (all 4 span/skip combos) |
|---|---|---|---|---|---|---|---|
| pid_hover_typ_s1 (new) | 97.6 | 108.2 | 3 (103.0-108.0) | 6.5e-04 (20.0) | 0 of 121 | 0 | 0/0 |
| a54 pid_hover_harsh_s1 | 99.3 | 110.1 | 4 (104.5-110.0) | 9.8e-04 (24.3) | 0 of 120 | 0 | 0/0 |
| a56 pid_hover_harsh_s2 | 97.2 | 108.1 | 3 (103.0-108.0) | 6.7e-04 (20.0) | 0 of 120 | 0 | 0/0 |
| a56 pid_hover_harsh_s3 | 98.0 | 108.8 | 3 (103.5-108.5) | 6.4e-04 (21.5) | 0 of 121 | 0 | 0/0 |

PID: no line at land entry (first flagged window starts ~5.5-6 s after entry, ~5 s before landed, i.e. final touchdown only), 3-4 windows (about 1.5-2 s of flagged span), RMS 6.4e-04 to 9.8e-04 (1.3-2x the floor), at 20-24 Hz at touchdown. The INDI landing line is 8-11 s long (from entry) and 2-6x larger (1.7e-03 to 3.9e-03). So PID does not show the same line at the same instants; at most a touchdown transient in the same band, below the sustained criterion.
Caveats: PID runs use stock params, one seed per profile for typ (one flight), landing time differs by 1.5-3 s between runs because take-off timing differs; PID harsh seeds 1-3 vs INDI harsh seeds 1-3 are different files but same seed numbers.

## 3. Why key1 and key2 counts differ
Window definitions (both over the whole airborne span for chatter, not the 10 s hold):
- Airborne span: key1 height > 1.0 m (AIRBORNE_M), key2 height > 0.3 m, so key2 includes ~1 s more at each end (take-off start, landing end) (e.g. typ_s1 key1 11.5-102.1 s, key2 10.6-103.1 s). Both spans include take-off and the AUTO_LAND descent (key1 ends at the last h>1 m sample, so the final touchdown is outside key1 but inside key2).
- Line RMS integration: key1 +-2 bins (+-0.5 Hz at the 4 s window), key2 +-2 Hz (the md says "+-2 Hz" for key1 but the code is +-2 bins). Also key1 resamples to the median logged rate with a 20-100 Hz band per motor, key2 to 800 Hz; "sustained" needs 3 consecutive 1 s-step windows within 10 % frequency in both. Borderline streaks therefore flip.
- Count reconciliation: hover 9 runs key1 4/9 vs key2 7/9; cruise 9/9 both (key1 table "cruise 0/9 PASS" = 9 flagged). The 3 extra key2 hover flags are hover_quiet_s1, quiet_s2, harsh_s3 (key1 max line RMS there 7.3e-4, 8.1e-4, 9.1e-4 but not sustained; key2 RMS 1.1e-3, 1.1e-3, 2.3e-3 with the wider +-2 Hz integration). Not re-run in this note (typ/harsh only), so the attribution to RMS width is consistent with the numbers but UNVERIFIED for the quiet runs.

Common-window experiment (this script, 6 INDI hover typ/harsh runs, chatter sustained, key1 detector / key2 detector):
| span | no skip | 3 s skip after every nav_state change (Q15-style, applied to chatter) |
|---|---|---|
| key1 span (h>1.0 m) | typ s1 1/1, s2 1/1, s3 1/1; harsh s1 0/1, s2 1/1, s3 0/0 | 0/0 in all 6 |
| key2 span (h>0.3 m) | typ s1 1/1, s2 1/1, s3 1/1; harsh s1 0/0, s2 1/1, s3 0/1 | 0/0 in all 6 |
Summary: with the same span and no skip, the two detectors still disagree on 2 of 6 runs (harsh_s1 and harsh_s3, borderline streaks flipping with the span edge or the RMS width), agreement 4/6. With the 3 s skip applied to chatter, both keys give 0 of 6 flagged (full agreement); that includes the typ runs and harsh_s2 that flagged without skip.
Caution on the skip: the skip windows [entry, entry+3 s] and [landed change, +3 s] remove the windows that overlap the transition, and the remaining landing windows no longer form 3 consecutive flagged windows within 10 % frequency, so the verdict flips to 0/6. The line itself (~10 s in AUTO_LAND, 2-4e-03) is unchanged. The skip was applied to chatter only in this script (not in the shipped checkers, which skip item 2 only). Cruise not re-run with the skip here.
