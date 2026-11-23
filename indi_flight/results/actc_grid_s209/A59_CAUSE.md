# A-59 cause: SIM_GZ_ERPM_LAT "no effect" (code reading only, nothing run)

## Most likely cause (high confidence, not flown)
The ident script fits the wrong esc_status instance. indi_flight/bench/ident_actc.py:275
`inst = max(d.multi_id ...)` selects instance 1. With SIM_GZ_ESC_FB=2, gz_bridge publishes a second
esc_status (`_esc_truth_pub`, GZMixingInterfaceESC.hpp:188) whose esc_rpm is the TRUE rotor rpm,
undelayed, no eRPM model (GZMixingInterfaceESC.cpp:296-302). The delay line only feeds instance 0
(`_esc_status_pub`, .cpp:261-265, 311). So the fit measures cmd -> true rotor, which ERPM_LAT cannot change.
The 1.73 vs 1.82 ms difference is noise.

## Evidence
- Delay line itself is correct: write at idx, read (idx+9-lat)%9, idx advances once per callback (.cpp:264-265, 285);
  lat clamped 0..8 (.hpp:82). It adds `lat` frames before the existing 1-frame reply. No off-by-one.
- The ACT hook (--dly-act) works because it delays the command to Gazebo, so the truth rotor moves late too.
- INDI modules use `uORB::Subscription _esc_status_sub{ORB_ID(esc_status)}` (McIndiRateControl.hpp:134), i.e.
  instance 0, the delayed one. In flight the latency is probably applied; only the measurement is blind. (unverified)

## Secondary cause (verified by reading, matters for g3_run.py)
SIM_GZ_ERPM_LAT is read once in the constructor (.hpp:66); updateParams() (.hpp:86-) does not re-read it.
g3_run.py:143 sets it via a --params file applied after boot, so the G3 "telemetry latency" factor was
probably never applied in the earlier 300 runs. PRETEST.md already says this. The scenario sim_params path does apply it at boot.

## Smallest fix
1. ident_actc.py:275: use instance 0 (`inst = 0`, or the instance whose esc_rpm differs from truth). Keep truth for a separate check.
2. Optional: re-read SIM_GZ_ERPM_LAT (clamped) in updateParams(), so params-file runs work. Or move g3_run.py to sim_params.

## One-flight check
Re-fly t1_a3d_d0f3_s1 (lat 3) and re-fit the existing log with inst 0: expect delay ~ +3.75 ms vs t1_a1_d0f0
(re-fit that log with inst 0 too). Cheap pre-check, no flight: fit instance 0 and instance 1 of the same ulg;
they should differ by about (1+lat) frames. Unverified: that the log has esc_status multi_id 1 as the max.
