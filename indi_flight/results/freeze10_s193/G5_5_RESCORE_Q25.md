# G5.5 re-score against the Q25 B horizontal limit (FREEZE-10, S197)

Rule (GATES.md "Owner amendments S197", D-OWNER-Q25): H_lim = max(0.5 m, tau_att x v_rms), tau_att = 0.125 s, v_rms = RMS of the
analytic reference horizontal speed on the scorer's samples. Vertical 0.3 m and offb_vel_step unchanged. Re-score only, no re-fly,
no scorer edited. Formula and constants taken from the amendment; no score used to choose anything.

Tools: `bench/g55_traj_limit.py` (v_rms, H_lim; uses `metrics.analytic_reference`, the key-1 scorer's reference; central
difference h = 1e-3 s as `traj_pva`), self-test `bench/tests/test_g55_traj_limit.py` (5 tests PASS: circle without ramp v_rms = r w,
circle with ramp against the closed-form smoothstep integral, lemniscate without ramp 4.243 m/s, zero-speed z-sine gives the 0.5 floor,
window selection), table generator `bench/g55_rescore_q25.py` (reads tabled key-1 values from `g55/*.check.txt`, key-2 values from
`g55/key2_g55.txt`, v_rms from each flight's own truth sample grid in its scorer window; key-1 and key-2 grids give the same v_rms).

## Why the values differ from the expected rough ones
The scorers' window is the whole `traj` segment, which includes the 3 s speed ramp-up and 3 s ramp-down (z-sine 2 s). The "expected"
5 m/s (o2) and 4.24 m/s (lemniscate) are cruise speeds. Over the scored window the reference speed RMS is 4.548 m/s (o2) and 3.711 m/s
(lemniscate), as the amendment's "same trajectory segments as the error RMS" requires. Consequence: o2 H_lim 0.5685 m (not about 0.62),
lemniscate rows 0.464 m of tau x v_rms, so the 0.5 m floor applies (not 0.53). Cruise-only values (5.000, 4.243) are reproduced by the
self-test without ramp. Flag for the owner: the amendment's expected numbers assume cruise speed.

## Limit table
| row | v_rms [m/s] | tau x v_rms [m] | H_lim [m] |
|---|---|---|---|
| o1_lemniscate | 3.711 | 0.464 | 0.500 (floor) |
| o2_circle_z | 4.548 | 0.5685 | 0.5685 |
| o3_lemniscate_gust | 3.711 | 0.464 | 0.500 (floor) |
| o4_lemniscate_payload | 3.711 | 0.464 | 0.500 (floor) |
| o5_zsine_com_shift | 0.000 | 0.000 | 0.500 (floor) |
| o6_zsine_mass | 0.000 | 0.000 | 0.500 (floor) |
| o7_lemniscate_tau2 | 3.711 | 0.464 | 0.500 (floor) |

Per-flight grids give identical v_rms to 4 digits within a row.

## INDI FREEZE-10 per row x seed (H in m; margin = H_lim - H; last four columns are the unchanged vertical 0.3 m limit)
| row | seed | key1 H | key2 H | v_rms | H_lim | key1 | key2 | key1 margin | key2 margin | V key1 | V key2 | V key1 | V key2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| o1_lemniscate | 1 | 0.4487 | 0.4475 | 3.711 | 0.5000 | PASS | PASS | +0.0513 | +0.0525 | 0.0975 | 0.0973 | PASS | PASS |
| o1_lemniscate | 2 | 0.4512 | 0.4515 | 3.711 | 0.5000 | PASS | PASS | +0.0488 | +0.0485 | 0.0673 | 0.0673 | PASS | PASS |
| o1_lemniscate | 3 | 0.4441 | 0.4438 | 3.711 | 0.5000 | PASS | PASS | +0.0559 | +0.0562 | 0.0415 | 0.0416 | PASS | PASS |
| o2_circle_z | 1 | 0.5027 | 0.5027 | 4.548 | 0.5685 | PASS | PASS | +0.0658 | +0.0658 | 0.0229 | 0.0229 | PASS | PASS |
| o2_circle_z | 2 | 0.4911 | 0.4913 | 4.548 | 0.5685 | PASS | PASS | +0.0774 | +0.0772 | 0.0819 | 0.0818 | PASS | PASS |
| o2_circle_z | 3 | 0.4959 | 0.4955 | 4.548 | 0.5685 | PASS | PASS | +0.0726 | +0.0730 | 0.0328 | 0.0329 | PASS | PASS |
| o3_lemniscate_gust | 1 | 0.4571 | 0.4574 | 3.711 | 0.5000 | PASS | PASS | +0.0429 | +0.0426 | 0.0545 | 0.0545 | PASS | PASS |
| o3_lemniscate_gust | 2 | 0.4561 | 0.4571 | 3.711 | 0.5000 | PASS | PASS | +0.0439 | +0.0429 | 0.0743 | 0.0744 | PASS | PASS |
| o3_lemniscate_gust | 3 | 0.4504 | 0.4509 | 3.711 | 0.5000 | PASS | PASS | +0.0496 | +0.0491 | 0.1026 | 0.1026 | PASS | PASS |
| o4_lemniscate_payload | 1 | 0.4215 | 0.4218 | 3.711 | 0.5000 | PASS | PASS | +0.0785 | +0.0782 | 0.0653 | 0.0652 | PASS | PASS |
| o4_lemniscate_payload | 2 | 0.4099 | 0.4100 | 3.711 | 0.5000 | PASS | PASS | +0.0901 | +0.0900 | 0.0660 | 0.0660 | PASS | PASS |
| o4_lemniscate_payload | 3 | 0.4115 | 0.4108 | 3.711 | 0.5000 | PASS | PASS | +0.0885 | +0.0892 | 0.0333 | 0.0332 | PASS | PASS |
| o5_zsine_com_shift | 1 | 0.0441 | 0.0441 | 0.000 | 0.5000 | PASS | PASS | +0.4559 | +0.4559 | 0.0439 | 0.0439 | PASS | PASS |
| o5_zsine_com_shift | 2 | 0.0411 | 0.0411 | 0.000 | 0.5000 | PASS | PASS | +0.4589 | +0.4589 | 0.0261 | 0.0261 | PASS | PASS |
| o5_zsine_com_shift | 3 | 0.0344 | 0.0344 | 0.000 | 0.5000 | PASS | PASS | +0.4656 | +0.4656 | 0.0253 | 0.0253 | PASS | PASS |
| o6_zsine_mass | 1 | 0.0513 | 0.0513 | 0.000 | 0.5000 | PASS | PASS | +0.4487 | +0.4487 | 0.0269 | 0.0269 | PASS | PASS |
| o6_zsine_mass | 2 | 0.0299 | 0.0299 | 0.000 | 0.5000 | PASS | PASS | +0.4701 | +0.4701 | 0.0328 | 0.0329 | PASS | PASS |
| o6_zsine_mass | 3 | 0.0432 | 0.0431 | 0.000 | 0.5000 | PASS | PASS | +0.4568 | +0.4569 | 0.0478 | 0.0479 | PASS | PASS |
| o7_lemniscate_tau2 | 1 | 0.4444 | 0.4451 | 3.711 | 0.5000 | PASS | PASS | +0.0556 | +0.0549 | 0.0956 | 0.0957 | PASS | PASS |
| o7_lemniscate_tau2 | 2 | 0.4314 | 0.4317 | 3.711 | 0.5000 | PASS | PASS | +0.0686 | +0.0683 | 0.0575 | 0.0575 | PASS | PASS |
| o7_lemniscate_tau2 | 3 | 0.4484 | 0.4481 | 3.711 | 0.5000 | PASS | PASS | +0.0516 | +0.0519 | 0.0364 | 0.0365 | PASS | PASS |

## PID references (G5.5 protocol, stock pid_default, same limit)
| flight | H (key1 scorer) | v_rms | H_lim | verdict | V | V verdict |
|---|---|---|---|---|---|---|
| freeze10_s193/g55_pid_ref/o2_circle_z_s1 | 1.1569 | 4.548 | 0.5685 | FAIL | 0.0893 | PASS |
| freeze10_s193/g55_pid_ref/o2_circle_z_s2 | 1.1444 | 4.548 | 0.5685 | FAIL | 0.0419 | PASS |
| freeze10_s193/g55_pid_ref/o2_circle_z_s3 | 1.1457 | 4.548 | 0.5685 | FAIL | 0.0526 | PASS |
| g5_freeze_s157/o1_lemniscate_s1_pid | 0.7851 | 3.711 | 0.5000 | FAIL | 0.0884 | PASS |
| g5_g55_s139/pid_ref/o1_lemniscate_s1 | 1.0434 | 3.711 | 0.5000 | FAIL | 0.0853 | PASS |

PID rows use the same flight-grid v_rms and H_lim; key-1 scorer (`g55_check.py`) H, no INDI-status validity applied (PID has no
`indi_pos_status`; same convention as `g55_pid_ref/README.md`). Key 2 not re-run on PID (key 1 and key 2 differ by <= 0.001 m on the o2 PID rows).
PID references available for G5.5 o-rows: o2_circle_z s1-s3 (freeze10_s193/g55_pid_ref), o1_lemniscate s1 only (g5_freeze_s157 and
g5_g55_s139, older firmware). None exist for o3-o7. G3-protocol PID lemniscate runs (g3_ladder_s116, g3_pid_ref_s187, g3_pretest_s187) are
a different test (disturbance draws) and are not scored here.

## Verdict
- G5.5 horizontal, INDI FREEZE-10, 21/21 o-row cells PASS key 1 and 21/21 PASS key 2. Vertical 21/21 PASS both keys. offb_vel_step 3/3 PASS (unchanged).
- Overall G5.5 (24 rows): key 1 PASS 24/24, key 2 PASS 24/24 under the Q25 B limit (was 23/24, o2 s1 H 0.5027 m).
- Worst INDI margin: o1 +0.049, o2 +0.066, o3 +0.043 (key 2 +0.0426), o4 +0.079, o5 +0.456, o6 +0.449, o7 +0.052 m. Smallest cell: o3 s1 key 2.
- PID against the same limit: o2 1.14-1.16 m vs 0.5685 FAIL (3/3); o1 s1 0.785 (S157) and 1.043 (S139) vs 0.500 FAIL.
