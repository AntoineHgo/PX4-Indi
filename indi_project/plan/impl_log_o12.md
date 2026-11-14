# impl log O-12 replay
- step1: wrote bench/watchdog_replay.py (pyulog on host OK, 3890 flight.ulg found).
- step2: first full run (5.5 min, 4 workers, nice 19): 3895 logs, 0 parse failures, but 2069 trips; 2018 were height<0.3 at ~19 s = takeoff (landed=false from 16.2 s, 5 m reached ~24 s). 3 s trim is not enough. Fix: window start also waits for height >= 0.9*median airborne height. Also run.json 'error' keys matched final_error_pct etc.; tightened key regex. Re-running.
