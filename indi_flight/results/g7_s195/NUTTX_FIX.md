# G7(e) NuttX compile fix and size (S195, agent)

## Edit (only one needed; whole NuttX build of both INDI modules then compiles)
| file:line | old | new | why identical |
|---|---|---|---|
| src/modules/mc_indi_pos_control/IndiStageMode.hpp:107 | `std::fmin(std::fmax(raw_dt, kStageDtMin), kStageDtMax)` | `fminf(fmaxf(raw_dt, kStageDtMin), kStageDtMax)` | raw_dt, kStageDtMin, kStageDtMax are all float; std::fmin/fmax on floats resolve to the float overloads = fminf/fmaxf (same NaN rule, though the isfinite guard precedes). |
No other compile error appeared in the 4 directories (v6x and v5x both compile fully). Not committed.

## Build commands (Docker px4io/px4-dev:v1.16.0-rc1-258-g0369abd556, -u 1001:1001, HOME=/tmp, `timeout 3000`, repo mounted at same path)
- temp labels boards/px4/fmu-v6x/indi.px4board and fmu-v5x/indi.px4board = default.px4board + CONFIG_MODULES_MC_INDI_RATE_CONTROL=y + CONFIG_MODULES_MC_INDI_POS_CONTROL=y (stock mc_rate/mc_pos kept). Both DELETED.
- `make px4_fmu-v6x_indi`, `make px4_fmu-v5x_indi`, `make px4_fmu-v5x_default`; sizes with `arm-none-eabi-size build/<t>/*.elf`.
- Logs: build_nuttx_both_indi.log (v6x), build_nuttx_v5x_indi.log.

## Sizes
### px4_fmu-v6x (flash 1966080 B): LINK FAILS, flash overflow
`region 'FLASH' overflowed by 23492 bytes` (INDI both modules). Implied text+data = 1989572 B; vs stock 1924508 B (FORMAT_SIZE.md) = about +65064 B. Stock free was 41572 B. No ELF produced, so no text/data/bss for v6x INDI.
### px4_fmu-v5x (FLASH_AXIM region 2016 KB = 2064384 B): FITS
| build | text | data | bss | flash used (linker) | free |
|---|---|---|---|---|---|
| stock default | 1983464 | 7148 | 98460 | 1990612 B (96.43%) | 73772 B |
| both INDI | 2048336 | 7188 | 98460 | 2055524 B (99.57%) | 8860 B |
| delta | +64872 | +40 | 0 | +64912 B (63.4 KB) | |
SRAM1 105436 -> 105500 B (+64 B static). Static only; task stacks/heap not included. The v5x delta (+64.9 KB) agrees with the v6x implied delta (+65.1 KB). Rate-only on v6x was +33.4 KB, so pos module + lib/indi_accel_control about +31.5 KB.
Conclusion: on a 2 MB part with stock default modules, both INDI modules fit on v5x with 8.9 KB to spare, do not fit on v6x default (23.5 KB short) unless other modules are dropped.

## Unit tests (host test build, px4-indi-sim image, `make tests TESTFILTER="'<regex>'"` into build/px4_sitl_test; px4_sitl_default untouched)
- Filter 'Indi|FailsafeSetpoint|SetpointExtrapolation|EkfResetDetect': 12/12 ctest targets passed (IndiAccelControl, IndiPosInjection, IndiStageMode, FailsafeSetpoint, EkfResetDetect, SetpointExtrapolation, IndiInjection, IndiMeasuredTorque, IndiRateSetpointWatchdog, IndiRateFeedforwardGate, IndiTorqueStampTracker, IndiInjectionStep). Log build/g7_tests.log
- Filter 'indi_rate_control' (lib test, name has no "Indi" capital): 1/1 passed. Log build/g7_tests2.log
- Total 13/13 ctest targets, 0 failed. Per-gtest-case counts not printed by ctest (unverified).

## astyle
`Tools/astyle/fix_code_style.sh --dry-run --formatted src/modules/mc_indi_pos_control/IndiStageMode.hpp` in Docker: no output (PASS).

## git diff --stat -- src
 src/modules/mc_indi_pos_control/IndiStageMode.hpp | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
