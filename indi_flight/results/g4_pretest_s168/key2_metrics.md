# G4 metrics, key 2 (indi_flight/bench/g4_metrics_key2.py), written before opening key 1

Truth = esc_status instance 1 (SIM_GZ_ESC_FB=2). Rotor and command both 800 Hz. Windows in s since ulog start.

| run | window | R20 rad/s (%) | R4 rad/s (%) | C20 | C4 | clip |
|---|---|---|---|---|---|---|
| g4_truth_s168/hover_typ_s1 | 58-72 | 0.7700 (0.0773) | 2.6027 (0.2614) | 0.001450 | 0.002341 | 0 |
| hoverL_harsh_s1 | 36.993-91.993 | 0.3350 (0.0336) | 0.8428 (0.0844) | 0.000495 | 0.000976 | 0 |
| hoverL_quiet_s1 | 37.100-92.100 | 0.0302 (0.0030) | 0.0853 (0.0085) | 0.000029 | 0.000055 | 0 |
| lemn_typ_s1 (traj event) | 34.887-52.105 | 0.3198 (0.0310) | 3.8139 (0.3695) | 0.001080 | 0.002738 | 0 |

Selftest: PASS (fs 2000/1000 Hz synthetic; at 400 Hz the linear interpolation attenuates 50 Hz by ~5 %, a property of the spec, irrelevant at 800 Hz only partly: 50 Hz at 800 Hz is 16 samples/period, ~1-2 % loss).
Hold window for hover_long = [start+5, start+60].

## Comparison with key 1 (g4_truth_s168/g4_metrics_inst1.json, hover_typ_s1 58-72 only)

| metric | key2 | key1 | diff |
|---|---|---|---|
| R20 rad/s | 0.7700 | 0.769995 | <0.01 % |
| R20 % | 0.0773 | 0.07743 | 0.2 % (denominator: key1 hover_speed 994.43, key2 window mean) |
| R4 rad/s | 2.6027 | 2.602679 | <0.01 % |
| R4 % | 0.2614 | 0.26173 | 0.1 % |
| C20 | 0.001450 | 0.0014498 | <0.02 % |
| C4 | 0.002341 | 0.0023404 | <0.03 % |
| clip | 0 | 0 | equal |

All within 2 %. Only this run has a key 1 number; the other three runs are not cross-checked.
