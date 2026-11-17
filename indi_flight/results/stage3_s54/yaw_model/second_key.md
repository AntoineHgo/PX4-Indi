# Second key, yaw loop break M3a (S54)

Script: indi_flight/bench/yaw_break_key2_s54.py (numpy only, hand-coded bilinear Butterworth 30 Hz).
Written from indi_rate_control.cpp lines 330-410 only. L = -y/x, loop includes attitude P=2.8, K=10, lead c=0.5.

## Results (my model)
== law coded
f=0.1: |L|=37.17 dB arg=-168.4 deg
f=1: |L|=6.00 dB arg=-120.0 deg
f=10: |L|=-21.48 dB arg=-103.0 deg
f=20: |L|=-25.61 dB arg=-134.4 deg
Ms=3.47 dB
crossover 1.850 Hz (down) arg=-129.7 PM=50.3
== law c
f=0.1: |L|=37.17 dB arg=-168.4 deg
f=1: |L|=3.53 dB arg=-108.2 deg
f=10: |L|=-8.36 dB arg=-97.2 deg
f=20: |L|=-14.19 dB arg=-139.5 deg
Ms=1.31 dB
crossover 1.442 Hz (down) arg=-94.2 PM=85.8
law c G2x0.5: Ms=2.93 dB, crossovers=[(1.43, 49.9)]
law c G2x2: Ms=3.70 dB, crossovers=[(10.69, 82.2)]
law c taup x2: Ms=1.64 dB, crossovers=[(1.56, 63.6)]

Reference (flight, coded law): -0.4 dB/178, -0.5/157, -11.6/53, -19.8/-4 deg at 0.1/1/10/20 Hz.

## Verdict
1. DISAGREE that the coded law gives L -> -1 at DC in my model: |L| = +37 dB / -168 deg at 0.1 Hz (integrator-like, K/s from the rate loop).
2. My coded-law numbers do not reproduce the flight reference at any of the four frequencies (Ms 3.5 dB, PM 50 deg at 1.85 Hz), so my model is NOT validated against the flight data.
3. Option (c) is integrator-like in my model: crossover 1.44 Hz, PM 86 deg, Ms 1.3 dB.
4. Option (c) under mismatch: Ms 2.9 (G2 x0.5), 3.7 (G2 x2), 1.6 dB (tau_p x2), all below 10 dB. AGREE on this part, conditional on the model being right.
5. In my model the G2 difference term is a small perturbation at low frequency (G2*jw ~ 17 vs G1 205 at 0.1 Hz), so coded and (c) agree at 0.1 Hz; the flight L=-1 must come from something my model lacks.

## Comparison with key 1 (bench/yaw_break_model_s54.py, /tmp/k1.txt)
Key 1 "yaw G2 27 M3a" gives 4.4 dB/-175, -0.6 dB/160, -10.5 dB/72, -16.7 dB/24 deg and Ms 24.4 dB, PM -6 deg, which matches the flight reference at 0.1 and 1 Hz, so key 1 reproduces L -> -1. Key 1 "yaw G2 0 M3a" gives 37.2/-168.4, 3.5/-108, -8.3/-97, -14.1/-139, Ms 1.3, PM 85.5, which equals my numbers for both of my laws (my option (c) matches to 0.1 dB, and my coded law matches the G2=0 case). So my coded law behaves as if G2 had no effect. The two keys agree on the structure without G2 but disagree on how G2 enters (my G2 term is a small low-frequency perturbation, key 1's collapses the loop gain by about 33 dB at 0.1 Hz). I did not resolve which is right. The likely cause is a difference in how the plant G2 term and the feedback-pair filters are modelled, and key 1 is the one that matches the flight data. My option-(c) Ms numbers should not be relied on until this is settled.

## Orchestrator addendum (S54): key-2 transcription error, corrected

Key 2 divided the coded law by G1 + G2 (1 - z^-1)/dt; the code divides by the static G1 + g2/dt
(`indi_rate_control.cpp` l.388-390). With only that line corrected (marked in `bench/yaw_break_key2_s54.py`,
output `second_key_fixed_out.md`): coded law 4.35 dB / -174.6 deg at 0.1 Hz, -0.60 / 160.5 at 1 Hz, -10.5 / 71.8 at
10 Hz, -16.8 / 23.0 at 20 Hz, Ms 24.4 dB = key 1 within 0.1 dB. Option (c), not affected by the error: Ms 1.31 dB,
crossover 1.44 Hz PM 85.8; G2 x0.5 Ms 2.9 (PM 49.9), G2 x2 Ms 3.7, tau_p x2 Ms 1.6 = key 1.
Verdict after correction: AGREE (coded law L ~ -1 near DC at M3a; option (c) integrator-like, Ms < 4 dB under the
mismatches tested). Both models give |L| +4.4 dB at 0.1 Hz where the flight gives -0.4 dB: below 1 Hz the models
depart from the flight (slow modes not modelled: heading loop details, yaw drag); the model "PM -6" crossing of the
coded law is not a stability verdict (the flight is stable) and is not used.
