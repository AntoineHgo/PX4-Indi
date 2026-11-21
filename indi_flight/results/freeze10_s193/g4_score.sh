#!/usr/bin/env bash
# FREEZE-10 G4 scoring, run INSIDE docker (scipy): run.sh -n f10g4score -t 1800 -- bash indi_flight/results/freeze10_s193/g4_score.sh
# = freeze9_s183/g4/score_all.sh (paths rewritten) + Q19 re-scores + Q20 guard key1/key2. PID refs: freeze9 g4_pid (PID firmware unchanged), symlink freeze10_s193/g4_pid.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
R=indi_flight/results/freeze10_s193; G=$R/g4; mkdir -p $G/q18
sed -e "s#freeze9_s183#freeze10_s193#g" indi_flight/results/freeze9_s183/g4/score_all.sh > $G/score_all.sh
# Q19 script copies keep their g4_gate_s169 refs (score_all sed rewrites them); only the freeze9 path refs are changed here
sed -i -e "s#freeze9_s183#freeze10_s193#g" $G/rescore_key1_q19.py $G/rescore_key2_q19.py
sed -i -e "s#freeze9_s183#freeze10_s193#g" $G/guard_q19.py $G/g3_checks_q19.py
bash $G/score_all.sh
cd $R || exit 1
python3 ../../bench/g4_guard_q20_key1.py --selftest > g4/guard_q20_selftest1.txt 2>&1
python3 ../../bench/g4_guard_q20_key1.py g4/{hover,cruise}_{quiet,typ,harsh}_s{1,2,3} > g4/guard_q20_key1_stdout.txt 2> g4/guard_q20_key1_stderr.txt
python3 ../../bench/g4_guard_q20_key2.py --selftest > g4/guard_q20_selftest2.txt 2>&1
args=""; for r in {hover,cruise}_{quiet,typ,harsh}_s{1,2,3}; do
  if [ -d g4_pid/$r ]; then args="$args g4/$r,g4_pid/$r"; else args="$args g4/$r,-"; fi; done
python3 ../../bench/g4_guard_q20_key2.py $args > g4/guard_q20_key2_stdout.txt 2> g4/guard_q20_key2_stderr.txt
echo G4_SCORE_DONE > g4/g4_score.done
