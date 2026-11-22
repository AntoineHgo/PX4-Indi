# A-44 closing run (S205): production ident_fit_yaw.py @57e80feac8 on axyaw / half_ax3

Commands (run from indi_flight/, each alone):
```
(ulimit -v 4000000; timeout 1800 python3 bench/ident_fit_yaw.py results/ident_m3a_s123/axyaw/flight.ulg --axis yaw --t0 22.1 --t1 76.0) > results/ident_yaw_a44_s205/axyaw.txt 2>&1
(ulimit -v 4000000; timeout 1800 python3 bench/ident_fit_yaw.py results/ident_m3a_s123/half_ax3/flight.ulg --axis yaw --t0 22.1 --t1 76.0) > results/ident_yaw_a44_s205/half_ax3.txt 2>&1
```

Per log (window 22.1-76.0 s, taps 15, decim 2, n 21520):
- axyaw: G1 207.51 rad/s^2 per unit, 95% CI +-2.73 (1.3 %); G2 26.910 (95% CI +-0.050, 0.2 %); Dr 1.491 1/s (95% CI +-0.080); shift 1 samples; Hansen J 55.0 (df 23); G1 vs 205.3: +1.08 % (band 199.1-211.5, in band)
- half_ax3: G1 208.13 rad/s^2 per unit, 95% CI +-3.25 (1.6 %); G2 26.874 (95% CI +-0.052, 0.2 %); Dr 1.462 1/s (95% CI +-0.101); shift 1 samples; Hansen J 60.2 (df 23); G1 vs 205.3: +1.38 % (band 199.1-211.5, in band)

Gates (axyaw / half_ax3):

| Gate | axyaw | half_ax3 |
|---|---|---|
| SW effective F, G1 >= 10 | PASS (307.4) | PASS (751.2) |
| SW effective F, G2 >= 10 | PASS (2.415e+04) | PASS (2.227e+04) |
| SW effective F, Dr >= 10 | PASS (1411) | PASS (909.2) |
| Hansen df >= 1 | PASS (23) | PASS (23) |
| J/df <= 20 | PASS (2.391) | PASS (2.616) |
| J curve finite on shift scan | PASS | PASS |
| latency shift interior to [-2,12] | PASS (1) | PASS (1) |
| CI/abs(G1) <= 0.15 | PASS (0.01314) | PASS (0.01564) |
| CI/abs(G2) <= 0.5 | PASS (0.001863) | PASS (0.001917) |
| filter-chain gain match <= 0.01 | PASS (2.814e-04) | PASS (2.814e-04) |
| excluded fraction <= 0.25 | PASS (0) | PASS (0) |

Verdict: axyaw IDENT PASS; half_ax3 IDENT PASS. Both within the 3 % closing band on G1.
