# G3 campaign f10 (300 runs): failure characterisation (S199)

Analysis only, no flight. Helper scripts in `analysis_s199/` (`extract.py`, `disagree.py`, `corr.py`, `cls.py`, `joint.py`,
`item3.py`, `abort.py`, `mkmd.py`). Sources: `SCORES.tsv`, `run_NNN/g3_checks.json` (key 1), `key2/run_NNN.json` (key 2),
`g3_draw.json`, `px4.log`, `g3_done.json`, `flight.ulg` (aborts only). Time stamps `tNN` = start of the detector streak in
seconds after airborne start (hold of the 3 s steady window is at about t 42-45; land command at about t 48-50).

## Headline
- Items 1: 0 LOC among the 297 scored runs. 3 unscored aborts (039, 245, 264, section 4).
- Item 2 failures, scored runs: key 1 73, key 2 45, union 79, both 39, key 1 only 34, key 2 only 6. Item 3: 15 on both keys.
- Item 3 denominator: 15 misses of 297 scored runs = 94.95 % pass, under the 95 % line by 0.05 point (one run). With the
  3 aborts counted as invalid the quota is 282.15 of 297. Items 4-6 are not part of this analysis. UNVERIFIED how the
  orchestrator counts aborts.
- The 79 item-2 failures are four different things (class column below):
  - A (8 runs, both keys): a real 10.75 / 11.5 Hz pitch (q) line, 14-16 windows long, 7-19 dps.
  - B (37 runs, key 2 flags them; 31 of them both keys): a 2.0-2.5 Hz line, rates up to 290 dps in the C1 corner. The
    large ones are real (245 diverges on it, 2.0 Hz pitch, rms 23 -> 252 dps in 16 s).
  - C (25 runs, key 1 only): a 2.0-2.5 Hz line only at t 46-48, the landing/touchdown windows, which key 2 skips by design.
  - D (9 runs, key 1 only): borderline 2.0 Hz lines in flight (3 windows, the minimum), key 2 does not flag them.

## 1. Item 2: per run (union of keys, scored runs)
Columns: run, scoring mode (pos/att), class A-D, agreement, key 1 signal (`axis@peak frequency, max line RMS in flagged
windows, streak start`), key 2 signal. Both detectors: truth p,q,r, 4 s Hann windows, 1 s step, band 2-40 Hz, peak > 20 x
band median AND line RMS > 5 dps, flagged in >= 3 consecutive windows within +-10 % of the first (the frequency grid is 0.25 Hz,
so for a 2.0 Hz line the tolerance admits only the 2.0 Hz bin). Position limit cycle (0.3 m p2p, 3 x 10 s) never triggered on
either key. p/q/r ratio is >1e4 in every run including passing ones (clean sim, tiny band median), so the 20 x ratio never
decides; the 5 dps RMS line and the 3-window rule do.

