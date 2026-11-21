# Noise profiles for G4 and the G5 re-fly (source note)

Rule: every number has a source id [S#] (list at the end) or is UNSOURCED with the reason. Arithmetic is marked "calc".
Reference airframe: 5-inch, ~600 g, hover 999 rad/s = 159 Hz (calc 999/2pi). Prop: the airframe data file says 3-blade
(`design/ref_airframe_data.md:11`), NOT 2-blade as GATES G4 assumed: blade-pass is 3 x 159 = 477 Hz, 2P (318 Hz) only if a
2-blade prop is chosen. Open point for the owner. Units: 1 dps = 0.017453 rad/s, 1 g = 9.80665 m/s^2.

## Datasheet choice
- quiet: ICM-42688-P, Rev 1.2 copy [S1] (the TDK page lists the same 2.8 mdps/rtHz and 70 ug/rtHz headline, current rev 1.8 [S2], not re-read).
- typical: BMI270 [S3], because it is the datasheet that could be downloaded and read here. The ICM-20602 datasheet URLs returned 404/HTML, so
  ICM-20602 is UNSOURCED. Density is at the datasheet condition (normal mode, 25 C), not at 160 Hz.
- harsh: typical density (no public source gives a worse in-flight white-noise floor). Harshness comes from vibration only.

## Profile tables (density and bias)
| item | quiet (ICM-42688-P) | typical = harsh (BMI270, normal mode) |
|---|---|---|
| gyro noise density | 2.8 mdps/rtHz = 4.89e-5 rad/s/rtHz [S1 Table 1, "Rate Noise Spectral Density @10 Hz" 0.0028 dps/rtHz, LN mode; headline p.1] | 0.010 dps/rtHz = 1.745e-4 rad/s/rtHz [S3 gyro table "Output Noise nG,nd", normal mode]; performance mode 0.007 = 1.22e-4 |
| accel noise density | 70 ug/rtHz Z, 65 XY = 6.86e-4 / 6.37e-4 m/s^2/rtHz [S1 Table 2, "Power Spectral Density @10 Hz"] | 0.16 mg/rtHz = 1.569e-3 m/s^2/rtHz [S3 accel table "Output Noise nA,nd", normal mode, 8 g range] |
| gyro bias instability | UNSOURCED: not in the datasheet (only ZRO tolerance +-0.5 dps, +-0.005 dps/C [S1 Table 1]) | UNSOURCED: not in the datasheet (only zero-rate offset +-0.5 dps, TCO +-0.015 dps/K [S3]) |
| accel bias instability | UNSOURCED: not given (zero-g +-20 mg, +-0.15 mg/C [S1 Table 2]) | UNSOURCED: not given (zero-g +-20 mg, +-0.25 mg/K [S3]) |

Cross-check with the sim default (below): sim gyro 4.36e-5 rad/s/rtHz is within 11 % of the ICM-42688-P value; sim accel 3.2e-4 is
about half the datasheet 6.4e-4 to 6.9e-4.

## Vibration at the IMU (accel amplitude, m/s^2; frequency lines at 159 Hz and its blade-pass)
No log population is public in numeric form, so percentiles cannot be computed. The three levels are anchors from the sources
below, not percentiles. This is stated in the note and must be repeated wherever the profiles are quoted.

| item | quiet | typical | harsh |
|---|---|---|---|
| accel line amplitude at 159 Hz (1P) and blade-pass | 1.0 m/s^2 | 10 m/s^2 | 27 m/s^2 |
| how the anchor was set | [S4]: PX4 "strong vibration" starts at 2-3 m/s^2 peak-to-peak, so 1.0 m/s^2 amplitude (2 pk-pk) is the clean end (calc). Matches the GATES draft x1 | Between [S4] and [S5] "normal below 15 m/s/s": 10 m/s^2 is a judgement value, NOT sourced as a median (UNSOURCED as a percentile) | [S6]: 2.8 g peak near 300 Hz at 50 % thrust on a 5-inch quad with 3-blade Hurricane 51366 = 27 m/s^2 (calc); also just under [S5] "acceptable below 30 m/s/s" |
| blade-pass amplitude | UNSOURCED split: no source gives the 1P versus blade-pass ratio. Sim hook fixes 2P = 0.5 x 1P (project choice, not a source) | same | same |
| gyro vibration amplitude (rad/s) | UNSOURCED: no public numeric gyro vibration amplitude was found for 5-inch quads ([S6] says gyro error depends on the mechanical design, gives no amplitude; the hover noise spectra in [S7] are figures only) | UNSOURCED | UNSOURCED |

Frequency anchors: ArduPilot shows a motor peak at 180 Hz in hover on a 5-inch quad with a smaller second harmonic [S8]; [S8] also says
vibration above 100 Hz may cause attitude control problems. Note that [S5] Vibe values are the ArduPilot log metric, not a single
sine amplitude, and its examples are for a larger frame: use it as order of magnitude only. The [S6] figure was taken from a web
search summary; the page itself timed out twice, so re-read it before freezing.

## Mapping to the simulator hooks
Sim default IMU: `indi_flight/sim/staged/quad5in_base_model_a14.sdf:175-221`, 800 Hz, "modelled after IIM42653", gyro stddev 8.7266e-4 rad/s
per sample, accel 6.37e-3 / 6.37e-3 / 6.86e-3 m/s^2. Density equivalent = sigma/sqrt(400 Hz): gyro 4.36e-5 rad/s/rtHz, accel 3.2e-4 / 3.4e-4 (calc).
Hooks (`src/modules/simulation/gz_bridge/module.yaml:186-235`, `GZBridge.cpp:685-702`): SIM_GZ_IMU_NSC (1..10, one factor on total
stddev for gyro AND accel), SIM_GZ_VIB_ACC (m/s^2 per rotor), SIM_GZ_VIB_GYR (rad/s per rotor), SIM_GZ_VIB_RPM (rpm where the
amplitudes apply, scaling with speed squared), SIM_GZ_SEED. Set SIM_GZ_VIB_RPM = 9540 (999 rad/s, calc) so amplitudes are hover values.

| param | quiet | typical | harsh |
|---|---|---|---|
| SIM_GZ_IMU_NSC | 1.0 (gyro 4.36e-5 vs 4.89e-5 target, accel 3.2e-4 vs 6.9e-4 target: accel is 2x too quiet, cannot be raised without raising gyro) | 4.0 gives gyro 1.75e-4 (on target, calc 1.745e-4/4.36e-5 = 4.0); accel then 1.27e-3 vs 1.57e-3 target (81 %). 5.0 would match accel but gives gyro 2.2e-4 (25 % high) | same as typical |
| SIM_GZ_VIB_ACC | 1.0 (see caveat below) | 10 | 27 |
| SIM_GZ_VIB_GYR | UNSOURCED, leave 0 | UNSOURCED, leave 0 | UNSOURCED, leave 0 |
| SIM_GZ_VIB_RPM | 9540 | 9540 | 9540 |

## What the hooks cannot express (code reading, unverified by a run)
1. One noise factor for gyro and accel: the accel density cannot be set independently (the "accel scale UNVERIFIED" note in STATE.md stays open; the factor is applied per the yaml text, no run checked it).
2. NSC >= 1 only: noise below the SDF level is impossible. Quiet gyro (4.89e-5) is 12 % above the SDF; quiet accel target is 2x above it.
3. Blade-pass is hard-coded as 2P (2 blades) on the thrust axis at 0.5 x 1P; the 3-blade reference prop (477 Hz, aliases to 323 Hz at the 800 Hz IMU rate) cannot be set. Gyro 2P is 0.2 x. Amplitude ratios are fixed.
4. Four rotors are given phase offsets of i x pi/2. At equal rotor speeds the 1P terms and the 2P terms of the four rotors sum to zero (cos/sin of phase + i pi/2 cancel; 2P alternates sign). The net IMU line is non-zero only when rotor speeds differ (phases drift, beating). So "per rotor amplitude" is not the amplitude seen at the IMU: the net level must be measured in a hover run (FFT of the logged accel at 159 Hz) and VIB_ACC trimmed to hit 1 / 10 / 27 m/s^2 at the IMU.
5. Vibration is added to IMU 0 only, needs SIM_GZ_ESC_FB 1 or 2, and has no broadband (non-tonal) vibration or frame resonance, no gyro-accel cross-coupling, no bias drift (bias instability UNSOURCED anyway), and no ESC/motor noise beyond what the rotor model gives.

## Gaps (to close before freezing the profiles)
- ICM-20602 datasheet not retrievable (404); typical uses BMI270. Re-read ICM-42688-P at the current rev 1.8 (copy used is rev 1.2).
- Bias instability for both parts: UNSOURCED (not a datasheet item; an Allan-variance measurement would be needed).
- Gyro vibration amplitude in rad/s: UNSOURCED.
- Typical (10 m/s^2) is a judgement value; no public log population gives a 50th or 99th percentile. Harsh 27 m/s^2 rests on one measurement [S6].
- Prop blade count conflict (2 versus 3) and the 1P versus blade-pass ratio.
- The accel line amplitude is "amplitude of one tone" for [S4] (converted from pk-pk) but is a metric (RMS-like) in [S5]: not the same quantity.

## Sources
- [S1] ICM-42688-P Datasheet, DS-000347 Rev 1.2, copy at https://static.chipdip.ru/lib/617/DOC014617647.pdf, Section 3.1 Table 1 (gyro), Section 3.2 Table 2 (accel), p.1 features. Read from the PDF text.
- [S2] https://invensense.tdk.com/products/icm-42688-p/ (product page, via search result; headline numbers only).
- [S3] BMI270 Datasheet rev 1.6, https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf, electrical characteristics accel and gyro tables (Output Noise rows). Read from the PDF text. Tables 8, 11, 12 give RMS noise per ODR (800 Hz gyro normal 176 mdps rms) as a cross-check.
- [S4] This repo, `docs/en/log/flight_log_analysis.md:16`.
- [S5] https://ardupilot.org/copter/docs/common-measuring-vibration.html (below 15 normal, below 30 acceptable, above 60 problems; clipping under 100 ok).
- [S6] https://www.analog.com/en/resources/technical-articles/vibration-effects-drone-imus.html (GEPRC Mark 5, Hurricane 51366, 2.8 g peak near 300 Hz at 50 % thrust). Second-hand via web search summary, page fetch timed out.
- [S7] https://arxiv.org/pdf/2605.05483 (INDI quad gyro noise spectra, 3-inch and TinyWhoop; figures only, not read in full).
- [S8] https://ardupilot.org/copter/docs/common-imu-batchsampling.html (180 Hz motor peak in hover, 5-inch quad; above 100 Hz may cause attitude problems).
- Repo: `indi_flight/GATES.md:307-348`, `indi_flight/sim/staged/quad5in_base_model_a14.sdf:175-221`, `src/modules/simulation/gz_bridge/module.yaml:183-235`, `GZBridge.cpp:685-702`, `indi_flight/design/ref_airframe_data.md:11`.
