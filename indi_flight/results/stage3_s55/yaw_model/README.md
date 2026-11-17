# S55 D-YAW-INV model: ACT_TC mismatch and controller rate (UNKEYED extension of the keyed S54 model)

Command: `python3 bench/yaw_break_model_s55.py results/stage3_s55/yaw_model/model_out.txt` (imports `loops()`
from the keyed `bench/yaw_break_model_s54.py` unchanged). Grid: fs 250/400/800 Hz, law code / lpf (option c),
model tau_m = 33 ms x {0.5, 1, 1.5, 2}, plant G2 x {0.5, 1, 2}, plant tau 33 ms x {1, 2}. Yaw G1 205, G2 27, K 10, P 2.8.
Margins are wrap-free (PM = 180 - |arg L|, GM at real-axis crossings with Re L < 0); Ms is primary.

Findings
1. Option (c) is dt-independent: worst M3a Ms 24.4 / 24.2 / 24.0 dB at 250 / 400 / 800 Hz, same pattern per case.
   Coded law: M3a Ms 21-57 dB everywhere (dead-beat spin-up, A-27).
2. Option (c), inside the ACT_TC tolerance already set for roll (model tau_m >= plant tau, D-RATE-LEAD addendum 2)
   and plant G2 x0.5..x2: M3a Ms <= 5.9 dB, GM >= 8.2 dB (worst: tau_m = plant, law G2 = 2x plant). Ms <= 6 dB
   implies GM >= 6 dB and PM >= 29 deg.
3. Weak sides: model tau below plant (tau_m x0.5 with plant x1 or x2) and law G2 above plant G2 (plant x0.5).
   Combined, the worst corner reaches Ms 24 dB / GM 0.6 dB. Law G2 below plant (plant x2) is benign.
   Consequence for stage 4: identification reports an upper bound of tau_c (already decided) and a LOWER bound of G2.
4. Plant-only break: Ms 1.3-17.9 dB, same weak corner; negative GM entries are low-frequency real-axis crossings with
   |L| > 1 (conditionally stable shape from the attitude integrator chain), not a loss of stability: read Ms.
Overturn rule of D-YAW-INV (G2 x0.5..2 gives GM < 6 dB) is NOT triggered inside the tau tolerance; it is outside it.
