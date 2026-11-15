# determinism_s12 notes

## Run 1 FAILED (exit 1)

run.json error: RunError: climb not finished by t=34.0 s (sim t=34.01); T_OFFBOARD_S=40.0 would slip

```
RUN FAILED: RunError: climb not finished by t=34.0 s (sim t=34.01); T_OFFBOARD_S=40.0 would slip
METRICS FAILED: no scenario window (no run.json window and no offboard span in log)
```

Runs 2 and 3 not started (stop-on-failure rule). No stray det_s12* containers before run 1.

## Try 1 cause (orchestrator)
px4.log: arm denied 20.0-24.0 s by "Preflight Fail: height estimate not stable"; armed 25.16 s; climb > 8.8 s missed the 34 s deadline. Constants moved: T_ARM_S 30 s, T_OFFBOARD_S 52 s. Try-1 output moved to results/det_s12_try1/.