| run | mode | cls | agree | key 1 | key 2 |
|---|---|---|---|---|---|
| 003 | pos | B | both | q@2.25Hz 13dps t47 | q@2Hz 12dps t23 |
| 008 | pos | A | both | q@10.75Hz 7dps t24 | q@10.75Hz 8dps t25 |
| 020 | pos | C | k1 only | q@2.0Hz 12dps t46 | - |
| 024 | pos | B | both | p@2.0Hz 30dps t34; q@2.0Hz 23dps t26 | p@2Hz 33dps t35; q@2Hz 25dps t27 |
| 025 | pos | A | both | q@10.75Hz 10dps t23 | q@10.75Hz 10dps t24 |
| 029 | pos | B | k2 only | - | p@2Hz 12dps t21; q@2.25Hz 12dps t21 |
| 031 | att | C | k1 only | p@2.0Hz 11dps t47 | - |
| 042 | pos | A | both | q@10.75Hz 11dps t24 | q@10.75Hz 11dps t25 |
| 045 | pos | C | k1 only | p@2.5Hz 9dps t47 | - |
| 046 | pos | D | k1 only | p@2.0/2.25Hz 15dps t33 | - |
| 052 | att | C | k1 only | p@2.0Hz 9dps t47 | - |
| 054 | pos | B | both | q@2.0Hz 18dps t34 | p@2Hz 11dps t35; q@2Hz 18dps t35 |
| 059 | pos | B | k2 only | - | p@2Hz 10dps t35 |
| 062 | pos | A | both | q@10.75Hz 10dps t25 | q@10.75Hz 10dps t25 |
| 067 | pos | D | k1 only | q@2.0Hz 15dps t34 | - |
| 077 | pos | B | both | p@2.0Hz 16dps t21; q@2.0Hz 26dps t22 | p@2Hz 16dps t22; q@2Hz 27dps t23 |
| 086 | pos | C | k1 only | q@2.0Hz 11dps t46 | - |
| 090 | pos | C | k1 only | p@2.0Hz 14dps t46 | - |
| 094 | pos | B | k2 only | - | p@2Hz 14dps t21 |
| 098 | att | C | k1 only | p@2.5Hz 14dps t46 | - |
| 107 | pos | B | k2 only | - | q@2Hz 13dps t35 |
| 109 | att | B | k2 only | - | p@3.5Hz 13dps t24; q@3.25Hz 17dps t24 |
| 112 | pos | A | both | q@10.75Hz 8dps t24 | q@10.75Hz 7dps t25 |
| 115 | pos | D | k1 only | q@2.0Hz 9dps t26 | - |
| 120 | pos | C | k1 only | q@2.5Hz 15dps t47 | - |
| 137 | pos | B | both | q@2.0Hz 10dps t28 | q@2Hz 10dps t28 |
| 139 | att | C | k1 only | q@2.5Hz 11dps t46 | - |
| 147 | att | C | k1 only | p@2.5Hz 11dps t48 | - |
| 153 | pos | C | k1 only | q@2.5Hz 13dps t47 | - |
| 160 | att | C | k1 only | p@2.5Hz 13dps t47; q@2.5Hz 12dps t47 | - |
| 167 | att | B | both | p@2.0Hz 14dps t47 | p@2Hz 11dps t24 |
| 174 | pos | B | k2 only | - | q@2Hz 7dps t31 |
| 175 | att | C | k1 only | q@2.0Hz 12dps t47 | - |
| 182 | pos | C | k1 only | q@2.0Hz 13dps t47 | - |
| 189 | att | C | k1 only | p@2.5Hz 12dps t47 | - |
| 195 | pos | C | k1 only | p@2.5Hz 12dps t47 | - |
| 200 | pos | C | k1 only | p@2.5Hz 13dps t47 | - |
| 204 | pos | D | k1 only | q@2.0Hz 11dps t33 | - |
| 205 | pos | B | both | p@2.5Hz 12dps t47; q@2.25Hz 14dps t26 | q@2.25Hz 15dps t27 |
| 206 | pos | B | both | q@2.0/2.25Hz 15dps t26 | q@2Hz 14dps t27 |
| 209 | att | C | k1 only | p@2.5Hz 17dps t47 | - |
| 220 | pos | A | both | q@10.75Hz 8dps t24 | q@10.75Hz 8dps t25 |
| 221 | pos | C | k1 only | q@2.5Hz 14dps t47 | - |
| 225 | pos | C | k1 only | p@2.5Hz 8dps t47 | - |
| 230 | att | C | k1 only | p@2.5Hz 14dps t47 | - |
| 239 | pos | B | both | p@2.0/2.25Hz 52dps t27; q@2.5Hz 16dps t46 | p@2.25Hz 54dps t25 |
| 240 | att | C | k1 only | p@2.25Hz 20dps t47 | - |
| 241 | pos | B | both | p@2.0/2.25Hz 227dps t0; q@2.0/2.25/3.0Hz 221dps t0; r@2.0/2.5/2.75Hz 123dps t25 | p@2.25Hz 223dps t7; q@3Hz 210dps t26; r@3Hz 126dps t26 |
| 242 | pos | B | both | p@2.25Hz 39dps t0 | q@2Hz 15dps t26 |
| 243 | pos | B | both | p@2.0Hz 293dps t0; q@2.0Hz 71dps t0; r@2.25/4.0Hz 47dps t3 | p@2Hz 294dps t7; q@2Hz 71dps t7; r@4Hz 48dps t7 |
| 244 | pos | C | k1 only | p@2.5Hz 14dps t46; q@2.5Hz 16dps t46 | - |
| 246 | pos | D | k1 only | p@2.0Hz 12dps t29; q@2.25Hz 23dps t46 | - |
| 247 | pos | B | both | p@2.0/2.25Hz 47dps t21; q@2.0/2.25Hz 245dps t21; r@4.25Hz 11dps t46 | p@2Hz 28dps t22; q@2Hz 191dps t26 |
| 248 | pos | B | both | q@2.0/2.25Hz 17dps t34 | q@2Hz 12dps t27 |
| 249 | pos | B | both | p@2.0/2.25Hz 38dps t0; q@2.0/2.25Hz 49dps t1; r@2.25Hz 6dps t27 | p@2Hz 39dps t23; q@2Hz 25dps t23; r@2.25Hz 6dps t28 |
| 262 | pos | B | both | q@2.0Hz 42dps t20 | q@2Hz 46dps t21; r@2.5Hz 18dps t21 |
| 265 | pos | D | k1 only | p@2.0Hz 14dps t33 | - |
| 269 | pos | B | both | p@2.0Hz 66dps t20; q@2.0Hz 32dps t20; r@2.5Hz 19dps t21 | p@2Hz 72dps t21; q@2Hz 34dps t21 |
| 270 | pos | B | both | q@2.0Hz 7dps t30 | q@2Hz 6dps t30 |
| 272 | pos | B | both | q@2.0Hz 17dps t27 | p@2Hz 13dps t35; q@2Hz 19dps t28 |
| 274 | pos | B | both | q@2.0Hz 8dps t30 | q@2Hz 8dps t31 |
| 276 | pos | B | both | q@2.0Hz 9dps t31 | q@2Hz 9dps t32 |
| 277 | pos | B | both | q@2.0Hz 7dps t30 | q@2Hz 7dps t31 |
| 278 | pos | B | both | q@2.0/2.5Hz 13dps t21 | p@2Hz 24dps t34 |
| 280 | pos | D | k1 only | p@2.0Hz 10dps t21 | - |
| 283 | pos | A | both | q@10.75Hz 19dps t24 | q@10.75Hz 19dps t25 |
| 284 | pos | D | k1 only | q@2.0Hz 11dps t23 | - |
| 285 | pos | A | both | q@11.5Hz 7dps t24 | q@11.5Hz 7dps t25 |
| 286 | pos | C | k1 only | q@2.0Hz 10dps t47 | - |
| 290 | pos | C | k1 only | q@2.5Hz 19dps t47 | - |
| 291 | pos | B | both | p@2.0Hz 25dps t46; q@2.0Hz 15dps t21 | q@2Hz 15dps t22 |
| 292 | pos | B | both | p@2.0/2.25/2.5Hz 15dps t6; q@2.0/2.25Hz 41dps t0; r@2.0Hz 13dps t21 | p@2.25Hz 16dps t7; q@2.25Hz 43dps t7; r@2Hz 14dps t21 |
| 293 | pos | B | both | p@2.0/2.25Hz 48dps t1; q@2.0Hz 20dps t22; r@2.0Hz 9dps t21 | p@2Hz 49dps t21; q@2Hz 17dps t23; r@2Hz 9dps t22 |
| 294 | pos | B | both | p@2.0Hz 19dps t22; q@2.0Hz 26dps t22 | q@2Hz 26dps t23 |
| 295 | pos | B | both | p@2.0Hz 20dps t46; q@2.0Hz 18dps t46 | q@2Hz 20dps t21 |
| 296 | pos | B | both | p@2.0/2.25Hz 43dps t1; q@2.0/2.5Hz 18dps t31 | p@2.25Hz 44dps t9; q@2.25Hz 15dps t26 |
| 297 | pos | B | both | q@2.0/2.25Hz 21dps t23 | q@2Hz 21dps t24 |
| 298 | pos | B | both | p@2.0/3.0Hz 21dps t21; q@2.0Hz 19dps t46 | p@2Hz 20dps t22 |
| 299 | pos | D | k1 only | p@2.0Hz 19dps t22 | - |

