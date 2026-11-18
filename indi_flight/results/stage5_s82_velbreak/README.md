# S82 outer-loop acceleration break injector (T170)

Code: `src/modules/mc_indi_pos_control/` (IndiPosInjection.{hpp,cpp,Test}, McIndiPosControl, params yaml `MC_INDI_PINJ_*`),
`msg/IndiPosStatus.msg` (a_c = u, a_c_pre_inject = c, inject = d). Analysis: `indi_flight/bench/pinj_csv.py`.

Pre-test: `pretest.params`, `run/` (flight.ulg, px4.log), `run.json`, `metrics.json`, `pinj_z.csv` (t,d,x,y), `margins.json`,
`check_window.py` (run in docker, needs pyulog). Command:
`indi_project/docker/run.sh -n s82fly -t 600 -- python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi --model quad5in --sim v2 --rate-hz 400 --seed 1 --speed 4 --params indi_flight/results/stage5_s82_velbreak/pretest.params --out indi_flight/results/stage5_s82_velbreak/run`
Result: z-axis break, PM 54.4 deg at 0.60 Hz, no phase crossing in 0.2-8 Hz. See NOTES.md for caveats.

## Orchestrator note (S82)
- Break identity: d is added at the INDI stage INPUT (a_ref = stock position-loop output). The measured L is the
  velocity/position (outer) loop with the INDI acceleration loop closed: the D-GAP "velocity-break PM" item at
  tb = 1.0 s (54.4 deg, one flight, pre-test). It is NOT the G2 INDI acceleration-loop break, which needs d at the
  stage output (thrust/collective command) and is still missing.
- Open before G2 use: tb/3 flight, window after climb (DLY >= 15 s or NP 5, drop 1st period), AX = 0 bit-identical
  flight, pinj_csv.py self-test, second key (code to brief_velbreak_s82.md), linear-model cross-check.
