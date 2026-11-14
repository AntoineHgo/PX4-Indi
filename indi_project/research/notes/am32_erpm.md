# AM32 bidirectional DShot eRPM telemetry: sourced facts

Sourced by reading code/docs in the shallow clone
`indi_project/research/raw/am32/AM32` (HEAD 077b6a49852a1d5642d89ccc4d1259cb8e3802dd,
commit date 2026-11-09). Source URLs use the upstream GitHub path at that commit.
Nothing below comes from memory; "NOT FOUND" means not found in the sources opened.

Base URL for code: https://github.com/am32-firmware/AM32/blob/077b6a49852a1d5642d89ccc4d1259cb8e3802dd/

## Source log (append as read)

- [S1] `Src/dshot.c` lines 18-23 (gcr_encode_table), 25-32 (telem scheduler), 40-42 (EDT divisors), 72-110 (computeDshotDMA: frame timing, CRC, telemetry request bit), 242-346 (make_dshot_package: period encoding, checksum, GCR).

## 1. eRPM frame format

Facts from S1:
- Input DShot frame is 16 bits. `dpulse[0..15]` are decoded from a DMA capture of pulse widths (`dshot.c:81-82`). `dpulse[11]` is the telemetry request bit (`dshot.c:107-108`: if set, `send_telemetry = 1`). The 4-bit CRC is `dpulse[12..15]` (`dshot.c:85`). Data is `dpulse[0..10]` (11 bits), built as `tocheck` at `dshot.c:102`. Input CRC check: `dshot.c:84`, `(d0^d4^d8)<<3 | (d1^d5^d9)<<2 | (d2^d6^d10)<<1 | (d3^d7^d11)`. The bit-11 request is included in the CRC, so the check uses only nibble XORs.
- Telemetry frame (AM32 -> ESC direction, sent on the signal line) is built in `make_dshot_package` (`dshot.c:242-346`):
  - 12-bit payload: `shift_amount` is 3 bits (`eee`), `com_time >> shift_amount` is 9 bits (`mmm mmm mmm`). Comment at `dshot.c:287-290`: "eee mmm mmm mmm", "allows for a range of up to 65408 microseconds ... shifted 0b111 (eee) or 7 times." Encoding at `dshot.c:291-301`: `shift_amount = i + 1 - 9` for the first i in [15..9] with `com_time >> i == 1`; `dshot_full_number = (shift_amount << 9) | (com_time >> shift_amount)`.
  - Field units: `com_time` is passed as a `uint16_t` parameter named `com_time` with a microsecond comment at `dshot.c:290`. The microsecond unit is stated in the code comment; no other unit conversion is visible in this function.
  - Checksum: 4-bit nibble XOR of the 12-bit value, inverted, masked to 4 bits (`dshot.c:304-311`), appended as `(dshot_full_number << 4) | csum` (`dshot.c:313`). 16-bit total.
  - GCR: 4-bit nibbles mapped via `gcr_encode_table` (`dshot.c:20-23`, values 0b11001 ... 0b01111, i.e. 5-bit GCR code per nibble). 16 bits -> 20 bits (`dshot.c:317-320`). Then the 20-bit value is converted to 21 output bits by a differential XOR chain (`dshot.c:322-345`; the `#else` branch at `dshot.c:339-344` is the path used on the F4/F4-class MCUs that are not F051/F031/CH32V203/NXP; the MCU_F051 branch at `dshot.c:322-329` uses 64 instead of 128).
  - `make_dshot_package` sets `com_time = 65535` when `!running` (`dshot.c:284-286`).
- Telemetry period is in microseconds (per the comment). Verify the GCR bit-rate and frame layout against the DMA setup before relying on it (see section 2 TODO).
- Resolution / quantisation formula: NOT YET DERIVED (see section 1 summary below).
- Note: `kiss_telemetry.c:27-29` (KISS serial telemetry, not DShot) states "eRPM * 100, so 1 in the packet means 100 eRPM" with a 16-bit field. That is the KISS serial path, not the bidirectional DShot path. Do not mix them up.

