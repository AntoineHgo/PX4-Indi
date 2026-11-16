# A-20 (S33): origin of CAL_BARO0_OFF and the 0.72 m bias0 (logs only)

Script: `a20_cal_offset.py` (run from repo root). Scans the 30 g16_set_s32 ULogs.

**Source of CAL_BARO0_OFF.** Written by `VehicleAirData::BaroGNSSAltitudeOffset()`
(`src/modules/sensors/vehicle_air_data/VehicleAirData.cpp:521-602`), called only when
SENS_BARO_AUTOCAL, `cs_gps_hgt` and `!cs_in_air` hold (`:273-275`). Saved via `ParametersSave` (`:601`).
Param: `src/modules/sensors/module.yaml:201`.

**Offset values.** All nonzero values are integer multiples of 20000/8192 = 2.4414 Pa (max deviation 0):
the 13-halving bisection grid over [-10000, 10000] Pa (`:573-594`), not a fine estimate.

**When it is set (log time, s).**
- speed1 (log starts 13.1-13.6): in-flight change at 15.9-16.4 in 9 runs, start value 0.
- speed4 (log starts 20.8-21.8): nonzero already at logger start in 10 runs, no in-flight change.

**bias0 is not the offset.** r4 (-9.77 Pa) and traj r5 (-7.32 Pa): bias0 = +0.72 at t=20.30 s, which is
before log start and before the first sensor_baro (21.74 s). Corr(off0, bias0) = -0.66; the steady bias
does follow the offset: median bias 15-35 s = -0.625 and -0.431 m, corr(off0, median) = +0.81,
slope 0.065 m/Pa vs hydrostatic 1/(rho g) = 0.088 m/Pa (ISA T assumed). Ratio 0.67-0.73 (EKF attenuation not checked).

**Why it differs per run (hypothesis).** The offset is baro-vs-GNSS altitude residual at calibration:
mean baro (`:534`) vs one GNSS sample (`:535`). Its value depends on which samples are accumulated and
on log start vs calibration time. Also `GZBridge.cpp:912-914` latches `_alt_ref` from the first navsat fix,
which could shift the baro reference. Not verified numerically.

**Unverified:** sim time of the ParametersSave call (inferred from changed_parameters only); why 11 runs
stay at 0; temperature in the sim; sign convention (Correct = raw - offset, `Barometer.hpp:79`, consistent
with the data); whether a14 bias0 pass criterion is meaningful given the first-sample transient.
