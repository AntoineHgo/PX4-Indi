# G7 re-check S259 on indi-fw-pr (rpm arming-check commits)

Branch head fcd212f228 (local only, no upstream, not pushed). Worktree /tmp/indi_fwbranch_s251 (reused, outside repo; build dirs kept, 3.5 GB; disk 189 GB free).
Cherry-picked e6af4b6b0d -> e07ac7d4d1, ac744d360e -> fcd212f228: no conflicts. Earlier branch commits carry no traceability lines, so the
"Owner answer Q36 B, decision D-OWNER-Q36 ... (indi_flight/results/...)" wording and the "Traceability: indi_flight ..." line were removed; Assisted-by kept.
src/modules/mc_indi_rate_control on branch is identical to feat/indi-flight.

Scripts: p2/ (S251 scripts with ids renamed; own docker wrapper dock.sh as in S251, since indi_project/docker/run.sh is guard-blocked for reading).

- (a) stock zero diff vs main (commander, mc_rate_control, mc_att_control, mc_pos_control, control_allocator, lib/control_allocation): PASS, 0 lines.
- (d) astyle dry-run: checked=53 reported=0 (p2/changed_cpp_files.txt).
- (g) make px4_sitl_default: rc=0, 443 steps incremental, 0 warnings.
- Tests (px4_sitl_test): 11 unit targets 216 passed + functional-IndiMeasuredTorque 23 + new functional-IndiErpmArmingCheck 5 = 244 passed, 0 failed (S251: 239).
- F-10 grep over added lines of diff main..HEAD (78 files, +16056/-23), S251 pattern: 0 hits; 0 paths under indi_flight/ or indi_project/.
- (e) NuttX px4_fmu-v5x (px4-dev v1.16.0-rc1-258 image, temp indi.px4board, removed): both builds rc=0, 0 warnings (INDI 133 s, stock 52 s).
  text 2049472 / data 7188 / bss 98460 (INDI) vs 1983424 / 7148 / 98460 (stock). FLASH_AXIM 2056660 B (99.63%) vs 1990572 B (96.42%): delta +66088 B
  (text +66048), +1296 B vs S252 (+64792). Free flash 7724 B. SRAM1 +64 B. Static only.
  Setup detours: NuttX submodule dirs copied from main checkout (paths sed-rewritten, stale objects removed, temp empty .git dir removed after).
