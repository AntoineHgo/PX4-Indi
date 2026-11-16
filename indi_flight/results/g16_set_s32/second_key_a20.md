# Second-key review: commit 4297ba9869 (A-20, baro reference latch)

Scope: `src/modules/simulation/gz_bridge/GZBridge.{hpp,cpp}` and
`platforms/common/include/px4_platform_common/atomic.h`, read-only.

## Verdict: AGREE-WITH-ISSUES

The baro/navsat handoff for the single-GPS case is correct. Two issues remain:
the reference write is a non-atomic check-then-act once two GPS instances are
configured, and the ground-truth publisher still reads `_alt_ref` unguarded.
Neither changes the baro output in the single-GPS case.

## (1) Happens-before from `_alt_ref` write to the baro read: AGREE

- Writer: `GZBridge.cpp:913` writes `_alt_ref`, then `GZBridge.cpp:914`
  calls `_alt_ref_set.store(true)`. VERIFIED (read in `git show` and at the lines).
- Reader: `GZBridge.cpp:590` `_alt_ref_set.load()`; the mapping that reads
  `_alt_ref` is at `GZBridge.cpp:592`, only inside the `true` branch. VERIFIED.
- Type: `atomic.h:375` `using atomic_bool = atomic<bool>;`. VERIFIED.
- Ordering on POSIX (SITL): `PX4_ATOMIC_SINGLE_CORE` is 0 unless
  `__PX4_NUTTX && !CONFIG_SMP` (`atomic.h:82-86`), so `store` uses
  `__ATOMIC_SEQ_CST` (`atomic.h:157`) and `load` uses `__ATOMIC_SEQ_CST`
  (`atomic.h:132`). VERIFIED from source.
- A seq_cst store that the seq_cst load reads from synchronizes-with it, so the
  plain write at 913 happens-before the read at 592. VERIFIED by C++ memory-model
  reasoning on the code above; not run under TSan.
- NuttX single-core path (`atomic.h:123-129`, `154-155`) uses relaxed accesses
  with a seq_cst signal fence. That is compiler-only ordering, which is
  sufficient on one core. NuttX SMP uses seq_cst. VERIFIED from source.

## (2) Can `_alt_ref` be written after the flag is set?

- `_pos_ref` is only initialised at `GZBridge.cpp:917`. A grep of
  `src/modules/simulation/gz_bridge/` finds no other `initReference` or
  `_pos_ref =` assignment. VERIFIED.
- `MapProjection` has no reset; `isInitialized()` returns `_ref_init_done`
  (`src/lib/geo/geo.h:40`). VERIFIED.
- The only write to `_alt_ref` is line 913. VERIFIED by grep.
- Single-GPS case: no. Once the flag is set, `_alt_ref` is never written again
  on this path.
- Multi-GPS case: yes, possibly. `_MAX_GNSS_SENSORS = 2` (`GZBridge.hpp:150`).
  `subscribeNavsat` (`GZBridge.cpp:428-462`) subscribes one callback per instance,
  each capturing its own `i` (lines 443-445). `navSatCallback` admits instances
  below `count = min(2, SIM_GZ_EN_GPS)` (lines 901-905). The guard at 911-913 is
  check-then-act: `if (!_alt_ref_set.load()) { _alt_ref = ...; store(true); }`.
  Two instances can both load `false` before either stores, and then both write
  `_alt_ref`. The second write can land after the flag is visible, and the two
  writes can differ (each instance reports its own altitude). VERIFIED that the
  code allows this. UNVERIFIED that gz-transport delivers instance callbacks on
  different threads concurrently. This is the same race the existing
  `_pos_ref.isInitialized()` check already had.
- The pre-fix code was also racy here (it re-wrote `_alt_ref` on every callback
  until init). The fix narrows the window but does not close it.

## (3) Other unguarded readers of `_alt_ref`

- `GZBridge.cpp:759` `local_position_groundtruth.ref_alt = _alt_ref;` runs in
  `poseInfoCallback` (defined at line 689), so it is on the pose thread, not the
  navsat thread. VERIFIED. It is gated only by the non-atomic
  `_pos_ref.isInitialized()` at line 755, not by `_alt_ref_set`. VERIFIED.
- Consequence: the pose thread can see `ref_init_done` true while `_alt_ref`
  is still stale (0.0), or overlap with the multi-GPS write above. This is a
  data race and it is pre-existing; the commit does not touch it.
- Impact on the baro step: none. Line 759 only feeds `local_position_groundtruth`
  and does not reach `airPressureCallback`. VERIFIED from the call sites.
- Suggested fix (small): gate line 755 on `_alt_ref_set.load()` rather than
  `_pos_ref.isInitialized()`. That gives the same ordering the baro path has.

## (4) GPS-disabled path: AGREE, behaviour unchanged

- `subscribeNavsat` is only called when `_sim_gz_en_gps.get()` is set
  (`GZBridge.cpp:101-102`). With GPS disabled, `navSatCallback` never runs, so
  the flag stays `false`. VERIFIED.
- Baro: with the flag `false` and `SIM_GZ_EN_GPS == 0`, the `else if` at 594 does
  not return, so the unmapped pressure is published at 598-599. VERIFIED.
- Pre-fix, `_pos_ref.isInitialized()` was also always false in this case, so the
  unmapped publish is identical. VERIFIED from the diff.

## Other observations (not regressions)

- With GPS enabled but the navsat subscription failing (`subscribeNavsat(false)`,
  `GZBridge.cpp:101-102`), the baro never publishes, because the flag is never set
  and the GPS-enabled branch at 594-595 returns. This is pre-existing: the old check
  also returned early. VERIFIED from source; the runtime effect is not tested.
- `SIM_GZ_EN_GPS` is read in the baro callback at 594 and in navsat at 901. Both are
  ParamInt reads on different threads. Pre-existing; no change in this commit.

## Requested changes (for the author, not blocking the single-GPS path)

1. Make the reference write single-writer: either accept only `instance_index == 0`
   for `_alt_ref`, or claim it with `compare_exchange` (`atomic.h:337`) before
   writing, then publish with `store(true)`. Keep the store after the write.
2. Gate `GZBridge.cpp:755` on `_alt_ref_set.load()`.
3. Optional: a test or a TSan run with `SIM_GZ_EN_GPS=2` to confirm the race is
   reachable (UNVERIFIED here, not run).
