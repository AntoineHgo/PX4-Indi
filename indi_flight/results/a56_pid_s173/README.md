# A-56 PID reference (S173): stock PID, harsh hover s2/s3

Fly: `sh indi_flight/results/a56_pid_s173/fly.sh`; score (Docker): `analyse.sh`. Flags as results/a54_s169 (s1).
Item 2 (whole flight): s2 no sustained line (flagged windows p3 q1 r0), s3 none (p2 q2 r0); g3_checks rc 0 (PASS) both.
With s1 (a54_s169) PID is clean 3/3 at harsh, while INDI fails 1/3 (s3, 2 Hz) with either outer loop
(a56_probe_s173). A-56 is INDI-specific and lies in the INDI rate loop.
