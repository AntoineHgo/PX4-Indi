# PX4 bidirectional DShot (BDShot) receive path: what reaches esc_status (session 27, read from this checkout)

Files: `src/drivers/dshot/DShot.cpp`, `src/drivers/dshot/DShot.h`,
`platforms/nuttx/src/px4/stm/stm32_common/dshot/dshot.c` (STM32; an NXP variant exists, not read).

## Rate and latency
- The DShot module uses `MixingOutput::SchedulingPolicy::Auto` (`DShot.h:153`): it runs once per `actuator_motors`
  update, i.e. at the rate-controller / allocator rate. Each `Run()` sends one frame (`up_dshot_trigger()`,
  `DShot.cpp:169`) and processes the telemetry captured since the previous `Run()` (`process_bdshot_telemetry()`,
  `DShot.cpp:98`). So one eRPM sample per output frame, and the value consumed at cycle k is the reply to frame k-1:
  **one output period of transport latency**, plus the ESC's own measurement age (AM32 averages one electrical
  revolution, `am32_erpm.md` sec. 2) and the turnaround (see `am32_erpm.md`, session 27 gap closure).
- `esc_status` is published in the same `Run()` when bdshot data was processed (`DShot.cpp:100-105`); the rate
  controller sees it at the latest one cycle later (it is not scheduled on esc_status).
- Default IMU_GYRO_RATEMAX (hence output rate) NOT verified in this session.

## Decode and resolution (`dshot.c:885-910`)
- 12-bit payload: 3-bit exponent, 9-bit mantissa, `period_us = mantissa << exponent`; `period == 65408 || 0` means
  stopped. `value = (600000 + period/2) / period`: an integer in **units of 100 eRPM** (rounded).
  `DShot.cpp:696`: `esc.erpm = erpm * 100`; `DShot.cpp:793/803`: `esc_rpm = erpm / (pole_count / 2)` with integer
  division; pole count from `DSHOT_MOT_POL<n>`, default 14 (`DShot.cpp:1026`).
- Two quantisations stack: the ESC's period (1 us steps below 512 us, 2^e us above) and PX4's 100-eRPM rounding.
  Example x500 hover ~7340 rpm, 14 poles: 51 400 eRPM, period ~1167 us -> exponent 2 (4 us steps, 0.34 %), then
  100 eRPM = 14.3 rpm (0.19 %).

## Errors and dropouts (`dshot.c:676-700`, `:995-1013`)
- A frame failing GCR/CRC increments `read_fail_crc` (reported by `up_bdshot_num_errors`) and is dropped.
  `_erpms[ch].ready` is NOT cleared, so `up_bdshot_get_erpm` keeps returning the **last good value**: a dropped frame
  is a held (one frame older) sample, and `esc_status.esc[i].timestamp` is still set to `now` (`DShot.cpp:674`).
  Staleness is therefore not visible in the timestamp; only `esc_errorcount`/the error counter changes.
- The channel goes offline only after more than `BDSHOT_OFFLINE_COUNT` = 200 consecutive failures (`dshot.c:144,684`),
  and back online after 200 consecutive successes. While offline, `esc_rpm` is not updated.

## Consequences for the SITL eRPM model and for INDI v2
- SITL model per output frame: true rotor speed -> age (one output period + ESC measurement age + turnaround) ->
  period quantisation (mantissa/exponent) -> 100-eRPM rounding -> integer rpm via poles/2 -> with probability p
  hold previous value (CRC drop). Offline only after 200 consecutive drops.
- INDI must not trust timestamps for staleness: detect frozen values (identical esc_rpm while the command moves) or
  use the error counter; the fallback to the onboard model triggers on the online flag (200 frames) or on that test.
