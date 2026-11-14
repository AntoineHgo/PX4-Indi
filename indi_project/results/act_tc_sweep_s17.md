# ACT_TC robustness sweep (session 17, post-acceptance, D-actsweep)

Frozen INDI candidate (r4f/c00, MC_INDI_ACT_TC 0.01142 s) with MC_INDI_ACT_TC scaled by f, stock gz_x500 plant,
step_roll, speed 4, seeds 1-3. Commands: `results/act_tc_sweep_s17/run.sh` (21/21 runs, 0 failures).
Output `results/runs/step_roll/indi_act<f>/seed<N>_x4/metrics.json`. PID row: same scenario/seeds/speed.
Mean ± std over 3 seeds. Plant/model time-constant ratio = 1/f.

| controller | n | roll rate RMS (rad/s) | roll att RMS (deg) | overshoot (%) | motor-rate RMS (1/s) | motor sat frac | alloc sat frac |
|---|---|---|---|---|---|---|---|
| pid_default | 3 | 0.086±0.001 | 3.379±0.043 | 0.137±0.013 | 0.544±0.014 | 0 | 0 |
| indi f=0.33 (ratio 3) | 3 | 0.129±0.006 | 2.960±0.063 | 0.477±0.047 | 0.788±0.055 | 0 | 0 |
| indi f=0.5 (ratio 2) | 3 | 0.128±0.002 | 2.939±0.106 | 0.294±0.017 | 0.690±0.015 | 0 | 0 |
| indi f=0.67 (ratio 1.5) | 3 | 0.133±0.007 | 2.849±0.051 | 0.269±0.002 | 0.678±0.049 | 0 | 0 |
| indi f=1 (frozen) | 3 | 0.138±0.002 | 2.906±0.064 | 0.262±0.022 | 0.646±0.008 | 0 | 0 |
| indi f=1.5 (ratio 0.67) | 3 | 0.143±0.003 | 2.910±0.032 | 0.232±0.003 | 0.605±0.023 | 0 | 0 |
| indi f=2 (ratio 0.5) | 3 | 0.152±0.004 | 2.863±0.058 | 0.212±0.008 | 0.609±0.018 | 0 | 0 |
| indi f=3 (ratio 0.33) | 3 | 0.161±0.002 | 2.885±0.042 | 0.182±0.004 | 0.596±0.010 | 0 | 0 |

## Findings

1. **No limit cycle anywhere in the sweep.** Across a 9x range of assumed actuator time constant the roll-rate RMS
   moves by 25 % (0.129-0.161) and attitude RMS stays within seed noise (2.85-2.96 deg). In H5 the 5-7 Hz limit cycle
   raised roll-rate RMS to 3.9x PID; nothing comparable appears here, even at f=0.33.
2. **The D-actsweep equivalence assumption is falsified.** Model too fast by 2x on the stock plant (f=0.5) is
   benign, while plant too slow by 2x with the stock model (H5 diag_h5_tau) gave the limit cycle, and plant x2 with
   the model matched x2 removed it (session 15). So the time-constant ratio is not the only factor: the slower plant
   adds real phase lag at the frozen gains, and a matched actuator model compensates it. What destabilises is the
   combination of a slower physical actuator and a model that does not know it, not model error alone.
3. Trends: a faster assumed model (small f) raises overshoot (0.18 -> 0.48 %) and motor-rate effort (0.60 -> 0.79,
   +32 %) and lowers rate RMS slightly; a slower assumed model does the opposite. Effects are graded and small.
4. Report wording: INDI's sensitivity is to an actuator that is slower than modelled, not to ACT_TC mis-set on a
   fast actuator. A sweep of the plant time constant (via `bench/model_variant.py` key tau, needs ~21 more runs) is
   the experiment that would map the stability boundary properly; not run in session 17.

Caveats: one scenario, 3 seeds, speed 4 (attitude/rate metrics verified speed-equivalent for PID only, D-speed).
Post-acceptance characterisation: does not change `results/acceptance_s15.md`.