- [S2] `Src/main.c` 2088 (e_com_time = (sum of 6 commutation_intervals + 4) >> 1, comment "COMMUTATION INTERVAL IS 0.5US INCREMENTS"), 2378-2379 (e_rpm = running*(600000/e_com_time); comment "ecom time is time for one electrical revolution in microseconds"), 1063 and 1784 (commutation_interval filters), 2216 (average_interval = e_com_time/3), 1751-1755 (processDshot: make_dshot_package(e_com_time), clamped to 65535), 1337/2023 (target_e_com_time from motor_poles). Sourced at https://github.com/am32-firmware/AM32/blob/077b6a49852a1d5642d89ccc4d1259cb8e3802dd/Src/main.c
- [S3] `Src/signal.c` 118-150 (transfercomplete: when dshot_telemetry and out_put, make_dshot_package(e_com_time) then computeDshotDMA, receiveDshotDma; otherwise sendDshotDma), 150-176 (dshot receive path, frametime window from average packet length). https://github.com/am32-firmware/AM32/blob/077b6a49852a1d5642d89ccc4d1259cb8e3802dd/Src/signal.c

## 1. eRPM frame format (continued, verified)

- The value sent in the eRPM telemetry frame is `e_com_time` (`dshot.c:242` parameter `com_time`, called with `e_com_time` at `main.c:1754` / `signal.c:142`). Per `main.c:2379` it is the time for ONE ELECTRICAL REVOLUTION in microseconds. So the frame carries the electrical PERIOD in µs, not eRPM. The receiver must compute eRPM = 60e6 / period_us (this follows directly from the definition; eRPM = electrical revs per minute).
- Period frame encoding (from `dshot.c:291-301`), with P = period in µs, i = floor(log2 P):
  - P < 512 (no bit 9..15 set): shift = 0; the 9-bit mantissa is P itself. Step = 1 µs.
  - 512 <= P <= 65535: shift = i - 8 (for i in 9..15), mantissa = P >> shift (9 significant bits, MSB at bit 8). Step = 2^shift µs.
  - Step values: [512,1024) -> 2 µs; [1024,2048) -> 4 µs; [2048,4096) -> 8 µs; ... [32768,65536) -> 128 µs.
  - Equivalent: step in (P/512, P/256] for P >= 512. Relative resolution dP/P between 1/512 and 1/256 (0.2% to 0.4%).
  - Max representable period: 511 << 7 = 65408 µs (matches the code comment at `dshot.c:289-290`). Above that, `processDshot` clamps to 65535 (`main.c:1751-1752`).
- eRPM quantisation: dERPM = eRPM * dP / P, so the eRPM step is proportional to eRPM. Relative resolution 1/512 to 1/256 (0.2 to 0.4%) for P >= 512 µs; below 512 µs it is 1/P (coarser relatively at high speed, since P is 1 µs steps). Absolute eRPM step is therefore ~ eRPM * 2^-8 to eRPM * 2^-9 (sawtooth within each octave of period).
- The eRPM unit in AM32 code (`main.c:2378`): e_rpm = 600000/e_com_time = (60e6/e_com_time)/100, i.e. e_rpm is in units of 100 eRPM. The code comment "in tens of rpm" at `main.c:2378` is inconsistent with this arithmetic; other comments say hundreds (`main.c:540`, `main.c:2497`, `Src/DroneCAN`/kiss `kiss_telemetry.c:27`). I follow the arithmetic, and flag the comment as contradictory.

