# S126 A-42 closing test
Two sequential `indi_project/docker/run.sh` calls (distinct `-n s126a42_1/2`, distinct `--out r1/ r2/`), hover,
quad5in, indi_m3a, seed 1, speed 4, stock params. Command: `bash indi_flight/results/a42_s126/run.sh`.
Result: both rc 0, both dirs complete (flight.ulg, metrics.json status ok), 43 s apart. A-42 not reproduced.
The failing S124/S125 launches shared one `--out` parent; rule kept: one `--out` dir and one `-n` per run.
Raw logs untracked.
