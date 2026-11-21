# A-52 raw-sample check (driver: indi_flight/bench/a52_raw_check.py), hoverL_harsh_s1, 37.0-92.0 s

## Raw sample intervals (in window)
| stream | n | median dt | dt min / max | max/min | gaps >1.5x median |
|---|---|---|---|---|---|
| actuator_motors | 43994 | 1.25 ms (800 Hz) | 1.25 / 2.50 ms | 2.0 | 7 (0.016 %) |
| esc_status inst 1 | 39001 | 1.25 ms | 1.25 / 3.75 ms | 3.0 | 4934 (12.7 %) |
Criterion: uniform enough if gaps >1.5x median < 1 % of intervals. Command: yes. Rotor: NO (12.7 % gaps,
~11 % of 800 Hz slots missing); the rotor raw numbers below are run at the median rate anyway, as specified,
and are NOT a valid absolute measure (R20 raw 0.527 vs 0.339 rad/s gridded: timing jitter adds fake HF).

## Each script's own filter/RMS on raw samples (key2 grid function swapped for identity in the driver only)
| metric | key1 | key2 | rel. diff |
|---|---|---|---|
| C20 | 5.3265e-4 | 5.3264e-4 | 0.001 % |
| C4 | 9.9771e-4 | 9.9770e-4 | 0.002 % |
| R20 rad/s | 0.52751 | 0.52734 | 0.03 % |
| R4 rad/s | 0.84809 | 0.84821 | 0.015 % |
Hover normaliser: key1 998.178 (edges excluded) vs key2 998.140 (whole window): 0.004 %, negligible.
**PASS** (all < 2 %). Filter design/order/cut-off normalisation, edge exclusion, motor mean are equivalent.

## Cause of the original 7 % C20 gap (found, not a filter difference)
Gridded runs at the SAME window 37.0-92.0: key1 C20 5.3248e-4, key2 5.3248e-4 (agree to 0.0003 %).
Original key2 run used window 36.993-91.993: key2 C20 4.95e-4, C4 9.76e-4; key1 at that window 5.325e-4, 9.977e-4.
Raw stamps lie on a 1.25 ms lattice (37.000 s is a lattice point; 36.993 s is ~0.4 sample off). key2 builds its
grid from t0, so a window start off the lattice puts every grid point between samples and linear interpolation
attenuates the 159 Hz content (~cos(pi*159/800*(2*phase)) up to 0.8x at half-sample). key1 starts the grid on the
first raw sample (phase 0), so it is insensitive. Key1 is right: it preserves the raw samples; key2 is
window-phase dependent (7 % C20, 2.2 % C4). R20/R4 pct differ less since rotor dt jitter dominates there.