## 2. Measurement (partial)
- `e_com_time` is the sum of six commutation intervals, halved (`main.c:2088`): i.e. the period of one electrical revolution averaged over 6 commutation steps (one full electrical cycle). Units: commutation_intervals in 0.5 µs ticks, sum >> 1 -> µs.
- `commutation_interval` is a first-order filter updated at each commutation: `main.c:1063` commutation_interval = (commutation_interval + ((lastzctime+thiszctime)>>1)) >> 1; and `main.c:1784` commutation_interval = (thiszctime + 3*commutation_interval)/4.
- Still open: when `commutation_intervals[]` is written (ISR or main loop), the turnaround delay between DShot frame end and telemetry frame start, and the frame's exact timing. TODO next.

- [S4] PX4 `src/drivers/dshot/DShotTelemetry.cpp` 325-352 (UART telemetry frame parser: 10-byte frame, byte 7-8 eRPM big-endian in [100ERPM], byte 9 CRC8, line 333 CRC8 over bytes 0..8, line 342 erpm = (b7<<8)|b8, line 344 timestamp = hrt_absolute_time(), line 348 erpm*100). Note: this is the serial/UART telemetry path, not the bidirectional DShot path. https://github.com/PX4/PX4-Autopilot/blob/main/src/drivers/dshot/DShotTelemetry.cpp
- [S5] PX4 `src/drivers/dshot/DShot.cpp` 97-106 (publishes esc_status with timestamp, esc_count, counter), 646 (process_bdshot_telemetry), 693-703 (BDShot eRPM via up_bdshot_get_erpm, esc.erpm = erpm*100; otherwise esc_rpm * pole_count/2), 785 (esc_errorcount aggregation), 793 and 803 (esc_rpm = esc.erpm / (pole_count/2)). https://github.com/PX4/PX4-Autopilot/blob/main/src/drivers/dshot/DShot.cpp
- [S6] PX4 docs `docs/en/peripherals/dshot.md` 56-75 (serial telemetry; DSHOT_TEL_CFG; DSHOT_MOT_POL1-12 pole count, line 75), 83-90 (Bidirectional DShot: eRPM telemetry on the signal wire, PX4 v1.16 badge, line 87-88). https://github.com/PX4/PX4-Autopilot/blob/main/docs/en/peripherals/dshot.md
- [S7] AM32 `Src/main.c` 809-813, 1337, 2023, 2491: uses eepromBuffer.motor_poles; default value NOT FOUND in the lines opened (the eeprom default table was not read). `Inc/eeprom.h:38` declares `uint8_t motor_poles; // 27`.

## 1. eRPM frame format: PX4 side and AM32 units (verified)
- AM32 sends period (µs per electrical revolution), 16-bit eRPM is NOT on the wire. The 100-ERPM unit is an AM32 UART telemetry convention (`kiss_telemetry.c:27`) and PX4 reads it at `DShotTelemetry.cpp:340-348` with the comment "[100ERPM]". For bidirectional DShot, PX4 takes eRPM from `up_bdshot_get_erpm` (`DShot.cpp:695-696`), so the decoding of the 12-bit period is done in the PX4 BDShot driver. That decoding is NOT in the AM32 clone and was NOT opened: NOT FOUND for the PX4 BDShot decode (`up_bdshot_get_erpm` is in the PX4 stm32h7 driver, not read).
- GCR per nibble and CRC: from S1 (dshot.c:20-23, 84-85, 310-313). Exact bit timing of the telemetry bit cell: NOT FOUND in the lines opened.

## 2. Measurement and timing (partial, verified)
- Period = mean of six commutation intervals (main.c:2088), i.e. one electrical revolution, updated once per electrical revolution in the main-loop/zero-cross path (the enclosing function was not read: its call frequency is NOT FOUND).
- Each commutation-interval sample at main.c:920 (`commutation_intervals[step-1] = commutation_interval`), filtered by main.c:1063 and 1784.
- Turnaround delay (µs, from DShot frame end to telemetry frame start): NOT FOUND. Only lead: `Src/main.c:28` changelog "add 28us delay for dshot300" and `main.c:186` "Fix dshot telemetry delay f4 and e230 mcu"; these are changelog lines, not the implementation constant. Not verified.

