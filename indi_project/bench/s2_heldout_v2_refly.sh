#!/usr/bin/env bash
# Re-fly of held-out V seed 3 for com_shift and motor_loss_0, all three controllers. The original runs stalled
# when the host suspended at 20:45:31 on 2026-11-14 (journalctl) and ended in wall timeouts: an infrastructure
# fault, so the affected (entry, seed) is re-flown for every controller (O-12). The stalled runs are kept in
# results/s2_heldout_v2/runs_suspended. Waits for SEEN_V2_DONE so it never shares the host with the seen set.
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
until grep -q SEEN_V2_DONE $P/results/s2_seen_v2/run.log 2>/dev/null; do sleep 60; done
SEEDS=3 bash $P/bench/s2_heldout_v2.sh >> $P/results/s2_heldout_v2/run.log 2>&1
echo HELDOUT_V2_REFLY_DONE >> $P/results/s2_heldout_v2/run.log
