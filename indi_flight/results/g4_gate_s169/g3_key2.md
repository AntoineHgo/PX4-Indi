# G3 items 1-3 + G4 chatter: key1 vs key2 (hover runs, g4_gate_s169)

Key2 = `bench/g3_checks_key2.py`, written from GATES.md only. Cells "K1 / K2" are pass (True/False) for items 1, 2 and sustained-chatter (True = chatter flagged) for the last column. Item 3 in the run order: K1 value, then K2 value.
Window used by K2: item 3 = last 10 s of the hold (hold end = event t_us + dur_s, ulog time base; e.g. 105.1-115.1 s). In all 9 runs the vehicle is airborne in that window (min height 4.94-5.0 m above ground, `airborne_in_window` true).
Items 1-2 use the airborne span (height > ground + 0.3 m) of the whole log, per the spec "whole flight".

| run | item1 LOC K1 / K2 | item2 osc K1 / K2 | item3 K1 | item3 K2 | chatter flagged K1 / K2 |
|---|---|---|---|---|---|
| quiet_s1 | n/a / True (K2 tilt max 0.8 deg, horiz 0.102 m) | n/a / True | n/a (no key1 file in run dir) | rms 0.0414, alt +0.0068, rp -0.004/-0.002, pass True | n/a / True |
| quiet_s2 | n/a / True (K2 tilt max 0.5 deg, horiz 0.081 m) | n/a / True | n/a (no key1 file in run dir) | rms 0.0327, alt -0.0227, rp +0.017/+0.002, pass True | n/a / True |
| quiet_s3 | n/a / True (K2 tilt max 0.6 deg, horiz 0.124 m) | n/a / True | n/a (no key1 file in run dir) | rms 0.0630, alt -0.0044, rp -0.006/+0.012, pass True | n/a / True |
| typ_s1 | n/a / True (K2 tilt max 1.0 deg, horiz 0.083 m) | n/a / True | n/a (no key1 file in run dir) | rms 0.0353, alt -0.0239, rp -0.004/+0.006, pass True | n/a / True |
| typ_s2 | n/a / True (K2 tilt max 0.9 deg, horiz 0.086 m) | n/a / True | n/a (no key1 file in run dir) | rms 0.0442, alt -0.0288, rp +0.011/+0.007, pass True | n/a / True |
| typ_s3 | n/a / True (K2 tilt max 1.3 deg, horiz 0.100 m) | n/a / True | n/a (no key1 file in run dir) | rms 0.0596, alt +0.0299, rp -0.015/+0.011, pass True | n/a / True |
| harsh_s1 | True / True (K2 tilt max 11.3 deg, horiz 0.146 m) | False / True | rms 0.0453, alt +0.0478, rp +0.004/+0.002, pass True | rms 0.0739, alt -0.0264, rp +0.031/-0.011, pass True | True / True |
| harsh_s2 | True / True (K2 tilt max 9.0 deg, horiz 0.073 m) | False / False | rms 0.0372, alt -0.0083, rp -0.001/-0.002, pass True | rms 0.0344, alt +0.0303, rp -0.013/-0.009, pass True | True / True |
| harsh_s3 | True / True (K2 tilt max 11.1 deg, horiz 0.090 m) | False / True | rms 0.0423, alt +0.0512, rp +0.002/-0.001, pass True | rms 0.0412, alt -0.0470, rp -0.014/-0.064, pass True | True / True |

## Verdict
- Item 1 (LOC): agree on pass for the 3 runs that have a key1 file. Tilt max differs (K1 1.5-1.6 deg, K2 9-11 deg) because K2 includes takeoff and the landing touch-down in its tilt scan; neither exceeds 60 deg for 0.2 s.
- Item 2 (oscillation): agree on 2 of 3 compared runs (harsh_s1, harsh_s3: no sustained oscillation). DISAGREE on harsh_s2: K2 flags q at 2 Hz (rms 9.8 deg/s, 3+ windows starting 83 s into the airborne span = about 117 s ulog, after hold end at 115.0 s, i.e. the descent/landing). Cause confirmed by re-running K2 truncated at hold end: no flag on any run, p/q/r max flagged rms <= 3.8 deg/s. K1's airborne span ends at its t_land, K2's at the last sample with height > 0.3 m; the 2 Hz flag is a landing transient and is excluded by K1. Which span the gate wants ("whole flight" vs up to touchdown) needs an owner decision. Position limit cycle: both pass (K2 max detrended p2p 0.19 m, one 10 s window).
- Item 3: pass/fail agree (all pass) but values differ, largest = altitude mean, harsh_s3: K1 +0.0512 vs K2 -0.0470 (diff 0.098 m); harsh_s1 alt +0.0478 vs -0.0264 (0.074 m); horizontal RMS harsh_s1 0.0453 vs 0.0739 (0.029 m). Probable causes (not proven, key1 code not read): K1 uses a 55 s window (36.98-91.98 in its time base) with a trajectory-setpoint reference; K2 uses the last 10 s with the reference = median position over the first 1 s of the hold. Roll/pitch means agree within 0.05 deg (all << 1.0). Roll/pitch gate is attitude-mode only; these runs are position mode, so K2 reports but does not gate it (K1 lists it as gated threshold 1.0).
- Chatter (20-100 Hz, peak > 20 x median): both flag all 4 motors in the 3 harsh runs at 70 Hz (K2 peak/median 2700-3300 over the hold; K1 line 69.8-70 Hz). Agree.

## Other findings and unverified items
- K2 also flags chatter in EVERY run, including quiet (22 or 39 Hz, peak/median 1200-5500) and typ (70 Hz, ratio 430-700; typ_s2 m3 22 Hz). On quiet runs the command std in hold is 0.00025 so the band median is tiny and a coloured spectrum exceeds 20 x median without a real line: the 20 x median rule as written cannot pass any run here. This looks like a detector calibration issue, not a controller result; do not use a chatter verdict from this rule until the threshold is calibrated (needs an absolute amplitude floor). K1 harsh results flag identically (81/81 windows).
- Key1 files exist only for hover_harsh s1-s3; quiet and typ (6 runs) have no key1 output, so those are unverified against key1.
- Controller fault flag (LOC rule) is not defined in the spec: not checked by K2.
- Wind/sag/weak-motor classes unknown to K2: calm limits (0.15 m, 0.10 m) were applied; all values are below them, so no verdict depends on it.
- "Peak" implemented as the band maximum per window; "one peak" > 20 x median; rms at peak = sqrt of PSD summed over +-2 bins; sustained = >=3 consecutive windows within +-10 % of the first in the streak.
- Self-test: 6 checks pass; with `--break` (ratio raised to 1e9) 4 of 6 fail and exit 1; restored (no break flag = all pass).
- Time bases differ (K1 times are about 22.3 s less than ulog time), compare by event, not by number.
