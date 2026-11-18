# G3 runner (S110): bench/g3_run.py

`build_run(draw, base_params_path, out_dir)` is pure and returns `argv`, `params` (overrides), `merged_params`, `applied`, `not_applied`,
`notes`. It raises if any factor (every key of `draw["factors"]`, plus `mode` and `g4_typical_noise`) is in neither dict or in both.
CLI: `g3_run.py --seed S --n N --base-params FILE --out-root DIR [--dry-run] [--start K] [--timeout-s T]`. Per run it writes
`g3_draw.json` (draw + build + command), `g3_params.txt` (base merged with overrides, passed as `--params`), `g3_stdout.txt`;
`g3_done.json` is the finished marker (written only on return code 0; failure/timeout writes `g3_failed.json` and is retried on resume).
No analysis, no pass/fail.

## Factor -> mechanism

| factor | status | mechanism |
|---|---|---|
| mode | applied | position -> `--scenario o1_lemniscate --sched`; stabilized/acro -> `--scenario stick_zsine_o6 --stick-mode M` |
| g1_ctrl_mult (also g1_err, g1_ratio aliases) | applied | params `MC_INDI_G1_R/P/Y` = base value x k (k = e / I_scale); not_applied if the base file lacks the nominal |
| tau_scale, tau_asym, mass_scale, inertia_scale | applied | `--model-variant tau=,tau_down=,mass=,ixx=,iyy=,izz=` (hooks.model_variant); a key equal to 1.0 is omitted, flag omitted if all nominal |
| loop_delay | applied | `--dly-act`, `--dly-imu` (integer ms 0..10; the 0.625-step draw is rounded to nearest ms, recorded in `notes`) |
| tel_latency | applied | param `SIM_GZ_ERPM_LAT` (needs `--sim v2`, set) |
| tel_dropout | applied | `--erpm-drop P` when on |
| vibration | applied | `--vib-acc`, `--vib-gyr` |
| gnss | applied | `--gps-dly latency_ms`, `--gnss-delay ekf_delay_ms` (omitted when None) |
| thrust_sag, saturation, weak_motor | not_applied when on | timed hook; run_scenario.py has no CLI argument (scenario keys `thrust_sag` / `motor_fault` only). Off -> applied `{on: false}` |
| tel_loss | not_applied when on | timed eRPM loss: no CLI argument (`erpm_loss` scenario key only) |
| tel_frozen | not_applied when on | "hook missing" |
| wind | not_applied unless zero wind | no CLI argument; `gust_x` is not parametrised (steady/peak/direction) |
| g4_typical_noise | not_applied | "hook missing" |

Fixed arguments: `--controller indi --model quad5in --sim v2 --rate-hz 800 --seed <sampler_seed mod 2^31> --sim-seed <gz_seed>`.

Missing arguments in run_scenario.py to report: timed sag/saturation/weak-motor, timed eRPM loss, frozen rpm, parametrised wind/gust,
G4 noise profile, fractional-ms delays (`--dly-*` is int). Result: every non-pretest draw has `wind` in not_applied, and about 40 % also
sag/weak/saturation, so as it stands a G3 flight under this driver exercises plant, delay, vibration, GNSS, telemetry latency/dropout and
mode only.

## Tests (`bench/tests/test_g3_run.py`, plain asserts, 200 campaign draws + pretest)
All 6 PASS: factors accounted, missing hooks reported, model_variant mapping (present iff non-nominal, values round-trip through the
run_scenario.py K=V rule), params override base (G1 = base x k, SIM_GZ_ERPM_LAT, untouched base keys kept), argv flags, determinism.
Mutation check: removing `mass` from the model-variant key list made `test_model_variant_mapping` FAIL; restored, all PASS again.

## Dry run (`--seed 7 --n 300 ... --dry-run`, first 2 of 5 shown, stdout trimmed)
```
run_scenario.py --scenario stick_zsine_o6 --controller indi --model quad5in --sim v2 --rate-hz 800 --seed 560268241 --sim-seed 115739492 --out /tmp/g3dry/run_000 --params /tmp/g3dry/run_000/g3_params.txt --stick-mode stabilized --model-variant tau=1.397339,tau_down=1.784948,mass=1.018731,ixx=1.026155,iyy=1.197303,izz=1.275334 --dly-act 2 --dly-imu 2 --vib-acc 2.367601 --vib-gyr 0.11838 --gps-dly 206 --gnss-delay 206
run_scenario.py --scenario o1_lemniscate ... --sched --model-variant tau=0.677305,tau_down=2.520729,mass=1.038625,... --dly-act 2 --dly-imu 2 --vib-acc 1.622072 --vib-gyr 0.081104 --gps-dly 250 --gnss-delay 250
```

## UNVERIFIED
- Nothing was flown. argv was checked by reading run_scenario.py argparse, not by running it (no `--help` parse of a generated argv).
- Scenarios `o1_lemniscate` / `stick_zsine_o6` are stand-ins: no scenario with the G3 timeline (take-off, hover 25, step_roll, lemniscate 30, hold 20) exists, and the stick scenario is not the same flight. `flight_s` and timeline event offsets are not used.
- `--seed` fed to run_scenario is sampler_seed mod 2^31; its role beyond naming is unchecked.
- Whether `--sched` combines with `--sim v2 --stick-mode` absent, and whether `--params` accepts `SIM_GZ_ERPM_LAT` as a boot param, rely on the S108 note.
- The 1800 s default per-run timeout is a guess, not a measured flight duration.
- Dry-run `--n 300` draws the whole campaign then prints from `--start`; only the first 5 lines were viewed.
