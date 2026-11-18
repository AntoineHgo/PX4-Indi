# S85: injector-off identity flight (MC_INDI_PINJ_AX 0 with PT 1 and a full multisine configured)

Question: does the bench injector, configured but with axis 0, change the flight? (open item of S84 README.)
Runs: hover_long, quad5in, INDI, 400 Hz, seed 1, speed 4, --sched --sched-anchor. `base.params` = S84 `hf.params`
without PINJ lines (base_a, base_b); `ax0.params` = base + PINJ_AX 0, PT 1, AMP 0.12, band 1.5-10 Hz (ax0_a).
Metric: `bench/identity_check.py` (self-test `--self-test`), last 40 s of the hold event (landing excluded).

| run | z std (m) | xy std (m) | mean u | u AC rms |
|---|---|---|---|---|
| base_a | 0.0253 | 0.0356 | 0.13667 | 0.00022 |
| base_b | 0.0108 | 0.0298 | 0.13667 | 0.00022 |
| ax0_a | 0.0190 | 0.0349 | 0.13667 | 0.00021 |

Max relative difference within base (same seed): z std 57 %, xy std 16 %, u AC 0.9 %. Base vs ax0: z std 43 %,
xy std 15 %, u AC 4.1 % (1e-5 absolute). Verdict: ax0 lies inside the same-seed spread on position (the known A-30
spread dominates) and equals base on mean command; the u AC difference is 1e-5 of full scale. No evidence that the
disabled injector changes the flight. Limits: n = 2 + 1, one seed, one mode; a bit-level identity test is not possible
while same-seed runs differ (A-30). UNKEYED (single script, written by the orchestrator).
