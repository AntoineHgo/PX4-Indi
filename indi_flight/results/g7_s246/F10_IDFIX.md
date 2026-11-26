# F-10 id fix, 7 firmware comments (comment-only)

Files: src/modules/mc_indi_pos_control/{EkfResetDetect,FailsafeSetpoint,SetpointExtrapolation}.hpp,
src/modules/simulation/gz_bridge/{GZBridge.cpp,GZBridge.hpp,GZMixingInterfaceESC.hpp}

Old -> new (id token and its parentheses removed, rest of sentence kept):
1. EkfResetDetect.hpp:4 "counters (T10). Pure" -> "counters. Pure"
2. FailsafeSetpoint.hpp:4 "module (T5). Pure" -> "module. Pure"
3. SetpointExtrapolation.hpp:4 "module (probe F2). The" -> "module. The"
4. GZBridge.cpp:686 "IMU (D-VIB-HOOK): the" -> "IMU: the"
5. GZBridge.hpp:175 "delay line (hook A2), one" -> "delay line, one"
6. GZMixingInterfaceESC.hpp:155 "delay line (hook A1). Only" -> "delay line. Only"
7. GZBridge.cpp:644 "Base stddev = SDF values in indi_flight/sim/staged/quad5in_base_model_a14.sdf (gyro lines ~186-198, accel ~208-221)."
   -> "Base stddev = IMU noise values of the vehicle model SDF."
   (the next line, FLU axes and 0.00686 accel z sigma, is untouched)

Extra scan of the 6 files (grep T#/F#/A#/S###/G#/Q#/D-*/indi_flight/indi_project/hook A/probe): no other hits.

Checks
(i) diff <(git show HEAD:$f | gcc -fpreprocessed -dD -E -P -x c++ -) <(gcc ... $f): empty for all 6 files.
(ii) PX4_ASTYLE_FIX=0 Tools/astyle/check_code_style.sh $f: rc 0 for all 6 files.
(iii) git diff --stat: only these 6 files, 7 lines changed.
