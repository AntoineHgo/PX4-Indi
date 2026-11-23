# ACT_TC refit on the telemetry instance (esc_status instance 0), no new flights
Command, per cell (30 cells, plus the 2 *_noframes folders), 8 in parallel:
`python3 indi_flight/bench/ident_actc.py <cell>/flight.ulg --esc-instance 0 --rpm-max 25783 --t0 24 --t1 76 --json <cell>/ident_inst0.json`
Rows: GRID_inst0.tsv (30 cells), GRID_inst0_noframes.tsv (2). Table: `actc_grid_table.py GRID_inst0.tsv`.
Failed identifications: 0/30 (0/2 noframes), no flags raised. All PASS.
| quantity                       | truth instance (README) | instance 0 (telemetry) |
| max abs(est/true-1) tau_up     | 0.0370                  | 0.0388                 |
| max abs(est/true-1) tau_down   | 0.0358                  | 0.0375                 |
| r_slow sym 1 (n=8)             | 0.9956 .. 1.0021        | 0.9990 .. 1.0039       |
| r_slow 3d (n=14)               | 0.5990 .. 0.6510        | 0.5988 .. 0.6499       |
| r_slow 3u (n=8)                | 0.6229 .. 0.6568        | 0.6218 .. 0.6567       |
| r_mean ranges (sym, 3d, 3u) | 0.9956-1.0021, 0.8986-0.9765, 0.9344-0.9852 | 0.9990-1.0039, 0.8983-0.9748, 0.9327-0.9851 |
delay_hat - true delay, ms (min..max, n):
| true delay, frames | truth instance   | instance 0         |
| 0 ms, frames 0     | 1.70..1.82 (14)  | 2.87..3.00 (14)    |
| 10 ms, frames 0    | 1.74 (1)         | 2.93 (1)           |
| 0 ms, frames 3     | 1.73 (1)         | 6.63 (1)           |
| 10 ms, frames 3    | 1.72..1.78 (14)  | 6.74..6.83 (14)    |
noframes folders (frames set after boot): truth 1.75 / 1.72, instance 0 6.63 / 6.79 (delay_hat 6.66 and 12.91 ms).
Reading: tau is unaffected by the telemetry artefacts (same errors to ~0.2 percent, same asym ratios; the
asym-class r_slow/r_mean are the identifier's mean-vs-slow convention, not changed by the instance).
Delay: telemetry adds +1.2 ms with frames 0 (2.9 vs 1.7) and +5.0 ms with frames 3 (6.7 vs 1.7), i.e. frames 3 is +3.8 ms
over frames 0 on the telemetry, as expected. The delay_hat on instance 0 is an actuator-plus-telemetry delay, not the actuator delay.
