# G3 subset re-fly at speed 1, INDI and PID reference (S199)

Read from `g3_done.json`, `g3_checks.json` (key 1, `rms_at_max_ratio`) and key 2 json (`max_rms_dps`) of each run; campaign
runs in `../g3_campaign_f10/run_NNN/`, classes from `../g3_campaign_f10/FAILS_S199.md`. Cells: verdict k1/k2, detector line
(axis, Hz, RMS dps) or watchdog reason.

| idx | corner / class | INDI s4 (campaign) | INDI s1 (re-fly) | PID s1 (same draw) |
|---|---|---|---|---|
| 245 | C1, LOC | ABORT height < 0.3 m at 64.70 s | ABORT height < 0.3 m at 65.05 s | ok, no LOC; k1/k2 FAIL item2 p 2.75 Hz 7.5 |
| 264 | C3, LOC | ABORT tilt > 60 deg at 60.67 s | ABORT tilt > 60 deg at 60.91 s | ok, no LOC; k1 PASS, k2 FAIL item2 r 2.5 Hz 9.7 |
| 008 | A | k1/k2 FAIL q 10.75 Hz 6.9/7.7 | k1/k2 FAIL q 10.75 Hz 7.1/8.1 | k1/k2 FAIL p 11.0 Hz 161/207 (r 8 Hz) |
| 240 | C1, class C | k1 FAIL p 2.25 Hz 13.3, k2 PASS | k1 FAIL p 2.25 Hz 8.6, k2 PASS | k1 FAIL q 3.25 Hz 5.9, k2 PASS |
| 283 | C5, A | k1/k2 FAIL q 10.75 Hz 19.1/19.0 | k1/k2 FAIL q 10.75 Hz 18.2/18.1 | PASS / PASS |
| 239 | B (LHS, largest) | k1/k2 FAIL p 2.0-2.25 Hz 51.6/53.8 | k1/k2 FAIL p 2.0-2.5 Hz 76.6/76.0 | PASS / PASS |
| 046 | D | k1 FAIL p 2.0 Hz 11.4, k2 PASS | k1 FAIL p 2.5 Hz 14.3, k2 FAIL p 2.5 Hz 31.5 | PASS / PASS |
| 039 | harness | ABORT land wall timeout | ABORT land wall timeout; k1/k2 FAIL q 2.0-2.5 Hz 16.9/21.4 | ABORT land wall timeout; PASS / PASS |

- Both INDI losses of control reproduce at speed 1 within 0.4 s of the campaign time; PID flies both draws without LOC.
- Class A (008, 283) and class B (239) lines reproduce on both keys at the same frequency. PID passes 283 and 239; on 008
  PID fails with a different, larger roll line (11 Hz, 161-207 dps), so 008 is a draw property shared with PID, 283 is not.
- 046 (class D) gets worse at speed 1 (key 2 now fails): borderline class D is not a speed-4 artefact.
- 039: both stacks hover after the land command until the wall timeout (LAND overridden by the stick re-centre), a
  harness property shared with PID.
