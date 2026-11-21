# S157 stage-6 freeze re-fly of G5 (D-FREEZE-6), typical noise profile

Firmware 23acbdef67 (frozen) + gz_bridge vibration hook 0f56d56bf1/56ebc4e009 (SITL rebuilt S156, checked newer than source).
Plant: quad5in, matched GNSS `--gps-dly 110 --gnss-delay 110`, G4 typical profile `--vib-acc 10 --vib-gyr 0
--imu-noise-scale 4.0` (D-NOISE-PROF; run.json `vib`, `imu_noise_scale` confirm it was applied). Serial, one stream.
Fly one: `bash indi_flight/results/g5_freeze_s157/fly.sh <scenario> <seed> [runner args]`; batch (resumable):
`bash indi_flight/results/g5_freeze_s157/batch.sh` (aborts if a run's params_applied MC_INDI_ID_OK != 1).

## Set-up fault found by the pre-test (fixed, no threshold change)
`bench/params/quad5in_indi_defaults.params` sets `MC_INDI_ID_OK 0`; the runner overlay is `setdefault("MC_INDI_ID_OK", "1")`
(run_scenario.py:1007), so a file that sets 0 wins and the flight runs at 0.5 x K (pre-identification). D-FREEZE-6 assumed
the overlay applied. Fix: `params.params` here = the defaults file with `MC_INDI_ID_OK 1` (only diff). The pre-test flight
is kept as `auto_tour_s1_idok0` (extra data at the firmware-default gain state, not a freeze-set result).

## Pre-test: auto_tour seed 1 at ID_OK 0 (checker bench/auto_smoke_check.py, keyed S135)
ramp max step 7.5 % hover, edge step 4.0 % (<= 10 %), dip 0.000 m (<= 0.3), take-off overshoot -0.10 m / bounce 0.20 m,
touchdown vz 0.721 m/s (<= 0.8), tilt 0.31 deg, re-lift 0.050 m, land vz 0.699, contact->disarm 2.69 s, RTL height
err 0.033 m: all PASS. indi_rate_status and indi_pos_status present (stack valid). Flies, logs, checker runs.

## Freeze set results
(batch in progress: G5.1 stick_steps acro/stab, G5.2 stick_pos_steps altctl/posctl, G5.3 mission + G5.4 auto_tour,
auto_land10; seeds 1-3. Remaining rows G5.5-G5.11 and the firmware-default cells are next.)
