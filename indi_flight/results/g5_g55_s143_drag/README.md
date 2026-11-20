# S143 drag feed-forward probe, o1_lemniscate seed 1 (PROBE ONLY, never gate evidence)

Hypothesis (D-A18-SOURCE): linear rotor drag (a_truth = tilt_accel - 0.514 v) is missing from the acceleration
feed-forward. Probe: the runner adds D * v_ref to the sent acceleration, earth x,y only. New flag
`--probe-ff-drag D` in bench/run_scenario.py (default 0 = unchanged; value recorded in run.json as probe_ff_drag).
Same firmware binary as S141 (no rebuild), params copied from ../g5_g55_s141_a18/params.params.

Command (as S141 run_batch.sh, plus the flag, out = this dir):
`indi_project/docker/run.sh -n x56drag1 -t 600 -- python3 indi_flight/bench/run_scenario.py --scenario o1_lemniscate
 --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110
 --params <dir>/params.params --probe-ff-drag 0.514 --out <dir>/o1_lemniscate_s1`
Scored with bench/g55_check.py (o1_lemniscate_s1.json), lag chain in lag_chain.txt.

| | S141 (D=0) | S143 (D=0.514) |
|---|---|---|
| horiz RMS vs truth | 0.590 m | 1.111 m (FAIL) |
| vert RMS | 0.045 m | 0.034 m |
| a_c delay x / y | 97 / 129 ms | -14 / 161 ms |
| truth position delay x / y | 125 / 158 ms | -12 / 199 ms |
| truth pos amp ratio x / y | 1.07 / 0.94 | 1.27 / 1.20 |

Result: hypothesis NOT supported as a simple feed-forward fix. x lag vanishes but amplitude overshoots 27 %
and y lag grows; RMS nearly doubles. Likely the INDI loop already compensates drag through the measured
acceleration (a_f), so adding it to a_ff double counts. Stage 1 delays in lag_chain.txt are vs the analytic
accel, so they include the injected D*v term (not a transport delay).
Validity: run rc=0, valid true, no invalid flags, n=14247 samples, full trajectory flown.
