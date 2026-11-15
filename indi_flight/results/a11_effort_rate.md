# A-11: effort metric versus logged sample rate (session 17)

Command: `python3 bench/a11_effort_rate.py results/det_g16_s4 results/det_g16_w125` (self-test: `--selftest`,
5 Hz sinusoid gives the analytic derivative RMS within 2 % for every variant). Output `a11_effort_rate.json`.

Motor-command derivative RMS (1/s) over the metrics window, mean of 5 same-seed flights:

| scenario | world | raw | zoh 285 Hz | zoh 250 Hz | 20 ms boxcar |
|---|---|---|---|---|---|
| hover | 4 ms (250 Hz log) | 0.0075 | 0.0081 | 0.0075 | 0.0034 |
| hover | 1.25 ms (800 Hz log) | 0.0068 | 0.0058 | 0.0056 | 0.0021 |
| step_roll | 4 ms | 0.204 | 0.219 | 0.205 | 0.094 (0.089-0.108) |
| step_roll | 1.25 ms | 0.374 | 0.221 | 0.206 | 0.087 (0.079-0.098) |
| traj_lemniscate | 4 ms | 0.120 | 0.128 | 0.120 | 0.035 |
| traj_lemniscate | 1.25 ms | 0.276 | 0.164 | 0.151 | 0.041 |

- The raw value on the 1.25 ms world recomputed here equals `metrics.json` (0.374, 0.276): independent key for the
  raw metric.
- The x1.8-2.3 gap of A-11 is the sample rate: the 800 Hz log carries command content above the 125 Hz Nyquist
  limit of the old log. Resampling alone does not remove it (aliasing of that content); a fixed bandwidth does.
- At a fixed 20 ms bandwidth step_roll agrees within the same-seed spread. Traj (+17 %) and hover (-37 %) differ
  by more than the spread (spread < 3 %): a real change of the closed loop between controller rates 250 and
  800 Hz, small in absolute terms.
- Consequence: G4 effort is defined on a uniform grid at a fixed bandwidth, never on the raw logged derivative;
  effort numbers from different logged rates are not compared. metrics.py keeps the raw value for history until
  G4 is written.
