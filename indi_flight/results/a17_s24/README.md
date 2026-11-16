# A17: Commander publish phase (mod 10000 us), g16_sched_s24 hover runs

Script: `indi_flight/bench/a17_commander_phase.py`. Per-run JSON: `hover_r{1..5}.json` in this folder.
Topics checked: vehicle_status, failsafe_flags, actuator_armed, vehicle_control_mode.
`commander_state` is absent from all five logs and was not computed.
Histogram bins are 1250 us wide (8 bins over 10000 us).
Every observed phase is an exact multiple of 1250 us, so the bins resolve the phase fully.

| run | dominant phase, vehicle_status (share) | failsafe_flags | actuator_armed | vehicle_control_mode | armed mod 10000 | offboard mod 10000 |
|---|---|---|---|---|---|---|
| hover_r1 | 2500 us (100 %) | 2500 (100 %) | 2500 (100 %) | 2500 (100 %) | 2500 | 2500 |
| hover_r2 | 3750 us (100 %) | 3750 (100 %) | 3750 (100 %) | 3750 (100 %) | 3750 | 3750 |
| hover_r3 | 8750 us (60.2 %) | 8750 (59.3 %) | 8750 (60.2 %) | 8750 (60.2 %) | 7500 | 8750 |
| hover_r4 | 6250 us (100 %) | 6250 (100 %) | 6250 (100 %) | 6250 (100 %) | 6250 | 6250 |
| hover_r5 | 6250 us (100 %) | 6250 (100 %) | 6250 (100 %) | 6250 (100 %) | 6250 | 6250 |

hover_r3 is the only run with more than one phase. Its vehicle_status messages sit at 0 us (15), 7500 us (53) and 8750 us (103). The min/max over each bin gives these exact values.

## Verdict on the hypothesis

- Within a run, one phase dominates above 80 % in hover_r1, r2, r4 and r5. In hover_r3 the dominant phase holds only about 60 %, so the claim fails there.
- Where the phase is fixed, armed and offboard both sit on it (r1, r2, r4, r5). In hover_r3 armed (7500) is a minor phase, and offboard (8750) matches the dominant one at 60 %.
- Across runs the fixed phase differs: 2500, 3750 and 6250 us (r4 and r5 match). hover_r3 is not fixed at all.
- Not tested: the 10 ms sleep period itself. The check only looks at timestamp mod 10000, so it shows a fixed phase but not the loop period.
