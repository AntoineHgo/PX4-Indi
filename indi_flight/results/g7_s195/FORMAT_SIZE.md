# G7(d)/(e) format and NuttX size (S195)

Image: px4io/px4-dev:v1.16.0-rc1-258-g0369abd556 (astyle 3.1, arm-none-eabi-gcc 7-2017-q4). Run as uid 1001, HOME=/tmp.

## G7(d) check_format: PASS
- Set: `git diff --name-only --diff-filter=d main...HEAD -- src msg`, filtered to *.c/*.h/*.cpp/*.hpp = 46 files (msg/*.msg, yaml, Kconfig, CMake not astyle-checked by PX4).
- Method: files exported with `git show HEAD:<f>` into a scratch copy, then per file `Tools/astyle/fix_code_style.sh --dry-run --formatted <f>` (the exact check used by check_code_style.sh, astylerc of the tree), in Docker. Result: 0 files reported, 0 diff lines.
- Deviation: ran on committed HEAD copies instead of `make check_format` on the tree, to avoid any rewrite. Only indi_flight/STATE.md is dirty in the tree (not in src/msg).

## G7(e) size, board px4_fmu-v6x (STM32H743, flash 1920 KB = 1966080 B)
Commands (in the container, repo mounted at same path):
- stock: `make px4_fmu-v6x_default`
- INDI: temp untracked `boards/px4/fmu-v6x/indi.px4board` = copy of default.px4board + `CONFIG_MODULES_MC_INDI_RATE_CONTROL=y`; `make px4_fmu-v6x_indi`
- `arm-none-eabi-size build/px4_fmu-v6x_{default,indi}/*.elf`

| build | text | data | bss | flash used (text+data) | flash free |
|---|---|---|---|---|---|
| stock default | 1916464 | 8044 | 107452 | 1924508 B (97.89%) | 41572 B |
| INDI (rate module only) | 1949848 | 8076 | 107516 | 1957924 B (99.59%) | 8156 B |
| delta | +33384 | +32 | +64 | +33416 B (32.6 KB) | |

AXI_SRAM used (linker): 113276 -> 113404 B (+128 B static). Runtime heap/stack of the module tasks is not included (static only).
Per archive (arm-none-eabi-size -t, pre-link, text): libmodules__mc_indi_rate_control.a 8056 (+20 data); libIndiRateControl.a (lib/indi_rate_control) 8488; IndiMeasuredTorque 1720; IndiInjection 892; IndiInjectionStep 420; IndiSafety 368. Sum about 20 KB; the 33 KB link delta also includes pulled-in code (uORB topic metadata, params, deps) and is the figure to cite.

## FINDING: mc_indi_pos_control does NOT compile for NuttX
With CONFIG_MODULES_MC_INDI_POS_CONTROL=y the build fails:
`src/modules/mc_indi_pos_control/IndiStageMode.hpp:107:45: error: 'fmin' is not a member of 'std'` (std::fmin/std::fmax with the NuttX toolchain; ::fmin exists). Build stopped at -Wfatal-errors, so further errors in that module are possible (unverified). Firmware frozen, not fixed. Hence the pos module and lib/indi_accel_control are NOT in the size numbers (INDI figure = rate module + lib/indi_rate_control only). Logs: build_stock_and_failed_indi.log (failing run is the second block), build_indi_rate_only.log.
Flash note: with the rate module alone only 8156 B are free on v6x default; adding the pos module likely will not fit without dropping other modules (unmeasured).

## Deviations / cleanup
- Pos module excluded from INDI build (compile error above); rate-only label used.
- Untracked boards/px4/fmu-v6x/indi.px4board deleted. Scratch tmp deleted. Containers g7_build, g7_build2 removed. Build outputs remain in build/px4_fmu-v6x_default and build/px4_fmu-v6x_indi (untracked). No tracked file modified, nothing committed.
