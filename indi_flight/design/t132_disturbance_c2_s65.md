# T132 - N1 C2: disturbance.py sized from the flown airframe (S65)

Files: `indi_flight/bench/disturbance.py` (edited), `indi_flight/bench/tests/test_disturbance_sizing.py` (new).
Not run in gz (no simulation, no firmware, no commit). Timing is unchanged: profiles are still functions of gz sim time
at every clock message; only the amplitudes now come from an `Airframe`.

## What changed
- New `Airframe` (mass = sum of all link masses of the base SDF, base_link inertia diagonal, CdA, CoP height) loaded by
  `load_airframe()`. New options `--airframe x500|quad5in` (default derived from `--model`: `quad5in*` -> quad5in, else x500)
  and `--sdf PATH`. Default `--model x500_0` -> x500 -> same numbers as before. The runner already passes `--model <model>_0`,
  so quad5in runs pick quad5in with no runner change.
- SDFs: quad5in `indi_flight/sim/models/quad5in_base/model.sdf` (quad5in/model.sdf only includes it), x500
  `Tools/simulation/gz/models/x500_base/model.sdf` (readable locally). If an SDF is not mounted in the container,
  `load_airframe` falls back to embedded constants equal to the SDFs (checked by the test) and logs the source in
  `disturbance.log` (line "airframe ...") - check that line in each run.
- Profile functions now take `(t, af)`.

## Per profile
| profile | old (x500-sized) | new rule | new quad5in value (0.610 kg, W = 5.98 N) |
|---|---|---|---|
| payload_add | Fz = -0.25 * 2.0643 kg * 9.8 = -5.06 N | -0.25 * m_flown * g (same fraction) | -1.49 N |
| com_shift | Fz = -0.15 * m * g = -3.03 N, Ty = 0.05 * Fz | -0.15 * m_flown * g, lever 0.05 m kept (see note) | -0.90 N, Tx = -0.045 N m |
| gust_x | 0.5*rho*0.06*v|v|, peak 9 m/s = 2.98 N (14.7 % W), torque via CoP 0.05 m | same drag law with airframe CdA and CoP | CdA 0.012 -> 0.595 N (10.0 % W), CoP 0.02 m |
| gust_diag | same law, peak 3.55 N (17.5 % W) | same | 0.71 N (11.9 % W) |
| torque_steps | 0.10/0.10/0.03 N m (already quad5in-sized) | quad5in numbers are the reference; scaled by I_axis / I_quad5in | unchanged: 0.10/0.10/0.03 N m = 97.8/89.1/15.4 rad/s^2; x500 would get 2.12/1.93/0.62 N m |
| wind | (the speed profile shared by gust_x, 3 m/s ramp + 6 m/s gust) | unchanged | - |

Note com_shift: the 5 cm lever is kept in metres (not scaled by frame size). 5 cm is ~23 % of a 0.22 m diagonal vs 10 % of
the x500, so the torque/inertia ratio is larger on the 5-inch: Tx/Ixx = 0.045/1.022e-3 = 44 rad/s^2, vs x500
0.05 * 3.03 N = 0.15 N m / 0.0217 = 7 rad/s^2. Owner decision: a size-scaled lever (about 0.02 m) is one constant
(`SHIFT_Y`); kept at 0.05 m here to preserve the physical meaning of the profile.

## Assumptions (UNVERIFIED)
1. UNVERIFIED: quad5in CdA = 0.012 m^2 and CoP height 0.02 m. Derived by scaling the x500 assumption by frame-size ratio
   (0.22/0.51)^2 and checked against the 0.01-0.02 m^2 order usually quoted for 5-inch freestyle quads. No measurement, no
   citable source, and the sim model has no drag plugin of its own to compare with. The gust is 10-12 % of weight, similar to
   the x500 (15-18 %), which is the intent.
2. UNVERIFIED: x500 CdA 0.06 / CoP 0.05 stay as the original spec assumption (plan/disturbance_spec.md).
3. Mass is the sum of link masses in the SDF (quad5in 0.566 + 4*0.011 = 0.610 kg), inertia is base_link only (rotor links
   ignored, as the SDF gives them separate inertials); torque_steps scale uses that base_link inertia.
4. UNVERIFIED: the world-frame wrench = body-frame approximation (vehicle near level, spawn yaw) is as before.
5. torque_steps on x500 changes vs before (it was never sized for x500); no earlier x500 result used it (N1 A text: none on quad5in either).

## Test output (`python3 indi_flight/bench/tests/test_disturbance_sizing.py`)
```
x500 mass 2.0643 kg, quad5in mass 0.6100 kg
payload_add  x500     peak Fz/weight = 0.250
payload_add  quad5in  peak Fz/weight = 0.250
com_shift    x500     peak Fz/weight = 0.150
com_shift    quad5in  peak Fz/weight = 0.150
gust_x       x500     peak |Fxy| = 2.977 N = 0.147 weight
gust_x       quad5in  peak |Fxy| = 0.595 N = 0.100 weight
gust_diag    x500     peak |Fxy| = 3.549 N = 0.175 weight
gust_diag    quad5in  peak |Fxy| = 0.710 N = 0.119 weight
torque_steps axis 0: quad5in 0.1000 N m (97.8 rad/s2), x500 2.1200 N m
torque_steps axis 1: quad5in 0.1000 N m (89.1 rad/s2), x500 1.9311 N m
torque_steps axis 2: quad5in 0.0300 N m (15.4 rad/s2), x500 0.6173 N m
OK
```
Checks: quad5in mass in 0.5-0.7 kg; x500 mass == old constant; x500 force numbers == old formula; payload/com_shift
force/weight equal on both; fallback constants == SDFs; quad5in torque_steps unchanged; gust ratios inside 5-25 % of weight.

## G1.5 check needed (pre-test flight on quad5in, injector running, speed factor as the gate uses)
In every case: `disturbance.log` shows the quad5in airframe line (mass 0.610), `disturbance.csv` sim_time_s stamps are gz
sim time, start at the trigger onset, step size matches the table, and returns to 0 at profile end.
- payload_add: Fz = -1.49 N from onset to +30 s in the csv; the vehicle sags/needs ~+25 % hover thrust (logged motor/thrust
  command up ~25 %), altitude error visible then recovered, no saturation.
- com_shift: Fz = -0.90 N and Tx = -0.045 N m; a steady roll/pitch torque disturbance visible in the rate/attitude residual,
  attitude hold error bounded; confirm torque sign/axis against the body axes (lever is along world +y).
- gust_x: Fx follows 0 -> 0.10 N (3 m/s) -> 0.595 N peak at onset+13 s (1-cos 1 s); vehicle position/velocity responds in +x,
  confirm the push is ~10 % of weight (tilt angle ~6 deg equivalent), not the old 17 % x500 value.
- gust_diag: |F| peak 0.71 N, direction 120 deg at peak; position excursion in the direction of the gust vector.
- torque_steps: 0.10/0.10/0.03 N m steps at 0-2, 4-6, 8-10 s; rate response about roll/pitch/yaw in the same sign; yaw step
  not dominated by saturation.
- Common: confirm the wrench actually moves quad5in_0 (not x500_0) - first look at the sign of the response (N1 A: earlier
  runs applied nothing), and that CdA = 0.012 gives a visible, not negligible, effect.
