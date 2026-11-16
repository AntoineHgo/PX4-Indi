# Second-key check: bias med arm-5..arm (T70)

Independent script: `/tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/175d5387-248c-41d5-a59e-00d3ffee5b4e/scratchpad/key_t70.py`
(median of `estimator_baro_bias.bias` over `[t_arm - 5 s, t_arm]`, `t_arm` = first `vehicle_status.arming_state == 2`, timestamps in microseconds).
Checker table: `/tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/175d5387-248c-41d5-a59e-00d3ffee5b4e/scratchpad/t70_table.md`

| log | t_arm (s) | n | mine (2 dp) | checker (2 dp) | verdict |
|---|---|---|---|---|---|
| indi_flight/results/a19a20_s34/hover_r1/flight.ulg | 30.00 | 99 | 0.12 | 0.12 | AGREE |
| indi_flight/results/a19a20_s34/hover_r2/flight.ulg | 30.01 | 100 | 0.15 | 0.15 | AGREE |
| indi_flight/results/g16_set_s32/speed4/hover/r1/flight.ulg | 30.01 | 100 | 0.17 | 0.17 | AGREE |
| indi_flight/results/g16_set_s32/speed4/hover/r2/flight.ulg | 30.01 | 101 | 0.15 | 0.15 | AGREE |
| indi_flight/results/g16_set_s32/speed4/hover/r3/flight.ulg | 30.00 | 100 | 0.11 | 0.11 | AGREE |
| indi_flight/results/g16_set_s32/speed4/hover/r4/flight.ulg | 30.01 | 100 | -0.06 | -0.06 | AGREE |
| indi_flight/results/g16_set_s32/speed4/hover/r5/flight.ulg | 30.01 | 100 | -0.03 | -0.03 | AGREE |

Result: 7/7 AGREE at 2 decimals.

## Diff review

- The change was already committed in `5cf9b5feaf` when reviewed, so `git diff` was empty. Reviewed the committed lines 28-50 of `indi_flight/bench/a14_close_check.py` instead.
- Window `(timestamp >= t_arm - 5e6) & (timestamp <= t_arm)`: matches the spec. Units are microseconds (t_arm values 30.00 to 30.01 s agree with the table).
- Empty window yields NaN, not a crash. No-arm yields `t_arm = None` and skips the block. Neither path is exercised by these 7 logs, so both are untested here.
- Defects found: none in the new logic.
- Pre-existing, not part of this change: `bias['bias'][0]` and the `topic()` calls raise if a topic is missing or empty.
- Note: the script calls `site.getusersitepackages()` because `python3 -I` drops the user site, where pyulog is installed. Without this the import fails.
