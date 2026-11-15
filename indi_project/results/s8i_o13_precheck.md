# O-13 pre-check of the stage-8 set O1-O7 (session 53, 2026-11-15)

pid_tuned (stock pipeline, `results/s2_tuning/pid/r1f/c05/params`), seed 1, v2 sim with vibration, speed 1, entries
flown 4 in parallel. Feasibility only, no verdict. `bench/s8i_o13_precheck.sh`.

| entry | traj rms 3D (m) | attitude rms (deg) | motor saturation | status |
|---|---|---|---|---|
| O1 lemniscate 10x5 m, 6 m/s | 0.44 | 7.9 | 0 | flyable |
| O2 circle r 5 m 8 m/s + 1.5 m vertical | 2.97 | 13.6 | 20 % | REPLACED |
| O3 O1 + gust_x | 0.40 | 6.9 | 0 | flyable |
| O4 O1 + payload_add | 0.74 | 4.7 | 8.7 % | flyable (saturation from carrying the payload through the path) |
| O5 O2 + com_shift | - | - | - | REPLACED: watchdog, height < 0.3 m at sim t 42.6 s |
| O6 vertical sine, mass x1.15 | 0.16 | 0.17 | 0 | flyable |
| O7 O1 + motor tau x2 | 0.44 | 7.9 | 0 | flyable |

Replacement (O-13: an entry pid_tuned cannot fly is replaced, not kept): the circle of O2/O5 is slowed to 6.5 m/s
(centripetal 8.45 m/s^2, about 1.4 g of total thrust, close to O1, which pid_tuned flies without saturation).
Old runs kept in `results/s8i_o13_precheck/replaced_circle_8ms/`. Re-check: `bench/s8i2_o13_circle.sh` ->
`results/s8i_o13_precheck/{o2_circle_z,o5_circle_com_shift}/pid_tuned/seed1/`, log `results/s8i2_o13_circle.log` (ends S8I2_DONE).

Re-check at 6.5 m/s (`bench/s8i2_o13_circle.sh`): O2 traj rms 1.55 m, attitude 11.8 deg, saturation 7.6 % (still
marginal, O1 is 0.44 m with no saturation); O5 crashed again by the same watchdog (height < 0.3 m at sim t 43.1 s,
same time as at 8 m/s). OPEN: the identical crash time suggests the com_shift onset or profile combined with the circle,
not the speed alone. Next: read z(t) and the motor outputs of O5 around t 40-43 s and the com_shift profile; candidates:
drop the vertical sine from the circle, slow to 5 m/s, or move com_shift to the lemniscate. Not frozen.

## Session 54: O5 diagnosed and replaced

O5 at 6.5 m/s (`replaced_circle_6p5ms/`): the com_shift step (15 % extra weight, -3.03 N, and -0.15 N m about world x)
starts with the circle. Collective thrust saturates 1.5 s after onset and the vehicle sinks into the watchdog.
Re-check at 5 m/s (`bench/s8i3_o13_circle5.sh`): O2 now flies cleanly (traj rms 3D 0.58 m, attitude 6.3 deg, no motor
saturation, motor mean 0.65), but O5 crashed again (watchdog, height < 0.3 m at sim t 50.2 s; run in
`replaced_circle_5ms/`). Cause, from the 5 m/s log: yaw. After onset the yaw torque setpoint reaches 0.5-1.0
(normalised) and yaw swings 60 deg off the setpoint. The two CW motors sit at 1.0 and the two CCW motors at about
0.62, and then roll/pitch and thrust are lost. The injector applies the offset weight torque fixed in the WORLD frame
(`bench/disturbance.py`, stated level-hover approximation). At the 15-35 deg tilts of the circle, that torque has a
body-yaw component of up to about 0.08 N m, which saturates the quad's small yaw authority. A real rigidly attached
offset mass reacts along the specific force (body z in a coordinated turn), so it adds almost no yaw torque: this is an
injector artefact, not a property of the path or of the controller.

Replacement (D-s8-oset): O5 = com_shift on the near-level vertical sine of O6 (nominal mass), where the approximation
holds: `o5_zsine_com_shift`. O2 stays the 5 m/s circle. Re-check: `bench/s8i4_o13_o5zsine.sh` ->
`o5_zsine_com_shift/pid_tuned/seed1/`, log `results/s8i4_o13_o5zsine.log` (ends S8I4_DONE).
Limitation for the report: payload_add (O4, on the lemniscate) is also a world-fixed force without the payload's
inertia. It is a force disturbance, not a true mass change in manoeuvring flight.

Re-check of O5 on the vertical sine (S8I4_DONE): flyable, traj rms 3D 0.19 m, attitude 0.75 deg, no motor saturation,
motor mean 0.74, peak roll deviation 3.1 deg at onset. Set O frozen in `bench/scenarios.md` sec. 10.
