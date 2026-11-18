# T207 (S99): G1.5 check of SIM_GZ_SEED and SIM_GZ_IMU_NSC

Firmware fdcc54ed63, runner 9d48cea369. Two `hover` flights, `--sim v2 --erpm-drop 0.1`:
F1 `--sim-seed 1 --imu-noise-scale 3`, F2 `--sim-seed 2 --imu-noise-scale 1`. Log of the task:
`design/t207_seed_noise_hooks_log.md`; author script `an.py`; independent second key `key_k99.md` (own code).

| check | author (an.py) | second key (K99) | verdict |
|---|---|---|---|
| eRPM drop fraction per motor | 0.102-0.105 | 0.101-0.106 | PASS |
| drop pattern differs F1 vs F2 | yes | yes | PASS |
| gyro white sigma F2 (SDF 8.73e-4 rad/s) | 8.7-8.8e-4 | ~8.7e-4 | PASS |
| gyro sigma ratio F1/F2 (expect 3) | 3.0 all axes | ~3.0, two estimators | PASS |
| accel sigma ratio | not measured | not measurable: sensor_accel logged at ~1 Hz | UNVERIFIED |

Open before G4 uses the accel noise: fly one pair with a full-rate accel topic in the logger profile.
Not re-run: seed 0 determinism with scale > 1 (seed 0 keeps the old fixed dropout seed by construction).
The two keys index drop events from different sample origins; both find differing sequences.
