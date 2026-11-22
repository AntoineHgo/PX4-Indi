# G7(a) stock modules at zero diff (S195, 2026-11-22)

Command (HEAD 08441561a6, merge-base with main 7d362c6f38):

```
for p in src/modules/mc_rate_control src/modules/mc_att_control src/modules/mc_pos_control \
  src/modules/control_allocator src/lib/control_allocation src/modules/commander \
  src/modules/land_detector src/modules/ekf2 src/modules/flight_mode_manager; do
  echo "$p $(git diff main...HEAD -- $p | wc -l)"; done
```

Result: 0 diff lines for all nine paths (the six named by O-11 plus land_detector, ekf2, flight_mode_manager).

Stock files the branch does touch (outside O-11, to be reviewed for the firmware-only branch):
ROMFS rc.mc_apps (+29/-), init.d-posix rcS (+6), airframe 4040_gz_quad5in (new), boards/px4/sitl/default.px4board (+3),
src/modules/logger/logged_topics.cpp (+4), msg/CMakeLists.txt (+6), src/lib/CMakeLists.txt (+2), gz_bridge (sim hooks).

Verdict G7(a): PASS at 08441561a6 (re-run on the firmware-only branch when it is cut).
