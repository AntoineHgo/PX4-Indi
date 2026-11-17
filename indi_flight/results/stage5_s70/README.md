# S70 stage 5 slice 2, part 1: position-mode thrust-gap experiment (pre-test, seed 1, speed 4, sequential)

No firmware touched, no rebuild (existing build/px4_sitl_default). All flights through `indi_project/docker/run.sh`, one at a time.

## Files
- `bench/scenarios.py`: added `s5_gap085` (position, settle 15 / up 5 / hold 40, motor_fault at "up", motors [0,1,2,3], scale 0.85) and `s5_loss08` (same, motor 2 at 0.8). The runner applied motor_fault on position-mode runs without change (run.json `motor_fault.event_us/event_done_us`, `events` has "up").
- `gap.params` = S60 hover_fix params + `CA_R_W_MAX 2700` (runner renames it to MC_INDI_W_MAX, run_scenario.py:680; 2700 = model maxRotVelocity in sim/models/quad5in/model.sdf). `--sim v2` (ESC feedback eRPM) used everywhere.
- `stock.params` = gap.params without `MC_INDI_POS_EN` (INDI rate loop, stock mc_pos_control).
- `stock_htoff.params` = stock + `HTE_HT_ERR_INIT 0`, `HTE_HT_NOISE 0.0001`; `stock_htoff_noi.params` = that + `MPC_Z_VEL_I_ACC 0`; `gap_htoff.params` = gap + the two HTE lines.
  `MPC_USE_HTE` DOES NOT EXIST in this build (runner: "Parameter MPC_USE_HTE not found"); mc_hover_thrust_estimator is always started (rc.mc_apps:48).
  HTE "off" is approximated by freezing the EKF (init variance 0, minimum process noise); estimate moves 0.137 -> 0.140 only (logged, see table).
- `bench/s5_gap_check.py <run dir>` (writes `gap_check.json` in the run dir) and `bench/tests/test_s5_gap_check.py` (synthetic known answer, passes).
- Run dirs: `hover_gap`, `gap085_indi`, `gap085_stock`, `gap085_stock_htoff`, `gap085_stock_htoff_noi`, `gap085_indi_htoff`, `loss08_indi`; each has `run/` and `stdout.txt` (empty on success).

## Commands
Flight (NAME SCENARIO PARAMS; scratch helper, equivalent to):
`indi_project/docker/run.sh -n s70NAME -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario SCENARIO --controller indi_s70 --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/stage5_s70/PARAMS --out indi_flight/results/stage5_s70/NAME/run`
Gate: `python3 indi_flight/bench/pretest_gate.py indi_flight/results/stage5_s70/hover_gap/run/flight.ulg indi_flight/results/stage5_s70/hover_gap/gate.md`
Check: `python3 indi_flight/bench/s5_gap_check.py indi_flight/results/stage5_s70/<name>/run`; test: `python3 indi_flight/bench/tests/test_s5_gap_check.py`.

