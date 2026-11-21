# G4 chatter probe, S175: is the AUTO_LAND ~22 Hz line gone after aa4fd2654a?

## Firmware of each log
| log | firmware | after aa4fd2654a? |
|---|---|---|
| results/g4_gate_s169 (18 runs) | before the freeze fix (not re-read here) | no |
| results/g4_jff_s172 hover (9) | run.json provenance: commit c2ad61df5e + dirty tree (the D-JFF-SOURCE diff, committed later as 20b4a41b22), binary 41d0b27d...; flown 09:11, aa4fd2654a committed 09:28 | NO, so NOT scored (task 2 condition not met) |
| hover_typ_s1 (this dir) | run.json: binary_commit 064457ffc1 (dirty = bench/docs files only), built here at BUILD_RC 0 (build.log) | yes: 064457ffc1 contains aa4fd2654a and `git diff aa4fd2654a 064457ffc1 -- src boards ROMFS platforms msg` is empty. HEAD moved to 922ca8be52 during the work (docs/bench commits; src diff after 064457ffc1 not re-checked) |

Flight: `sh indi_flight/bench/gate_g4.sh fly indi_flight/results/g4_chatter_probe_s175 typ hover 1` (via fly.sh, with a `make px4_sitl_default` first), rc 0 (status.txt), exit_status ok, timeout 900 s not hit.

## Key1 width fix (task 1)
`bench/g3_checks.py`: chatter line RMS now peak +-2 Hz (`CMD_RMS_HZ`, `rms_hz=`), was +-2 bins (+-0.5 Hz). Self-test `chat_width` added to `bench/tests/test_g3_checks.py`, break-check (old width) caught once, all PASS.
Re-score of the 18 s169 runs (`rescore_s175w.py`, `rescore_s175w_runs.md`; Q15 skip as before): chatter hover 4/9 -> 6/9 (+ harsh_s1, quiet_s1), cruise 9/9 -> 9/9, all 18: 13 -> 15. Detail in results/g4_gate_s169/rescore_s175.md section "S175 width fix".

## hover_typ_s1 at current firmware (task 3), scored like chatter_s175.md (`chatter_probe_s175.py`, ±2 Hz width in the band tracker and key1 detector; `landwin_s175.py` -> landwin_s175.txt)
Phases: OFFBOARD 29.8 s, AUTO_LAND entry 97.6 s, landed 108.2 s.
- Line at AUTO_LAND entry: NO. Windows 92.0-107.0 (entry 97.6 up to 3 s before the end of the descent): none flagged; best ratio>20 motor line RMS 1.2e-4 to 2.3e-4 (39 Hz), 0 at 102-107. Old runs: flagged from the window starting 94.0, 20-22.5 Hz, whole ~10 s descent.
- A 20.3 Hz line appears only in windows 103.5-109.0 (4 windows, line RMS 3.1e-3 falling to 1.1e-3), i.e. final touchdown (landed 108.2). Which window it came from: 103.0-107.0 is clean and 103.5-107.5 flagged, so the burst sits in about 107.0-107.5 s, <1.2 s before touchdown (inference from window edges, no finer check). Same position as the PID reference (flagged only at touchdown, chatter_s175.md section 2), but amplitude here is larger (3e-3, ±2 Hz width, vs PID 6.5e-4 at ±2 bins, not same width: not comparable directly).
- Steady OFFBOARD hold: 0 of 122 windows flagged (max ratio>20 line RMS 3.1e-4). Take-off/loiter: 0 flagged.
- Chatter verdict (sustained = 3 consecutive windows within 10 %): key1 0 (span h>1.0 m 12.4-103.7 s) and key2 0 (span h>0.3 m 11.5-104.7 s), with and without the 3 s nav skip (4 combinations all 0/0). Both spans end before the touchdown burst (key1 last h>1 m sample 103.7 s).
- Caveat: one seed, typ profile only; harsh (the s169 run with the largest line) was not flown. The disappearance is consistent with removing the vibration-coupled omega_ff (aff_source.md), but no run isolates that cause (no A/B on one commit); also the old verdict "CHATTER" for typ s1-s3 came from an airborne span that included the AUTO_LAND descent.
