# G7 NuttX re-check at HEAD 4e7b12048e (S252)

Board px4_fmu-v5x. Temp untracked boards/px4/fmu-v5x/indi.px4board = default.px4board + CONFIG_MODULES_MC_INDI_RATE_CONTROL=y + CONFIG_MODULES_MC_INDI_POS_CONTROL=y (deleted at end).
Image: px4io/px4-dev:v1.16.0-rc1-258-g0369abd556 (px4-indi-sim has no arm-none-eabi-gcc; first attempt with it failed at cmake, not a code issue). Commands, via the docker run.sh wrapper:
`PX4_INDI_IMAGE=<that image> run.sh -n s252 -t 2700 'HOME=/tmp make px4_fmu-v5x_indi'` (and `px4_fmu-v5x_default`), then `arm-none-eabi-size` on both elfs.

## Result
- INDI build: rc=0, 102 s, full 1329 steps, 0 compiler warnings, 0 errors.
- Stock build: rc=0, 73 s, 0 warnings.
- Logs: build_nuttx_v5x_indi.log, build_nuttx_v5x_stock.log, size.txt

| build | text | data | bss | flash used (linker) | SRAM1 |
|---|---|---|---|---|---|
| stock | 1983480 | 7148 | 98460 | 1990628 B (96.43%) | 105436 |
| INDI both | 2048232 | 7188 | 98460 | 2055420 B (99.57%) | 105500 |
| delta | +64752 | +40 | 0 | +64792 B (63.3 KB) | +64 B |

Flash free with INDI: 2064384 - 2055420 = 8964 B.

## vs S195 (+64872 text, +40 data, +64912 B flash, SRAM1 +64)
Compiles the same. Flash delta is 120 B smaller (+64792 vs +64912); data and SRAM1 identical. Stock text moved +16 B (1983464 -> 1983480), so the stock tree itself changed slightly. IndiMeasuredTorque and the new headers cause no NuttX-only error; the std::fmin fix from S195 is in HEAD.
Static only; task stacks/heap not included. v6x not rebuilt (S195: overflow by 23492 B with both modules).
