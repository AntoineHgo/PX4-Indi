# S83 velocity/position-break re-fly (D-GAP overturn test, z axis)

Break: MC_INDI_PINJ_* at the INDI stage input (S82 injector, commit 3b7af1282f), so L is the outer
(velocity/position) loop with the INDI acceleration loop closed. Second key of the injector:
`../stage5_s82_velbreak/second_key.md` (AGREE WITH MINOR).

Set-up: hover_long, quad5in, INDI stack, v2, 400 Hz, seed 1, speed 4. Params `tb10.params`, `tb033.params`
(S82 pre-test params with DLY 20 s, NP 5, and MC_INDI_POS_TB 1.0 / 0.33). The window starts 20 s after the first
armed, non-landed cycle, i.e. after the climb. The first period is discarded (`margins_est.frf_periodic`,
discard=1), which leaves 4 periods of 10 s. Bins 0.2-8 Hz.

Commands:
```
indi_project/docker/run.sh -n s83tb10 -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario hover_long \
  --controller indi --model quad5in --sim v2 --rate-hz 400 --seed 1 --speed 4 \
  --params indi_flight/results/stage5_s83_velbreak/tb10.params --out indi_flight/results/stage5_s83_velbreak/tb10
indi_project/docker/run.sh -n s83an1 -t 240 -- python3 indi_flight/bench/pinj_csv.py \
  indi_flight/results/stage5_s83_velbreak/tb10/flight.ulg 2 indi_flight/results/stage5_s83_velbreak/tb10_pinj_z.csv \
  --Tp 10 --fmin 0.2 --fmax 8 --margins > indi_flight/results/stage5_s83_velbreak/tb10_margins.json
```
(same with tb033)

| tb [s] | PM [deg] | f_c [Hz] | DM [s] | GM | Ms | min coh x / y |
|---|---|---|---|---|---|---|
| 1.0  | 57.3 | 0.67 | 0.237 | no -180 crossing in band | 1.19 (1.5 dB) | 0.82 / 0.97 |
| 0.33 | 59.1 | 0.62 | 0.264 | no -180 crossing in band | 1.19 (1.5 dB) | 0.52 (0.2 Hz) / 0.96 |
| S82 pre-test, tb 1.0, DLY 8 NP 4 | 54.4 | 0.60 | - | - | - | - |

Reading:
- D-GAP overturn criterion "velocity-break PM < 45 deg" is NOT met at tb or at tb/3: PM is 57-59 deg and
  changes by less than 2 deg between them. The D-GAP blend does not reduce the outer-loop margin at these values.
- The repeat with a later window moves PM from 54.4 to 57.3 deg at tb 1.0. The S82 window overlapped the climb.
  This is the spread for one seed and two windows, not a confidence interval.
- The other half of the overturn test (lightly damped HF mode of the acceleration loop, peak > 3 dB) needs the
  stage-OUTPUT break, which does not exist yet. Ms of the outer loop is 1.5 dB. That bounds the outer loop, not the
  inner acceleration loop. D-GAP stays ACCEPTED pending that break.
- The 0.2 Hz bin at tb 0.33 has a low coherence (0.52). The crossing (0.62 Hz) is 3 bins away, with coherence above
  0.9 near it.

Open before G2 use: stage-output (acceleration-loop) break, x/y axes, 800 Hz, AX = 0 bit-identical flight,
pinj_csv.py synthetic self-test, linear-model cross-check, injector minors (re-arm in the same boot, yaml wording).
