# Disturbance injection for gz_x500 (T6 gust_x, T7 payload_add): implementation spec

Session 10, 2026-11-14. Decision record: `DECISIONS.md` D-dist.

## Goal

Add the first two simulator-extension scenarios of `bench/scenarios.md`
(T6 `gust_x`, T7 `payload_add`) to the runner, applied identically to every
controller, deterministic in sim time, and logged so that `metrics.py` can
align the disturbance with the ULog.

## Mechanism (decided)

- Gazebo Harmonic 8.15 in `px4-indi-sim` ships
  `gz-sim-apply-link-wrench-system` and the Python bindings
  `gz.transport13` / `gz.msgs10` (checked session 10).
- Do NOT edit `Tools/simulation/gz/worlds/*.sdf` or the x500 models: a
  tuning batch is running against them. Load the ApplyLinkWrench system at
  runtime, preferably through the world's `/world/<world>/entity/system/add`
  service on the world entity, after gz starts and before PX4 arms. If that
  service does not work in 8.15, fall back to a generated world file under
  `indi_project/bench/worlds/` (copy of `default.sdf` + the plugin), selected
  only for disturbance scenarios.
- A small injector (new file `bench/disturbance.py`) runs inside the same
  container as the runner, subscribes to the world clock
  (`/world/<world>/clock` or `/clock`), and publishes a persistent wrench on
  the x500 `base_link` (topic `/world/<world>/wrench/persistent`, msg
  `gz.msgs.EntityWrench`; clear with `/world/<world>/wrench/clear`).
  The profile is a function of **sim time**, so it is independent of the
  speed factor. It updates the wrench at >= 100 Hz of sim time and writes a
  CSV `disturbance.csv` (sim_time_s, fx, fy, fz, tx, ty, tz) next to the
  ULog. Profile time 0 is the moment the scenario's disturbance segment
  starts; the runner tells the injector that moment (e.g. via an argument
  giving the absolute sim time, or by starting it at that point).
- Verify once that ULog timestamps and gz sim time share an origin or find
  the offset, and record it in `bench/RUNNER_NOTES.md`; `metrics.py` needs
  the disturbance onset in ULog time.

## Profiles

Both in position mode, hovering at the runner's hover setpoint, with the
disturbance starting after a 10 s settle and the run lasting until 15 s
after the disturbance ends.

- **T6 `gust_x`**: wind modelled as a quasi-steady drag force along +x
  `F = c * v_w * |v_w|`, with `c = 0.5 * rho * Cd * A`, rho = 1.225,
  Cd*A = 0.06 m^2 (x500 frame, frontal area order 0.05-0.1 m^2; record this
  as an assumption). Vehicle velocity is neglected (position-held hover).
  Wind speed: ramp 0 -> 3 m/s over 2 s, hold 10 s, then 1-cosine gust of
  +6 m/s amplitude over 1 s (total 9 m/s at the peak), then hold 3 m/s for
  15 s. The force acts at a centre of pressure 0.05 m above the CoM, so the
  wrench also carries the torque `r x F` (pitch torque for +x force).
  Constants live at the top of `disturbance.py` as named values.
- **T7 `payload_add`**: step of a downward force `0.25 * m * g` on
  base_link (m = x500 total mass read from the model SDF, record the value),
  held until the end. Limitation to record: adds weight, not inertial mass
  or inertia.

## Integration

- `scenarios.py`: add `gust_x` and `payload_add` entries; a new optional key
  (e.g. `disturbance="gust_x"`) tells the runner to start the injector.
  Existing scenarios must behave byte-for-byte as before.
- `run_scenario.py`: start/stop the injector, put `disturbance.csv` in the
  run output dir, record onset sim time in the run's metadata.
- `metrics.py`: for disturbance scenarios, compute peak attitude deviation
  (deg), peak position deviation (m, horizontal for T6, vertical for T7),
  and recovery time (time from onset until the deviation stays within 10 %
  of its peak... use: position error back within 0.1 m and staying there
  for 2 s; record the definition). Keep existing metrics unchanged.
- Run one PID-default flight of each new scenario, seed 1, speed 1
  (position scenario), with a container name tag that does not collide with
  the running tuning batch (`px4-indi-*-c??-*-r2`). Check the CSV, that the
  vehicle visibly reacts (position deviation > 0.1 m for T6), and that it
  does not crash.

## Out of scope here

Motor loss (T8, via per-channel `SIM_GZ_EC_MAX` at runtime), model
variants (T9, H5), trajectories (T5, H1), held-out variants H2/H3 (they
reuse this injector with other profiles). Next tasks.
