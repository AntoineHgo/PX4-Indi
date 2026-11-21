# F4 probe (S180): inner INDI setpoint lead time constant 0.01 -> 0.03 s
Change: src/lib/indi_rate_control/indi_rate_control.hpp:279 kSetpointLeadTc = 0.03f (nothing else). Working tree only, NOT committed.
Unit (build/px4_sitl_test, docker f4t, unit_tests.txt): indi_rate_control_test 70/70, IndiRateFeedforwardGate 6/6, IndiRateSetpointWatchdog 6/6. No test asserts the old constant.
Build px4_sitl_default OK (build.log). Flight cruise_typ_s1 (seed 1, traj_lemniscate, params_xyp12, typical noise) rc=0, container f4fly (first attempt failed on zsh word splitting before launch, rerun with bash).
Scoring: score.sh / reconcile_f2.py copied from F2 with paths changed; RAW into this folder (tracked raw untouched). Outputs score_out.txt, reconcile_out.txt.
## Results (window 36-53.5 s) vs F2
89 Hz line: still the dominant spectral peak (88.5-89.25 Hz) but per-motor window RMS (+-2 Hz) max m0 4.02e-4, m1 3.88e-4, m2 4.16e-4, m3 3.92e-4 (F2 5.2-7.7e-4). 0 of 14 windows flagged on all motors, both keys. Track() max 4.2e-4 (88.8 Hz, t 38.6-42.6, m0).
33.5 Hz: absent as a flagged line (nearest 33.75 Hz at t=41 s, 2.2e-4 m0, 1.5e-4 m1, 2.4e-4 m2, below threshold).
G4: R20 0.022 % (F2 0.030), C20 6.6e-4 (F2 1.14e-3), R4 0.321 (F2 0.388), chatter NO both keys (key1 fixed/old, key2), item2 PASS, item1 PASS, item3 FAIL (known window artefact).
Take-off / pre-traj / ramp / cruise / hold: 0 flagged windows. AUTO_LAND (66-71 s): 20.3 Hz 2.1e-3 (F2 1.9e-3), outside lemniscate window, only flagged span.
## Verdict vs criterion: PASS. No line at 33.5 or 88-90 Hz with RMS >= 5e-4 on either key, no new line >= 5e-4 in the window. 89 Hz reduced, not eliminated (3-4e-4, 0.6-0.8x of F2 threshold margin).
