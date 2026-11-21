#!/bin/bash
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
for r in indi_flight/results/g4_gate_s169/hover_harsh_s2 indi_flight/results/g4_jff_s172/hover_*_s?; do
  python3 -I indi_flight/results/g4_jff_s172/omega_ff.py $r
done