## 4. Frame rate and PX4 esc_status (verified)
- Telemetry is one frame per DShot command request bit (dshot.c:107-108 sets send_telemetry from bit 11). So frame rate = DShot output rate. PX4's DShot output rate: NOT FOUND in this session (not read; `module.yaml` grep returned no definitions in the form searched).
- esc_status fields written: esc_rpm (mechanical rpm = erpm/(pole_count/2), DShot.cpp:793/803), esc_errorcount (DShot.cpp:785), esc[].timestamp (DShot.cpp:791/801, from esc.timestamp, DShotTelemetry.cpp:344), esc_status.timestamp and counter (DShot.cpp:103-105).
- CRC errors in PX4: DShotTelemetry.cpp:333-346 counts checksum mismatch only in the UART path; the error counter aggregation is at DShot.cpp:785 (other term not read). NOT FOUND for the BDShot CRC error counter.
- DSHOT_BIDIR_EDT, DSHOT_MOT_POL default and DSHOT_TEL_CFG parameter definitions: NOT FOUND in `src/drivers/dshot/module.yaml` as searched (grep matched only DSHOT_* lines with other keys). Names in docs: DSHOT_TEL_CFG, DSHOT_MOT_POL1-12 (dshot.md:72,75).
- [S8] WebFetch https://betaflight.com/docs/wiki/guides/current/RPM-Filter: HTTP 404, not read.
- [S9] WebFetch https://betaflight.com/docs/wiki/guides/current/Bidirectional-DShot: HTTP 404, not read.

## Correction to S1 notes
- The line "used on the F4/F4-class MCUs" in section 1 is an inference, not sourced. The `#else` branch at `dshot.c:338-344` is the generic path for MCUs not listed in the `#if` at `dshot.c:322`. Which MCUs take it was NOT verified.

## 3. Motor pole count
- eRPM vs mechanical rpm: from `main.c:1337` and `main.c:2023`, target_e_com_time = 60000000 / rpm / (motor_poles/2). Inverting: eRPM = rpm * (poles/2), i.e. mech_rpm = eRPM / (poles/2). Source: https://github.com/am32-firmware/AM32/blob/077b6a49852a1d5642d89ccc4d1259cb8e3802dd/Src/main.c
- PX4 uses the same relation: `DShot.cpp:793` and `803`: esc_rpm = esc.erpm / (pole_count/2). https://github.com/PX4/PX4-Autopilot/blob/main/src/drivers/dshot/DShot.cpp
- PX4 parameter: DSHOT_MOT_POL1 to DSHOT_MOT_POL12 (per-motor pole count), documented at `docs/en/peripherals/dshot.md:75`. Its default: NOT FOUND (module.yaml grep did not return the definition).
- AM32 default motor_poles: NOT FOUND in lines opened. (`Inc/eeprom.h:38` only declares it.)
- Typical pole count for 5-10 inch motors: NOT FOUND in any source opened in this session.

## 5. Frame loss / CRC error rates
- Betaflight RPM-Filter and Bidirectional-DShot pages: both HTTP 404 (S8, S9). Not read.
- PX4 `docs/en/peripherals/dshot.md` (lines 56-106 read in part): no CRC error or frame loss rate stated. NOT FOUND.
- PX4 code: `DShotTelemetry.cpp:333-346` CRC check on UART telemetry; `DShotTelemetry.cpp:406` prints "CRC errors: %i" (count only, no rate). No rate is computed in the opened lines.

## 1 (quantisation formula, final)
- Period P (µs), i = floor(log2 P). Step Δ(P):
  - P < 512: Δ = 1 µs (shift 0).
  - 512 <= P <= 65535: Δ = 2^(i-8) µs; equivalently Δ in (P/512, P/256].
  - Max representable period 65408 µs (511 << 7), clamped above (main.c:1751-1752).