Axis counts: q appears in most lines (pitch is the weak axis), p next; r only in the C1/C6 corners and a few LHS runs
(292, 293, 262, 269, 247, 249, 241, 243, 205...). Frequency is 2.0-2.5 Hz in all but class A (10.75 / 11.5 Hz) and 109
(3.25-3.5 Hz).

### Agreement key 1 / key 2
| | runs |
|---|---|
| both fail item 2 | 39 (A 8 incl. 112 with a 3-window key 1 line, B 31) |
| key 1 only | 34 (C 25, D 9) |
| key 2 only | 6 (029, 059, 094, 107, 109, 174, all class B, all in-flight 2.0 Hz lines) |

"Both" is per run, not per axis: 003, 054, 109, 242, 262, 272, 278 etc. are flagged on different axes or at different
times by the two keys.

### Why the keys differ (code: `bench/g3_checks.py` line_detector/evaluate, `bench/g3_checks_key2.py` psd_windows/sustained/osc_rates)
1. Nav-change skip (explains class C, 25 runs, and the 3 D runs 280, 284, 299). Key 2 always skips every window that
   overlaps the 3 s after a vehicle_status.nav_state change (Q15 A; 21 windows skipped per run: takeoff, offboard switch,
   land). Key 1 runs it only with `--skip-nav-change` (G4 option); `g3_score.sh` calls it without, so `skipped_windows`
   is 0 in every key 1 file. Every class C line starts at t 46-48 = the land command / touchdown (t_land - airborne start
   is 47.8-49.7 s in all 25 runs) and lies inside key 2's skipped windows. Verified by overlapping each key 1 line against
   key 2's `skipped_windows_t` (script `disagree.py`, output `dis.txt`).
