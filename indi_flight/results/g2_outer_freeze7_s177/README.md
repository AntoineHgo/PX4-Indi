# S177 G2 outer cells re-flown at freeze-7 (INDI pos xy gains MC_INDI_XY_P/XY_VP 1.9/3.6)

Same 24 cells and recipe as g2_outer_freeze_s163 (batch.sh + fly.sh copied, only the out dir and container prefix s177o changed;
timeouts added: flight 1300 s, margins/holes 300 s). Params base results/g5_freeze_s157/params.params (xy gains are firmware
defaults, not in the file). Plant: matched GNSS 110 ms, `--vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0`.
Cells: pt{0,1}_ax3_r{800,400}_s{1,2} (z: AMP 0.04, TP 10, hover_long) = 8; pt{0,1}_ax{1,2}_r{800,400}_s{1,2} (xy: AMP 0.08, TP 20,
hover_xlong) = 16. PT0 = vel/pos break (--point input), PT1 = INDI accel break (--point output).

Source commands (fly.sh per cell, in order):
- flight: `indi_project/docker/run.sh -n s177o$N -t 1200 -- python3 indi_flight/bench/run_scenario.py --scenario ${SCN:-hover_long} --controller indi --model quad5in --sim v2 --rate-hz $RATE --seed $SEED --speed 4 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 --params $D/$N.params --out $D/$N`
- margins: `python3 indi_flight/bench/pinj_csv.py $D/$N/flight.ulg $((AX-1)) $D/${N}_pinj.csv --Tp ${TP:-10} --fmin 0.2 --fmax 8 --margins --point $POINT > $D/${N}_margins.json`
- holes: `python3 indi_flight/bench/hole_report.py $D/$N/flight.ulg > $D/${N}_holes.txt`
(margins and holes are run inside queue2.sh/fly.sh right after each flight, via indi_project/docker/run.sh.)

Run: queue2.sh waits (30 s poll, max 2 h) for freeze7_s177/queue.log QUEUE_END and no docker container named s177*, then flies.
Log: queue2.log (ends QUEUE_END, also on WAIT_TIMEOUT); status: queue2_status.tsv (cell, start, end, rc, flight_ulg).
Resume (repo root, only when no sim is running): 
`setsid nohup bash indi_flight/results/g2_outer_freeze7_s177/queue2.sh >> indi_flight/results/g2_outer_freeze7_s177/queue2.log 2>&1 &`
A cell is skipped when flight.ulg and a non-empty margins json exist; a flight without margins is only re-scored.

Scoring afterwards (already keyed, no second key): margins.json + holes.txt per cell are produced by the queue. Then:
- table: `python3 indi_flight/bench/g2_freeze_table_s163.py` and second key `python3 indi_flight/bench/g2_key2_outer_s164.py`
  hard-code results/g2_outer_freeze_s163 (read-only bench scripts); run them on a copy with that path replaced by
  g2_outer_freeze7_s177, or compare _margins.json directly with the s163 ones. Model for comparison: g2_outer_model_s177.md
  (xy PM 46 deg, GM 7.8 dB; limits 45 deg / 6 dB). Holes: grep OVERALL *_holes.txt.
