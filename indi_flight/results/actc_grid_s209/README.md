# ACT_TC identification grid S209 (SITL error table)
Commands (repo root):
- run: `python3 indi_flight/bench/actc_grid.py --out indi_flight/results/actc_grid_s209` (30 cells, see PRETEST.md)
- table: `python3 indi_flight/bench/actc_grid_table.py` (reads GRID.tsv, per-cell lines + stats)
- self-test: `python3 indi_flight/bench/tests/test_actc_grid_table.py`

r_slow = tau_sym_hat / tau_slow, r_mean = tau_sym_hat / tau_mean. Percentile 95: numpy linear interpolation
(rank 0.95 (n-1)). All 30 cells counted. Frames factor (cells f3) was NOT applied in the sim (A-59): treated as frames 0.
GRID_noframes.tsv (2 earlier cells) is excluded from all statistics.

| class | n | r_slow min / max / p95 | r_mean min / max / p95 |
|---|---|---|---|
| all | 30 | 0.599 / 1.002 / 1.002 | 0.899 / 1.002 / 1.002 |
| asym 1 | 8 | 0.996 / 1.002 / 1.002 | 0.996 / 1.002 / 1.002 |
| asym 3 down-slow | 14 | 0.599 / 0.651 / 0.646 | 0.899 / 0.977 / 0.969 |
| asym 3 up-slow | 8 | 0.623 / 0.657 / 0.652 | 0.934 / 0.985 / 0.979 |

Per-motor time constants, max |est/true - 1| over 30 cells: tau_up 3.7 % (est biased high, +1.2..+3.7 %),
tau_down 3.6 % (est biased low, -0.8..-3.6 %). Error grows with tau_slow (largest at tau_slow 3x0.033 s).
tau_sym_hat sits near the harmonic-like mean of the two: about 0.6 tau_slow and 0.9-0.98 tau_mean at asym 3.

Delay: delay_hat minus true actuator delay = +1.70..+1.82 ms for both true 0 and 10 ms (n=15 each), i.e. a constant
~1.75 ms offset (base pipeline latency), scatter 0.12 ms. The 10 ms injected delay is recovered to within 0.1 ms.

Failed identifications: 0 of 30 (all PASS, no flags, status done).

Limitations: frames inert (A-59); one seed except the 4 asym-3 down-slow tau corners (seed 2); speed 4 sim;
roll axis injector only; quad5in plant only.