- eRPM = 60e6 / P. Step in eRPM: dERPM = eRPM * ΔP / P, so the relative step is 1/512 to 1/256 (0.20 to 0.39 %) for P >= 512 µs, and 1/P for P < 512 µs.
- Check on the premise "coarser at high rpm": absolute eRPM step scales with eRPM, so the absolute step grows with speed. The relative step is bounded by 0.2 to 0.4 % for periods of at least 512 µs. Below 512 µs (roughly, the top of the speed range) the relative step grows as 1/P.

## Summary for the simulator model
| Parameter | Value | Source |
|---|---|---|
| Frame payload | 12 bits: 3-bit shift + 9-bit mantissa, plus 4-bit nibble-XOR checksum, 16 bits total, then GCR-encoded | dshot.c:291-313 |
| Period step Δ(P) | 1 µs for P<512; 2^(floor(log2 P)-8) µs for P>=512 | dshot.c:291-301 |
| Max period | 65408 µs (511<<7), clamp 65535 | dshot.c:289-290; main.c:1751-1752 |
| Telemetry content | e_com_time = µs per electrical revolution | main.c:2379; main.c:1754; signal.c:142 |
| eRPM units (AM32 internal) | e_rpm = eRPM/100 | main.c:2378 (arithmetic) |
| Period averaging | mean of 6 commutation intervals (÷2 of sum at 0.5 µs ticks) | main.c:2088 |
| Commutation filter | c = (c + (lastzc+thiszc)/2)/2; c = (thiszc + 3c)/4 | main.c:1063; main.c:1784 |
| eRPM vs rpm | eRPM = rpm * poles/2 | main.c:1337, 2023 |
| PX4 mech rpm | esc_rpm = erpm / (pole_count/2) | DShot.cpp:793, 803 |
| PX4 pole param | DSHOT_MOT_POL1-12 | docs dshot.md:75 |
| Frame rate | one telemetry frame per DShot command (request bit 11) | dshot.c:107-108 |
| Turnaround delay | NOT FOUND | - |
| Motor pole default (AM32) | NOT FOUND | - |
| Typical pole count, 5-10 inch | NOT FOUND | - |
| PX4 DShot output rate | NOT FOUND | - |
| CRC error rate in practice | NOT FOUND | - |

## Session 27 gap closure

Same clone and base URL as above (HEAD 077b6a49852a1d5642d89ccc4d1259cb8e3802dd). Files are under `Src/`, `Mcu/`, `Inc/` of the clone.

### Q1. Turnaround delay (DShot frame end -> telemetry frame start) and telemetry bit cell

- Turnaround as a fixed constant: NOT FOUND. No µs delay constant exists in the telemetry send path. The telemetry send is started directly from the DMA transfer-complete path, with no software delay:
  - `Mcu/f051/Src/IO.c:21-56`, `receiveDshotDma()` / `sendDshotDma()`; the TC handler `Mcu/f051/Src/stm32f0xx_it.c:111-116` reads `if (out_put) { receiveDshotDma(); compute_dshot_flag = 2; } else { sendDshotDma(); compute_dshot_flag = 1; }`.
  - `Mcu/g431/Src/stm32g4xx_it.c:88-91` calls `transfercomplete();`, and `Src/signal.c:121-127` holds the armed+bidir branch that makes the same out_put choice.
