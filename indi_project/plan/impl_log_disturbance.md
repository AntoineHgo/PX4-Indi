# Implementation log: disturbance injection (gust_x, payload_add)

- Step 0: read spec, runner, scenarios, metrics, batch. Plan: bench/disturbance.py (injector), scenario keys, runner hooks, metrics.
- Step 1 (probe, container px4-indi-dist-probe): runtime system add WORKS in gz 8.15:
  `gz service -s /world/default/entity/system/add --reqtype gz.msgs.EntityPlugin_V --reptype gz.msgs.Boolean --req 'entity {id: 1} plugins {filename: "gz-sim-apply-link-wrench-system" name: "gz::sim::systems::ApplyLinkWrench"}'` -> `data: true`, topics /world/default/wrench{,/persistent,/clear} appear. No generated-world fallback needed.
- x500 mass = 2.0 (base_link) + 4 * 0.016076923 (rotor links) = 2.064308 kg; gz gravity 9.8 -> payload force 0.25*m*g = 5.057 N.
- Design: injector started early (idle), runner writes trigger file `disturbance_trigger.json` with onset in PX4 time; profile from gz clock.
- Step 2: wrote bench/disturbance.py; edited scenarios.py (gust_x, payload_add: segments settle 10 s + "dist" 28/30 s, key disturbance=...); run_scenario.py: spawns injector after start_px4 (idle), writes disturbance_trigger.json + meta["disturbance"] before the scenario loop. Old scenarios untouched (guarded by sc.get("disturbance")).
- Step 3: first flights ran but injector crashed: need 'from gz.msgs10.plugin_pb2 import Plugin' (message class not registered). Fixing; containers dist-* stopped.
- Step 4: python binding cannot build gz.msgs.Plugin (TypeError 'No message class registered' with .add() and .append(), plugin_pb2 imported). Using the CLI 'gz service' (proven in step 1) via subprocess for the system add only; wrench/clock stay in Python.
- Step 5: injector standalone test OK (gz sim -s alone, onset 0): system add true via CLI, clock is 250 Hz (4 ms steps), 4459 wrench updates over 28 s, csv correct (0.33075 N at 3 m/s, ty=0.01654 Nm). Next: full flights.
- Step 6: metrics.py: added disturbance_metrics() (peak tilt/roll/pitch dev, peak position dev horizontal(gust)/vertical(payload), recovery = first t>=t_peak with error<=0.1 m for 2 s within window). Output key 'disturbance' in metrics.json, only when run.json has 'disturbance'. Full flights (docker dist-gust_x, dist-payload_add) launched at speed 1.
- Step 7: first full flights FAILED physically: /wrench/persistent ACCUMULATES every message (re-publishing 250x/s summed the force: payload_add dropped from z=-5 to ground in 2 s, gust_x flew to 245 m, gz ODE assertion abort). DEVIATION from spec: the injector now publishes on the one-step topic /world/<w>/wrench at every clock tick (250 Hz sim time), no persistent wrench. Relaunching flights.
- Step 8: flights with the one-step wrench both OK (exit ok, no crash). Results (PID default, seed 1, speed 1):
  gust_x: peak horizontal dev 0.614 m (east, t_peak 13.2 s after onset), peak tilt 14.2 deg (pitch), recovery 15.9 s, final err 0.017 m.
  payload_add: peak vertical dev 0.351 m (sagging, 1.18 s after onset), peak tilt 0.40 deg, recovery 4.78 s, final err 0.003 m.
  ULog/gz offset = 0 s (motors react 20 ms after onset); recorded in bench/RUNNER_NOTES.md.
## Files changed
  new: bench/disturbance.py. edited: bench/scenarios.py, bench/run_scenario.py (guarded by sc.get("disturbance")), bench/metrics.py (disturbance_metrics, only if run.json has "disturbance"), bench/RUNNER_NOTES.md, plan/impl_log_disturbance.md.
  outputs (untracked): results/runs/gust_x/pid_default/seed1/, results/runs/payload_add/pid_default/seed1/.
## Reproduce (from repo root; note: run_batch.sh would name containers px4-indi-<scn>-1, so use run.sh with dist- names)
  indi_project/docker/run.sh -n dist-gust_x -t 600 -N python3 indi_project/bench/run_scenario.py --scenario gust_x --controller pid_default --seed 1 --speed 1 --out indi_project/results/runs/gust_x/pid_default/seed1
  indi_project/docker/run.sh -n dist-payload_add -t 600 -N python3 indi_project/bench/run_scenario.py --scenario payload_add --controller pid_default --seed 1 --speed 1 --out indi_project/results/runs/payload_add/pid_default/seed1
  python3 indi_project/bench/metrics.py <out>/flight.ulg
  (or: NAME_TAG=dist SCENARIOS="gust_x payload_add" SPEEDS=1 indi_project/bench/run_batch.sh -- container names px4-indi-<scn>-1-dist, no collision with *-r2)
## Not verified
  Existing scenarios not re-run after the edits (changes are guarded; py_compile OK). speed != 1 for disturbance scenarios not tested (profile is in sim time; trigger lead is 10 s sim). Force direction/magnitude on the vehicle only checked via flight response, not by reading the link wrench in gz.
