#!/bin/bash
R=indi_flight/results/stage5_s83_stick
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
bash $R/fly.sh pid_altctl altctl
bash $R/fly.sh pid_posctl posctl
bash $R/fly.sh indi_altctl altctl $R/indi.params
bash $R/fly.sh indi_posctl posctl $R/indi.params
