# GM jump check (T80): roll, INDI meas Tb 0, n 1, eta 1

Table row = `margins_of(L_indi, fs, meas=True, Tb=0, n=1)`, grid geomspace 0.05 Hz to 0.45 fs. Dense check: 0.1 Hz to fs/2 (linear interp).

| fs [Hz] | -180 crossings: f [Hz], \|L\| [dB] | picked | dense grid |
|---|---|---|---|
| 800 | 11.91, -21.13 (GM 21.13); fs/2 = 400: L = 0 exactly, +inf | 11.91 Hz, GM 21.13 dB | same, Nyquist point not the min |
| 400 | 27.00, -34.77 (GM 34.77); fs/2 = 200: L = 0 exactly, +inf | 27.00 Hz, GM 34.77 dB | same |

|L|=1 crossings: 2.74 Hz (800) and 2.72 Hz (400), PM 54.3 / 54.2 deg, so PM agrees. The GM difference is only in the -180 crossing.
Phase at 11.9 Hz: 800 Hz is -180.0 deg and falls to -196 at 20 Hz. 400 Hz is -174.9 deg and flat (-176 at 20 Hz) up to the crossing at 27 Hz, where |L| = -22.2 dB at 11.9 Hz.

Verdict: the 21.1 dB at 800 Hz is GENUINE (model). It is a -180 crossing at 11.9 Hz, far from Nyquist, reproduced on the dense grid. Nyquist is not the cause: L is exactly 0 at fs/2 (F has a double zero at z = -1), giving +inf that never becomes the min. Only fmax_frac 0.5 breaks margins() (GM NaN).
Verdict for the 34.8 dB (400 Hz) and 33.6 dB (267 Hz): UNCLEAR, not a robust margin. The 27 Hz crossing sits on a phase plateau 5 deg above -180. A few degrees more lag puts the crossing at ~12 Hz, GM ~22 dB. The 14 dB rate jump is phase-shape sensitivity, not a grid or Nyquist artefact.
Script: /tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/ae2cb827-858b-4fb8-b012-422538715809/scratchpad/gm_jump_check.py
