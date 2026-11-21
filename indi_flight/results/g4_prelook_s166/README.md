# G4 pre-look (S166): bench/g4_metrics.py on hover_typ_s1 -- PROBE, UNKEYED, not gate evidence
Log: results/g4_vib_s156/hover_typ_s1/flight.ulg, window t0 58 .. t1 72 s (log-start time base). JSON: g4_metrics.json.
Commands (repo root, Docker, host has no scipy):
- `indi_project/docker/run.sh -n s166g4 -t 600 -- python3 indi_flight/bench/g4_metrics.py --selftest` -> PASS (50 Hz line R20/R4 and C20 within 1 %, 8 Hz line absent from R20/C20 and present in R4/C4, jittered 1 kHz times, clip fraction 0.15 exact)
- `... g4_metrics.py --break-check` (cutoff 200 Hz via function argument) -> selftest FAILS as required
- `... g4_metrics.py g4_vib_s156/hover_typ_s1/flight.ulg --t0 58 --t1 72 --json g4_prelook_s166/g4_metrics.json`
Note: a sine below 4 Hz (e.g. 1 Hz) is in the low-pass for both cutoffs, so it cannot appear in R4; the 8 Hz line tests the 4-20 Hz band.
Truth topic: NONE in this log. `esc_status.esc[i].esc_rpm` (800 Hz, timestamp; esc_status has no timestamp_sample) is the only rotor-speed
topic, and this log has SIM_GZ_ESC_FB=2 (eRPM telemetry model: one frame latency, 100 eRPM rounding, held values on drops). Truth would need
SIM_GZ_ESC_FB=1 (joint state, same topic). So R20/R4 below are a telemetry PROXY. sim_ground_truth carries no rotor speed.
Command: actuator_motors.control[0..3], 800 Hz, timestamp_sample.
Params caveat: this log used MC_INDI_POS_TB 1.0 (not the freeze params).

| metric | measured | typical limit | verdict (probe) |
|---|---|---|---|
| R20 (proxy) | 0.92 rad/s = 0.093 % hover (hover 995 rad/s) | <= 1.5 % | below, proxy |
| R4 (proxy) | 2.86 rad/s = 0.288 % | <= 4 % | below, proxy |
| C20 | 0.00152 | <= 0.006 | below |
| C4 | 0.00248 | (no limit) | n/a |
| clip fraction | 0 | 0 | ok |
Quiet SIM here (sub-limit by >5x); rerun with FB=1 and freeze params for gate evidence. 100 eRPM rounding floors the proxy near 0.1 rad/s per sample.
