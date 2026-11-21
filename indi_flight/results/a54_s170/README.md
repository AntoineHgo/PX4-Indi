# A-54 cause search (S170, one session, probe, UNKEYED)

Logs: results/g4_gate_s169/hover_harsh_s1 (INDI), results/a54_s169/pid_hover_harsh_s1 (PID). Scripts (docker):
`bench/a54_probe3.py LOG T0 T1 ...` (per-window line table), `a54_probe.py`, `a54_probe2.py` (chain sweep).

INDI harsh hover, hold windows (true rotor speed from esc_status inst 1):

| window s | rpm | sensor_accel x 1P | sensor_accel z | vehicle_acceleration z (267 Hz) | actuator_motors 20-100 Hz |
|---|---|---|---|---|---|
| 60-70 | 9532 (158.9 Hz) | 159.0 Hz | 323.5 Hz | 57.0 Hz, 2807x | 70.0 Hz, 747x |
| 75-85 | 9531 | 159.0 | 323.5 | 56.5, 3196x | 70.0, 488x |
| 90-100 | 9502 | 159.0 | 323.0 | 56.5, 709x | 22.0, 12x |

(105-115 s of the S169 window is the landing: rpm falls, excluded here.)

Findings:
1. The hook (GZBridge::addRotorVibration, D-VIB-HOOK) puts 1P (159 Hz) on accel x/y and the blade-pass line NB x 1P =
   476.5 Hz (NB 3) on z. The IMU runs at 800 Hz (Nyquist 400): the blade-pass line appears at 800 - 476.5 = 323.5 Hz in
   sensor_accel (predicted 323.0, measured 323.5), then folds again at the 266.7 Hz accel decimation to 56.5 Hz in
   vehicle_acceleration (predicted 56.3). Confirmed on the data.
2. The 70.0 Hz motor line tracks neither fold above. Candidate (UNVERIFIED): 1P 159 Hz through an 88.9 Hz stage
   (3 x 3.75 ms, EKF2 prediction step): 159 - 88.9 = 70.1 Hz. Both stacks carry it (PID ref 78x, INDI 768x) -> stock
   sensors/EKF2 chain (O-11), excited by the accel vibration; INDI's larger ratio = its acceleration feedback gain.
3. Sim vs real: a real 8 kHz IMU publishing FIFO means at 800 Hz attenuates the 476.5 Hz line by sinc ~0.5 (-6 dB)
   but still aliases it; the 1P line is below Nyquist and physical. So the line is NOT a pure simulator alias that a
   hook fix removes: a FIFO-mean model would lower the ratio ~4x (power), not below 20x for INDI (768 -> ~190).
4. Absolute size: line RMS 2.5e-4 of full-scale command (S169) = half of one DShot step (1/2000 = 5e-4); C20 23x below
   its limit. The chatter clause is the only G4 item that fails, and it is a relative ratio (lesson 6).
Decision: no hook change (would not close the clause, and would bend the plant toward a pass). Owner Q14.
