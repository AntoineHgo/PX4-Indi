# S103 G5 pre-test: thrust gap 0.85 in manual POSCTL (neutral sticks)

Command: `results/g5_posctl_s103/fly.sh` (repo root). Scenario `s5_gap085_posctl` = copy of `s5_gap085_altctl`
(bench/scenarios.py), flown with `--stick-mode posctl`, controller indi_s98, quad5in, seed 1, speed 4, sim v2,
`gap.params` copied from results/stage5_s98. Scope note: design/posctl_gap_scope_s103.md. Flight exit 0.
Check: `bench/s5_gap_check.py run` -> gap_check.out (truth z against run.json hold_pos_ned).

| flight | z err [ev+10,ev+20] mean/std | last 10 s | max abs dev | stage |
|---|---|---|---|---|
| POSCTL (this) | -0.082 / 0.016 m | -0.092 / 0.003 m | 0.112 m | 0x7f from 34 s, mean_u valid 1.0 |
| ALTCTL (S98 B, reference) | 0.035 / 0.014 m | 0.036 / 0.011 m | 0.203 m | 0x7f |

Predicted with the PID structure (S70 formula): 0.37 m. The gap is mostly removed, but a standing -0.09 m (vehicle
above the hold point, NED) remains and does not decay over the last 10 s. UNVERIFIED: nav_state = POSCTL (not checked
in the ulog); whether POSCTL re-latched its altitude setpoint after the dip (the check uses the run.json hold point,
not the logged setpoint). pretest_gate not run (its window includes the fault, S98 note). Open as A-38.

## A-38 closing test (S104)

`python3 a38_check.py run/flight.ulg 70.82 97.5 > a38_check.out` (event 70.82 s, POSCTL until LAND at 98.0 s).

| window | z_sp | truth - sp | est - sp | truth - est |
|---|---|---|---|---|
| [ev-20, ev-1] before gap | -4.906 (constant) | -0.059 | +0.017 | -0.076 |
| [ev+10, 97.5] after gap | -4.906 (constant) | -0.072 | 0.000 | -0.072 |
| last 10 s | -4.906 | -0.073 | -0.001 | -0.072 |

The setpoint was not re-latched. The INDI z-path removes the 0.85 thrust gap against its own estimate
(est - sp = 0.000 m; predicted gap of a loop without integral action: 0.37 m). The standing truth error is the
estimator's vertical offset (truth - est = -0.076 m before the event, -0.072 m after), not a control gap. The
gap_check figure of -0.09 m used the run.json hold reference, which includes the same offset. Per lesson 3,
tracking error versus truth and estimator error are reported separately in G5.