- "28" in code: only in the changelog, `Src/main.c:28` ("add 28us delay for dshot300") and `Src/main.c:186` ("Fix dshot telemetry delay f4 and e230 mcu"). These are changelog text, not an implementation constant. Not used as a value.
- The main leading delay is `buffer_padding`: `Src/signal.c:212` sets `buffer_padding = 14` (DShot branch 1) and `Src/signal.c:224` sets `buffer_padding = 7` (branch 2). The GCR buffer is built with `gcr[buffer_padding] = 0` (`Src/dshot.c:329`, `:344`), and the DMA sends `23 + buffer_padding` entries from `gcr[0]` (`Mcu/f051/Src/IO.c:77`, `:87`; `Mcu/g431/Src/IO.c:71`). So the first `buffer_padding` entries are low, i.e. a leading delay of `buffer_padding` output-timer cells before the first telemetry bit. Interpretation (derived from code, not measured).
- Telemetry bit cell (one GCR entry = one output-timer update period): `cell = (ARR + 1) * (PSC + 1) / f_tim`, where
  - G431: `ARR = 108` (`Mcu/g431/Src/IO.c:65`), `PSC = output_timer_prescaler` (`Mcu/g431/Src/IO.c:64`).
  - F051: `ARR = 61` (`Mcu/f051/Src/IO.c:71`), `PSC = output_timer_prescaler` (`Mcu/f051/Src/IO.c:70`).
  - `output_timer_prescaler` values: `Src/signal.c:206` (=1 if CPU_FREQUENCY_MHZ > 100 else `:208` =0) for branch 1; `Src/signal.c:220` (=3 if > 100 else `:222` =1) for branch 2.
  - Relation: branch 2 cell = 2x branch 1 cell (PSC 3 vs 1, same ARR). Absolute µs NOT computed: f_tim (timer clock vs CPU_FREQUENCY_MHZ on the G431 target) was NOT verified.
- Telemetry bit rate relative to DShot rate: NOT FOUND as a ratio. The DShot input rate was not derived from the code. No 5/4 or similar factor found in the lines read.
- Caveat: the receive DMA completes after `buffersize = 32` captures (`Src/signal.c:27`, `:213`, `:225`), i.e. at the last captured edge of the input frame. Frame-end reference point is inferred from this, not measured.

### Q2. How often the period value is updated

- Source value: `e_com_time` is recomputed on every main-loop iteration: `Src/main.c:2088` (inside `while (1)` at `Src/main.c:2087`), as the sum of six `commutation_intervals[]` halved, mean over one electrical revolution. `commutation_intervals[]` is written at each commutation (`Src/main.c:920`, from the prior note).
- Build of the telemetry buffer: `make_dshot_package(e_com_time)` is called from:
  - `processDshot()` at `Src/main.c:1754` (or `make_dshot_package(65535)` at `:1752` when `e_com_time > 65535`), only when `compute_dshot_flag == 2` (`Src/main.c:1744-1756`);
  - `Src/signal.c:142` (the non-armed `dshot_telemetry` branch, not the armed path).
- Who calls `processDshot()`: G431 `EXTI15_10_IRQHandler` at `Mcu/g431/Src/stm32g4xx_it.c:133-136`; F051 `EXTI4_15_IRQHandler` at `Mcu/f051/Src/stm32f0xx_it.c:310-313`; main loop at `Src/main.c:2102` only under `#ifdef NEED_INPUT_READY` with `input_ready` (`Src/main.c:2098-2104`). `EXTI->SWIER ... LINE_15` is set at the end of each DMA TC handler, which triggers that EXTI ISR.
- Trigger: `compute_dshot_flag = 2` is set in the TC handler when `out_put` is 1, i.e. after each telemetry transmission completes (`Mcu/f051/Src/stm32f0xx_it.c:111-116`, `Src/signal.c:121-130`).
- Resulting rate: the period is rebuilt once per DShot frame cycle (one receive plus one send), not per electrical revolution and not per main loop. Per cycle, the send is started with the buffer built at the end of the previous send (derived from control flow, not measured). The sampled value is therefore aged by about one DShot frame interval (the wait for the next input frame, plus a frame length). Derived, not measured.
- CORRECTION to the section 4 claim above ("one telemetry frame per DShot command request bit, dshot.c:107-108"): in the armed bidir branch, `Src/signal.c:121-127` sends a telemetry frame on every cycle with no check of `send_telemetry`. `send_telemetry` (set at `Src/dshot.c:107-108` from bit 11) only gates the serial telemetry path (`Src/main.c:2260`). So the per-frame rate follows the DShot cycle, not the request bit. Read the code to confirm before modelling; this contradicts the earlier note.