## (i) hover regression, gap.params
Gate PASS (rate RMS 0.0037/0.0029/0.0005, pin 0, achieved 1.0). mc_indi_pos_control ran; stage cond 0x7f at flight (bit 0x20 = telemetry/measured thrust set, absent in S60's 0x5f), 0x3f/0x7f/0x7e/0x3e during later phases (bits 0 and 6 toggle, not analysed; UNVERIFIED meaning of bit 6 and of the 0x3e/0x7e dips).

## Z error (truth z minus hold z, positive = below; event = "up" segment start, ~70.9 s)
Prediction (1-0.85)*g/(1.0*4.0) = 0.368 m (MPC_Z_P 1.0, MPC_Z_VEL_P_ACC 4.0 read from the log).
| run | z err [ev+10,ev+20] mean/std | last 10 s mean/std | max abs dev | HTE est event->end | thrust before->after |
|---|---|---|---|---|---|
| (ii) INDI pos, HTE on (gap.params) | 0.330 / 0.016 | 0.306 / 0.008 | 0.372 | 0.137 -> 0.161 | 0.1367 -> 0.1608 |
| (ii-b) INDI pos, HTE frozen | 0.381 / 0.010 | 0.372 / 0.017 | 0.412 | 0.137 -> 0.140 | 0.1367 -> 0.1608 |
| (iii) stock mc_pos_control, HTE on | -0.006 / 0.016 | -0.010 / 0.014 | 0.195 | 0.137 -> 0.161 | 0.1366 -> 0.1608 |
| (iv) stock, HTE frozen (integrator on) | 0.057 / 0.013 | 0.057 / 0.012 | 0.273 | 0.137 -> 0.140 | 0.1366 -> 0.1608 |
| (iv-b) stock, HTE frozen, MPC_Z_VEL_I_ACC 0 | 0.397 / 0.019 | 0.372 / 0.008 | 0.420 | 0.137 -> 0.140 | 0.1366 -> 0.1608 |
| (v) s5_loss08 INDI pos, HTE on | 0.194 / 0.012 | 0.189 / 0.006 | 0.216 | 0.137 -> 0.145 | 0.1367 -> 0.1452 |

## Findings
- The scenario does create the gap: (iv-b) stock with HTE frozen and no z velocity integrator sags 0.372 m, matching the 0.368 m prediction. The plain (iv) setup (HTE frozen only) shows 0.057 m, NOT the prediction, because the stock z velocity-loop integrator (MPC_Z_VEL_I_ACC) absorbs the gap. The stock reference therefore needs HTE and the integrator off to show the P-only sag; with HTE on it shows ~0 (iii).
- The INDI outer loop does NOT remove the standing z error: 0.31 m (HTE on, still decaying slowly, 0.330 -> 0.306) and 0.372 m (HTE frozen), equal to the P-only stock sag. Per the plan, this means the thrust gap is carried by the ht/G scaling and decision A11 (remedy) is needed. The INDI chain behaves like stock with integrator off, with only the HTE partially absorbing (0.31 m with HTE on vs stock+HTE+integrator ~0).
- Collective thrust rises to 0.1608 (=0.1367/0.85) in every run, so the sag is the position-error P term, not a thrust shortfall.
- (v) single motor 0.8: 0.19 m standing (plan guessed ~0.12). The checker's printed "prediction" for loss08 (0.49 m) is wrong (uses the single-motor scale as total scale); the real total loss is 0.05, P-only prediction ~0.12 m; HTE on here, so not comparable.
- `indi_pos_status` is not in the log (optional topic, not logged by the default profile), so mean_u / mean_u_valid are not reported; telemetry validity is taken from stage cond bit 0x20 in the log messages (stdout of checker prints them).

## UNVERIFIED
- Single seed, single flight each (determinism spread of G1.6/A-32 not applied; differences of ~0.02 m are within it, the 0.3-0.4 m INDI/stock gaps are not).
- HTE freeze is an approximation (estimate drifted +0.003); MPC_USE_HTE named in the S69 plan/note does not exist.
- Meaning of stage cond bits 0x20/0x40 inferred from the message text; INDI chain's own use of an integrator not checked in code.
- Thrust scale s=0.85 realized in the plant (gz plugin) only checked through the thrust ratio 1/0.85 observed in the setpoint.

## Orchestrator note (S70)
- `s5_gap_check.py` prediction fixed after the runs: the collective scale is now the mean over rotors
  (`_collective_scale`; one motor at 0.8 gives 0.95, prediction 0.12 m). The 0.49 m printed for `loss08_indi`
  above is the old, wrong value; the measured 0.19 m is unaffected.
- `MPC_USE_HTE` does not exist in this build (S69 plan note wrong); HTE frozen via HTE_HT_ERR_INIT/HTE_HT_NOISE.
- Decision: D-GAP (DECISIONS.md), proposed, review pending.
- Second key (T153, haiku, blind, `second_key.md`): last-10 s dz 0.304 / -0.008 / 0.371 / 0.188 m vs this table
  0.306 / -0.010 / 0.372 / 0.189 (gap085_indi, stock, stock_htoff_noi, loss08_indi): agree within 0.006 m. It found
  run.json event times offset from ulog time by -0.79..-0.96 s (anchored on arm and offboard edges); the [ev+10, ev+20]
  window differs by up to 0.006 m, consistent with s5_gap_check not applying that offset. Harmless for 10 s windows;
  check before the checker scores a transient (S71).
