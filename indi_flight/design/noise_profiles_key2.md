# Key 2 review of noise_profiles.md (sources to numbers)

Verdicts: quiet ACCEPT WITH CHANGES (vibration wording and value), typical ACCEPT WITH CHANGES (relabel, keep 10), harsh ACCEPT WITH CHANGES (keep 27, fix its justification).
Datasheets re-read from the PDFs by this key (BMI270 bosch URL, ICM-42688-P chipdip copy, both as cited in S1/S3).

## 1. Value check
| value | result |
|---|---|
| ICM gyro 0.0028 dps/rtHz @10 Hz (S1) | CONFIRMED (icm.pdf Table 1, "Rate Noise Spectral Density"). 4.887e-5 rad/s/rtHz CONFIRMED (calc) |
| ICM accel 65 XY / 70 Z ug/rtHz | CONFIRMED (Table 2 PSD @10 Hz). 6.37e-4 / 6.86e-4 CONFIRMED (calc). Same table: 0.65/0.70 mg rms at 100 Hz BW |
| ICM ZRO +-0.5 dps, 0.005 dps/C; zero-g +-20 mg, 0.15 mg/C | CONFIRMED |
| BMI270 gyro 0.010 dps/rtHz normal, 0.007 perf | CONFIRMED (electrical table "Output Noise nG,nd", TA 25 C). 1.745e-4 / 1.222e-4 CONFIRMED |
| BMI270 accel 0.16 mg/rtHz, 8 g, normal | CONFIRMED. 1.569e-3 CONFIRMED |
| BMI270 zero-rate +-0.5 dps, TCO +-0.015 dps/K; zero-g +-20 mg, +-0.25 mg/K | CONFIRMED |
| BMI270 800 Hz rms 176 mdps (normal) | CONFIRMED (Table 11); accel 2.96 mg at 800 Hz (Table 8), consistent with 0.16 x sqrt(400)=3.2 mg |
| Bias instability both parts | UNVERIFIABLE (not a datasheet item), UNSOURCED label is correct |
| "typical = harsh density" | judgement, labelled as such; acceptable |
| PX4 "strong vibration" 2-3 m/s/s peak-to-peak (S4) | CONFIRMED at docs/en/log/flight_log_analysis.md:16. docs/en/assembly/vibration_isolation.md and flight_review.md give no numeric threshold |
| ArduPilot "below 15 normal, below 30 acceptable, above 60 problems" (S5) | DIFFERS in detail: page says healthy example "below 15 but occasionally peak to 30"; above 30 "may" have problems; above 60 "nearly always". Core numbers right. Vibe is the standard deviation (RMS) of the accel after a 5 Hz high-pass, per axis (https://ardupilot.org/copter/docs/common-measuring-vibration.html) |
| S6: 2.8 g peak near 300 Hz, 50 % thrust, Hurricane 51366 | UNVERIFIABLE (ADI page timed out twice for this key too). 2.8 g = 27.46 m/s^2 (calc OK) |
| S7 | UNVERIFIABLE (not opened) |

## 2. Vibration amplitudes (conversion used)
Sinusoid amplitude A: peak-to-peak = 2A, RMS = A/sqrt(2) = 0.707A.
- PX4 2-3 pk-pk is the onset of "strong", so A = 1.0-1.5. The note calls A=1.0 "the clean end": wrong reading, 1.0 is at the strong threshold (and real pk-pk of broadband noise is about 6 sigma, so the PX4 rule is even tighter on tonal content). Quiet 1.0 is therefore "good but not clean". Suggest quiet 0.5 (pk-pk 1, RMS 0.35), flagged judgement; keeping 1.0 is defensible only if relabelled "edge of PX4 strong".
- ArduPilot Vibe is RMS per axis, all frequencies. Typical A=10 gives RMS 7.1, under the "normal below 15" line: DEFENSIBLE as typical-healthy, still a judgement (no median exists). Harsh A=27 gives RMS 19.4, inside "acceptable below 30": DEFENSIBLE as harsh-but-flyable. The note's remark "27 just under acceptable below 30" compares an amplitude with an RMS metric and should be restated as RMS 19 (amplitude 30 RMS would be A=42, the ArduPilot ceiling; not recommended). Ceiling reference for stress: A=42.
- Frequency issue in S6: a 300 Hz peak at 50 % thrust on a 3-blade prop is about 3P (1P would be ~100 Hz), i.e. 27 is probably a blade-pass amplitude, not 1P. If so the 1P line at hover is not sourced by S6 at all. S8 (ArduPilot IMU batch sampling) only gives "motor peak with smaller second harmonic", which supports blade-pass < 1P qualitatively (ratio 0.5 is plausible, not sourced).
- No first-hand public numeric 5-inch FPV IMU vibration found in 2 searches (Betaflight/blackbox sources are figures or forum text). Be explicit that harsh rests on one unread second-hand number plus ArduPilot's RMS band.
- Also the per-rotor to net-IMU cancellation (limitation 4 in the note) means VIB_ACC values only mean something after a hover FFT trim, as the author says.

## 3. Arithmetic
- sigma/sqrt(400): gyro 8.7266e-4 -> 4.363e-5; accel 6.37e-3 -> 3.185e-4; 6.86e-3 -> 3.43e-4. All CONFIRMED. Assumes Nyquist noise bandwidth 400 Hz (white, per-sample); fine for a sim but real sensors filter, so density comparison is nominal.
- 159.0 Hz, 9539.7 rpm, 3P 477 Hz CONFIRMED. Alias at 800 Hz: 800-477 = 323 Hz CONFIRMED.
- NSC 4.0: gyro 4.363e-5 x 4 = 1.745e-4 (ratio 4.002) CONFIRMED; accel 3.185e-4 x 4 = 1.274e-3 (and 1.37e-3 on Z), vs 1.569e-3 = 81 % CONFIRMED (87 % on Z). NSC 5: gyro 2.18e-4 = +25 % CONFIRMED.
- Quiet: gyro 4.36e-5 vs 4.89e-5 is -11 %, note says "within 11 %" OK; accel 3.2e-4 vs 6.9e-4 = 46 % (about half) OK. Sim default is "IIM42653", not ICM-42688-P: the 4.89e-5 target is the same family, fine.
- NSC 4.0 vs 4.5 compromise: 4.5 gives gyro +12 %, accel 91 %; consider if accel fidelity matters more than gyro (judgement).

## Proposed table changes (only changed cells)
| item | quiet | typical | harsh |
|---|---|---|---|
| SIM_GZ_VIB_ACC target at IMU (sinusoid amplitude) | 0.5 (was 1.0), label "PX4 strong threshold = 1.0-1.5" | 10 (unchanged), add "RMS 7.1, ArduPilot normal band" | 27 (unchanged), add "RMS 19.4, ArduPilot acceptable band; S6 unverified, probably blade-pass" |
| 1P/blade-pass note | add: S6 peak at 300 Hz suggests blade-pass dominant; ratio unsourced | same | same |
| NSC | 1.0 | 4.0 (or 4.5, optional) | same |
Other edits: fix the "clean end" wording; state conversions A, pk-pk, RMS beside the table; re-read S6 before freezing.
