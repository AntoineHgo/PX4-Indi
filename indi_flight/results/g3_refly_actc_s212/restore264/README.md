# Draw 264 per-factor restoration (G3 item 1, loss of control)

Purpose: find which single factor of draw 264 (C3 corner, speed 1) is needed for the INDI stack's loss of control.

## Method

- Each variant is draw 264 (`samples_actc/run_024.json` values) with ONE factor set to nominal (`scripts/make_variants.py`); `joint` is the reverse: every factor nominal except saturation and weak motor.
- Speed 1, gate binary 903eae63, one flight at a time (`scripts/batch.sh`), outcomes in `batch.log` and `indi_<name>/SCORES.tsv`.
- Drawn values: saturation scale 0.351 (2.0x hover), weak motor 3 at 0.709, mass 1.3, wind 3.36 m/s + gust 5.64 m/s, vibration x4.67, delay 10 ms, GNSS mismatched, tau up 0.5 / down 0.60, g1 error, inertia.
- Fault time = in-flight parameter write that applies saturation/weak motor (`scripts/tilt.py`); max tilt is after that time. The `orig` row is the unmodified draw; `actc` sets ACT_TC to the nominal 0.033 (drawn 0.0177). `joint` also uses ACT_TC 0.033, tau/g1/inertia/etc. nominal.
- Joint script note: `joint` was added to `make_variants.py` (optional name filter as 3rd argument); it was generated from `../samples` (original draw).

## Results

| variant (factor to nominal) | outcome | watchdog reason, sim time | fault t [s] | max tilt after fault [deg] | key1 / key2 |
|---|---|---|---|---|---|
| orig (none) | LOC | height < 0.3 m, 60.92 | 58.92 | 71.2 | INVALID / INVALID |
| actc (ACT_TC) | LOC | tilt > 60 deg 0.5 s, 60.59 | 58.91 | 74.4 | INVALID / INVALID |
| delay | LOC | tilt > 60 deg 0.5 s, 60.54 | 58.91 | 74.7 | INVALID / INVALID |
| g1 | LOC | height < 0.3 m, 60.71 | 58.88 | 76.8 | INVALID / INVALID |
| inertia | LOC | tilt > 60 deg 0.5 s, 60.26 | 58.85 | 104.5 | INVALID / INVALID |
| tau | LOC | tilt > 60 deg 0.5 s, 60.52 | 58.88 | 76.2 | INVALID / INVALID |
| tel | LOC | height < 0.3 m, 60.90 | 58.88 | 71.0 | INVALID / INVALID |
| wind | LOC | height < 0.3 m, 59.99 | 58.10 | 69.3 | INVALID / INVALID |
| vib | LOC | > 3 m below hold altitude 1 s, 60.78 | 58.12 | 64.2 | INVALID / INVALID |
| gnss | LOC | height < 0.3 m, 60.35 | 58.14 | 65.6 | INVALID / INVALID |
| mass | ok (no LOC) | none | 58.08 | 56.0 | FAIL / FAIL (item1, item2, item3) |
| sat (saturation) | ok (no LOC) | none | 58.84 | 44.5 | pass / pass |
| weak (weak motor) | ok (no LOC) | none | 0.00 (see below) | 46.0 | FAIL / FAIL (item3) |
| joint (all nominal except sat + weak) | LOC | tilt > 60 deg 0.5 s, 60.05 | 58.23 | 86.7 | INVALID / INVALID |

Fault time and max tilt for `weak`: `tilt.py` reported fault t 0.00 (no matching parameter write found), so 46.0 deg is the maximum over the whole flight (unverified as "after fault"; the saturation write should still occur). The fault time shifts to about 58.1 s in wind, vib, mass, gnss and about 58.2 s in joint (different anchor timing; cause not checked). Variant `mass` also keeps saturation scale 0.351 as drawn.

## Conclusion

- The LOC is removed by restoring saturation alone, weak motor alone, or mass alone (mass: no LOC, but keys FAIL items 1-3). Restoring any one of actc, delay, g1, inertia, tau, tel, wind, vib or gnss leaves the LOC.
- `joint` (everything nominal except saturation 0.351 and weak motor 3 at 0.709) still loses control (tilt > 60 deg, 60.05 s), so saturation plus weak motor alone reproduce the LOC on this draw.
- Not established by this table: why mass restoration helps (it was not isolated from the saturation scale being tied to mass in the draw, 0.27 x 1.3 = 0.351, which stays as drawn here; unverified), and whether the no-LOC flights of weak and mass would pass G3 (they fail key1/key2 items).
- Single runs per variant; no repeat for flight-to-flight variation was done.
