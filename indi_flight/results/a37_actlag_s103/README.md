# A-37 closing test (S103): SIM_GZ_DLY_ACT applied lag in flight

## Command
`results/a37_actlag_s103/fly.sh` (repo root): build px4_sitl_default at a9e5066a55 (release-age windows, 4000 releases
each, printed to px4.log), then hover_long, indi_m3a, seed 1, speed 4, quad5in, 800 Hz, sim v2, `--dly-imu 0` and
`--dly-act 5` (d5) / `--dly-act 10` (d10). Both exit 0. Read: `grep 'DLY_ACT window\|rmed' d{5,10}/px4.log`.

## Result (raw px4.log, read by the orchestrator)
| run | windows fully after arming | age min | age mean | age max | skipped / window |
|---|---|---|---|---|---|
| d5 | 19 | 5000 us | 5000-5003 us | 6250 us | 88-229 (2-6 %) |
| d10 | 19 | 10000 us | 10000-10001 us | 10000-11250 us | 72-152 (2-4 %) |

- Applied lag after arming = requested + [0, 1.25 ms) (one 800 Hz output period), mean within 0.04 ms of requested.
  Closing criterion "5 +-1.25 ms" met for d5, and also for d10.
- Before arming: first release 50 ms, a window max 200 ms: sparse mixer calls while disarmed (benign, motors stopped).
- Releases per window 4000 in ~5.14 s sim plus ~110 skipped = ~800 calls/s: the output calls keep the 800 Hz rate,
  but ~3 % arrive one period late, so two entries become due at once and the older one is skipped (latest wins).
  Release instants equal output-call instants, so the plant sees the same call timing as without the delay line,
  shifted by d. The criterion "zero drops after arming" was wrong: it tested the output-call jitter of the SITL
  lockstep, not the delay line. INFERRED, not measured: the same jitter exists at d0 (bypass path has no counter).

## Verdict
A-37 closed: DLY_ACT usable in G3 with lag = d + [0, 1.25 ms). Instrument change a9e5066a55 is logging-only and was
read by the orchestrator only (no second key; the hook itself was keyed in K102).