### Q3. AM32 default motor_poles

- Value: 14 poles (7 pole pairs). Source: `Src/DroneCAN/DroneCAN.c:343-347`, `static const uint8_t default_settings[]`. Comment at `:340`: "default settings, based on public/assets/eeprom_default.bin in AM32 configurator / update to 2.19 default". Index 27 (0-based) = `0x0e` = 14.
- Offset check (verified in the code): `Inc/eeprom.h:30-40` labels fields with byte offsets (`pwm_frequency; // 24`, `motor_kv; // 26`, `motor_poles; // 27`). Index 24 of the same array = `0x18` = 24, matching the pwm_frequency offset label; index 26 = `0x37` (motor_kv), index 27 = `0x0e` = 14.
- Cross-check: DroneCAN parameter default `Src/DroneCAN/DroneCAN.c:157`: `{ "MOTOR_POLES", T_UINT8, 2, 64, 14, &eepromBuffer.motor_poles}` (min 2, max 64, default 14). Same value.
- NOT FOUND: the `eeprom_default.bin` file (the array's stated origin) is not in the clone (`find` for `eeprom_default*` returned nothing). `Src/main.c:275-348` (the "Defaults" block) contains no `motor_poles` entry. The DroneCAN build conditional around `default_settings` was not checked, so the table may apply only to DroneCAN builds.
- Usage: `Src/main.c:812-813`, `:1337`, `:2023`, `:2491`: eRPM = mech_rpm * (motor_poles/2).


### Q4. Typical bidirectional DShot error / dropped-frame rates (web, secondhand)

- Official Betaflight pages: `https://betaflight.com/docs/development/Dshot` returned HTTP 404 (WebFetch). `https://betaflight.com/docs/wiki/guides/current/RPM-Filter` and `.../Bidirectional-DShot` returned 404 earlier (S8, S9). Not read.
- Search (WebSearch, standard mode) did not return official `dshot_telemetry_info` documentation or an error-percentage definition from Betaflight. Secondhand forum figures only:
  - IntoFPV (`https://intofpv.com/archive/index.php/thread-25242.html`, also `https://intofpv.com/t-bidirectional-dshot-errors-when-transmitter-on`): the "E" field is the DShot telemetry error rate; quote: "A powered ESC should show 0% or very close to 0% errors."
  - IntoFPV (`https://intofpv.com/t-bidirectional-dshot-errors-when-transmitter-on`): with BlueJay on Betaflight 4.4, quote: "The error percentage fluctuate between 0% and 0.3% when my transmitter is off. The error rate should be 0." Rate reported about 5% at 4 kHz PID on that setup (single user).
  - IntoFPV (same search, separate thread): one user reports about 2-3% error at DShot600 during motor spin-up, and no errors after switching to DShot300 (single user).
  - ArduPilot forum (`https://discuss.ardupilot.org/t/esc-errors-on-logs-and-what-can-i-do-to-reduce-the-errors/145157`): one user puts the abnormal line at 1%, "anything over 1%". Forum opinion, not a spec.
- Rotorflight wiki (`https://github.com/rotorflight/rotorflight/wiki/Bidirectional-DSHOT`, a Betaflight fork, not Betaflight): ESC firmware 32.7.0 or later stated for full support. Secondhand, search snippet only.
- Assessment: the only quantitative figures are single-user forum reports (0 to 0.3% idle with transmitter off, 2-3% at DShot600 spin-up, about 5% under heavy PID load, 1% as a rule of thumb). No dropped-frame rate in per-second terms was found. Use these as bounds for a sensitivity range, not as a calibrated model input.
- Sources were not opened as full pages beyond search snippets. The IntoFPV and ArduPilot figures come from search-result summaries, not from full page reads.