2. Window grid and span (explains D in-flight, 46/67/115/204/246/265, and key 2 only 6). Key 1 grids the airborne span with
   `g4_metrics.uniform` starting at the airborne sample, key 2 interpolates onto `np.arange` from the first finite airborne
   sample; the airborne spans differ (key 2 `h > mean(h[:800]) + 0.3`, key 1 its own `up` mask) by a fraction of a second, so
   the 4 s / 1 s windows sit at slightly different phases. A line at 2.0 Hz (the band's lowest bin) in exactly 3 windows
   flips with this. Strict `>= 5` (key 1) against `> 5` (key 2) is a negligible second cause. UNVERIFIED: I did not re-run
   both detectors on the ulg to confirm that the phase shift alone flips these 12 runs.
3. 003 (key 1 t47 only in the landing windows, key 2 t23 in flight) is the same two causes in one run.
Consequence: at 2.0 Hz both keys are at the detector's resolution edge; this is the same borderline family already seen in
`speed_check/README.md` (draw 09, 03). The 10.75 Hz lines (A) are agreed by both keys with the same frequency and RMS within
10 %, so they are not detector artefacts.

## 2. Item-2 failure against the drawn factors
Base: LHS 0-239 (239 scored; 46 fail item 2 on either key, key 1 40, key 2 21), corners 240-299 (58 scored, 33 fail). `corr.py`
prints every factor; the few that matter:

| split (LHS) | n | key 2 fails (A+B) | key 1 fails | note |
|---|---|---|---|---|
| total loop delay >= 7.5 ms (draw 0-10 ms) | 80 | 13 (16 %) | A 6, C 10, D 2 | vs 159: key 2 8 (5 %), A 0, C 11, D 2 |
| delay >= 8.75 ms and tau_up <= 0.55 (all 300 indices) | 23 | A 8 | | all 8 class A runs sit here |
| class A signature: delay >= 8.75, tau_up <= 0.55, controller/plant G1 pitch e <= 0.91 | 9 (all indices) | 7 A | | 7 of 9 runs with all three (8, 25, 42, 62, 220, 283, 285); 112 is class A at e just above 0.91 |
| mass < 0.9 | 79 | 12 (15 %) | C 16 | vs 160 (mass >= 0.9): key 2 9 (6 %), C 5; mass drives class C (16 of 21 LHS C runs) |
| gust peak >= 6 m/s | 86 | 13 (15 %) | | vs 8/153 (5 %) |
| tau_down / tau_up above median | 119 | 10-12 | 26-27 | key 2 no effect; key 1 22-23 % vs 11-12 % (mostly class C) |
| GNSS latency (EKF delay >= 200 ms) | 73 | 3 (4 %) | | opposite direction: low delay (< 120 ms) 7/54 |
| GNSS mismatch matched vs mismatched +-50 ms | 119 / 120 | 9 / 12 (key 2) | 18 / 22 | no effect |
| vibration x mult above / below median | 119 / 120 | 9 / 12 | 19 / 21 | no effect |
| steady wind above / below median | | 10 / 11 | 17 / 23 | no effect |
| eRPM frozen / loss / dropout, thrust sag, weak motor (LHS) | | 11/47, 3/48, 7/95, 5/65, 6/51 | | frozen is the only one clearly above the base for key 2 (11/47 = 23 % vs 10/192 = 5 %); small n, not examined further |

| corner | pins (g3_sample.py) | n scored | item 2 either key | classes |
|---|---|---|---|---|
| C1 240-249 | G1 +20 % all axes, slow motors tau 3, max delay | 9 (+245 abort) | 9 | B 241 242 243 247 248 249; C 240 244; D 246 |
| C2 250-259 | G1 -20 %, heavy mass 1.3, sag off, inertia high | 10 | 0 | clean |
| C3 260-269 | saturation (thrust 2.0 x hover), gust peak 9, mass 1.3 | 9 (+264 abort) | 3 | B 262 269; D 265 |
| C4 270-279 | GNSS latency max, matched, steady wind 5, G1 +20 % | 10 | 6 | B 270 272 274 276 277 278 |
| C5 280-289 | vibration max, frozen, dropout, fast motors | 10 | 5 | A 283 285; C 286; D 280 284 |
| C6 290-299 | weak motor, slow motors tau 3, max delay | 10 | 10 | B 291-298; C 290; D 299 |

Reading: the factor that explains class A and B is the pair loop delay (max in C1, C6; >= 8.75 ms in A) with the motor time constant
(slow tau for B: C1, C6; LHS delay >= 7.5 and tau_down >= 1.5 gives 5 B in 35; fast tau for A: LHS delay >= 7.5 and tau_up <= 0.7
gives 6 A in 34). Low mass goes with class C (key 1 only, touchdown windows; mechanism not investigated). GNSS latency, GNSS mismatch,
vibration and wind do NOT explain it (C4 fails come with the G1 +20 % pin and the max GNSS latency, but LHS GNSS latency shows the
opposite trend). Mode: LHS draws are position (lemniscate) and attitude; attitude-mode runs (stabilized) fail item 2 through class C
(31, 52, 98, 139, 147, 160, 175, 189, 209, 230, 240) or class B (109 key 2 only, 167 both); none is in class A.
Caveat: factors are correlated by design in the corners (several pins per corner), and the LHS n is small (21 key 2 failures), so the
split rates are indications, not fitted effects. No regression was run.

## 3. Item 3 misses (15, both keys agree on every number)
Spread rule (README Verdict + `speed_check/README.md`): the speed-1 same-seed spread is expressed as |diff| / threshold,
max over 20 draws: horizontal RMS 0.16, altitude mean 0.98 (read as 1.0), roll/pitch mean 0.26. I read "within spread" as
(value - limit) / limit <= spread. Roll/pitch is not gated in position mode (all 15 are position), so no roll/pitch miss exists
(roll/pitch means are only reported, e.g. 276 -2.07 / +2.65 deg, 272 +2.01 deg, not gated).

| run | sub-item | value | limit | over limit | within spread? | notes |
|---|---|---|---|---|---|---|
| 002 | horizontal | 0.310 m | 0.30 | 3.4 % | yes (16 %) | sag on; the pre-test 02 miss (0.318 m there) |
| 133 | horizontal | 0.314 m | 0.30 | 4.7 % | yes | alt 0.094 of 0.10 too |
| 174 | horizontal | 0.3014 m | 0.30 | 0.5 % | yes | also item 2 key 2 |
| 262 | horizontal | 0.327 m | 0.30 | 9.1 % | yes | saturation + weak motor (C3), also item 2 |
| 271 | horizontal | 0.311 m | 0.30 | 3.6 % | yes | C4 |
| 272 | horizontal | 0.311 m | 0.30 | 3.8 % | yes | C4, sag on, roll mean 2.0 deg |
| 274 | horizontal | 0.3010 m | 0.30 | 0.3 % | yes | C4 |
| 276 | horizontal | 0.334 m | 0.30 | 11.4 % | yes | C4, weak motor |
| 277 | horizontal | 0.3145 m | 0.30 | 4.8 % | yes | C4 |
| 278 | horizontal | 0.338 m | 0.30 | 12.7 % | yes | C4, weak motor, closest to the 16 % edge |
| 279 | horizontal | 0.30001 m | 0.30 | 0.003 % | yes | C4 |
| 023 | altitude | -0.110 m | 0.10 | 10.3 % | yes (100 %) | |
| 042 | altitude | +0.110 m | 0.10 | 10.2 % | yes | also item 2 class A |
| 200 | altitude | -0.108 m | 0.10 | 7.8 % | yes | also item 2 key 1 (class C) |
| 243 | altitude | -0.150 m | 0.10 | 50 % | yes | C1, also item 2 (294 dps p line); also horizontal 0.192 (ok) |

All 15 are within spread, none is outside it. Seven of the 11 horizontal misses are C4 (271, 272, 274, 276-279; C4 has steady wind 5 m/s), 262 is C3, 002, 133, 174 are LHS.
Run 262 is the only run of the campaign with the key 2 column 5 (G4 chatter, not G3) False.

## 4. The three aborts
| run | corner/mode | abort | what happened | class | drawn factors |
|---|---|---|---|---|---|
| 039 | LHS, stabilized stick flight (zmulti altitude pilot), speed 4 | wall timeout (150 s) in phase `land`, sim t 681.8 | The land command at sim 83.3 s was overridden: px4.log has `Landing at current position` followed immediately by `Pilot took over using sticks`. `sticks.csv`: the altitude pilot's throttle stick was at raw z 409 (throttle_applied -0.18) and the runner returned it to the centre (z 504, then 500) at the land command, which the commander treats as a pilot override and leaves LAND. The vehicle then hovered for 600 s sim: last 0.7 s of the ulg (the only part kept; the first 1 GiB file was rotated away, `Log file size limit reached, rotating`) shows z -4.93 m (5 m up), tilt 0.2 deg, rates ~1 dps, motors 0.096. | harness artefact (land command overridden by the stick re-centring); no loss of control seen. The flight data before the rotation is not in the kept ulg and `metrics.py` failed, so the run is unscorable. UNVERIFIED that the stick re-centre is the trigger (consistent with the logs, not isolated). | g1_err r/p/y 0.96/1.19/0.81, GNSS delay 157 ms mismatch 0, mass 0.70, tau_up/down 2.46/2.71, delay 2.5 ms, vib x2.53, wind 0, no sat/sag/weak, frozen eRPM motor 1 at +4.6 s, eRPM dropout 13 % |
| 245 | C1 (position, lemniscate) | flight watchdog height < 0.3 m (sim t 64.7), cycle 41 s | Real loss of control. Take-off at ulg t 11, hover at 5 m from t 17 (before the trajectory anchor at t 35). A pitch-rate (q) oscillation at 2.0 Hz grows from t 17: rms 23 dps (17-21 s), 68, 160, 252 dps (29-33 s), p and r stay at 1-2 dps; tilt 28 deg at t 30, 68 deg at t 40, then the vehicle falls to 0.25 m. Growth factor about x3 per 4 s: a linear instability at the 2.0 Hz line that all C1 runs show (241 p 223 dps, 243 p 294 dps). | real LOC (item 1), the divergent end of the C1 family | g1_err 1.2 all axes, GNSS delay 138 ms mismatch 0, mass 1.09, tau_up/down 3.0/2.6, delay 10 ms (max), vib x1.12, wind 1.1 gust 6.8, sag to 0.72 (ramp 10 s from anchor), eRPM loss motor 3 for 2 s at anchor +3.6 s |
| 264 | C3 (position, lemniscate) | flight watchdog tilt > 60 deg for 0.5 s (sim t 60.7), cycle 30 s | Real loss of control, abrupt. Quiet hover at 5 m (rates 2-4 dps) until the trajectory anchor (ulg t 35.4); at the anchor the C3 hooks fire (`SIM_GZ_THR_SC` to 0.351 = saturation, 2.0 x hover on mass 1.3, and motor 3 thrust scaled to 0.709). Rates jump to 64 dps at t 36 (tilt 18 deg) and to 90 dps / 57 deg at t 37, then > 60 deg. 7 s of the run, no growing oscillation: a thrust/torque authority loss (one motor at 71 % on top of the 2 x hover thrust cap, wind 3.4 steady, gust to 9 m/s, delay 10 ms, tau_up 0.5). | real LOC under the corner's combined fault; can the plant keep authority at all? UNVERIFIED (no PID or authority bound computed here). The 8 other C3 flights passed item 1 (260-269 except 264), so it is the corner's extreme, not the whole corner. | g1_err 0.80/1.04/1.17, GNSS delay 181 ms mismatch -47 ms, mass 1.30, tau 0.5/0.60, delay 10 ms, vib x4.67, wind 3.4 gust 9.0, saturation on, weak motor 3 at 0.709 |

## 5. Re-fly list (speed 1, same index)
Rule (README Verdict): every item 1-2 failure on either key (79), the 3 aborts, every item-3 miss within spread (15, all
within). Union 87 indices (79 item 2 + 3 aborts + 5 item-3-only misses 002, 023, 133, 271, 279). Item 1: no LOC among scored runs, so none.
Note the pre-test draws 03 and 08 (PID reference failed them: 03 key 1 FAIL / key 2 PASS, 08 both; per
`g3_pretest_q24_s197/README.md`, not re-checked here) fail on both keys here (03 class B, 08 class A).
Suggested priority if the 87 flights are too many (orchestrator decides): all of A (8), the C1/C3/C6 corner failures, and 039/245/264 first.

REFLY: 2,3,8,20,23,24,25,29,31,39,42,45,46,52,54,59,62,67,77,86,90,94,98,107,109,112,115,120,133,137,139,147,153,160,167,174,175,182,189,195,200,204,205,206,209,220,221,225,230,239,240,241,242,243,244,245,246,247,248,249,262,264,265,269,270,271,272,274,276,277,278,279,280,283,284,285,286,290,291,292,293,294,295,296,297,298,299
