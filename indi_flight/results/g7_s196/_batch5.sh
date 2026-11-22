D=indi_flight/results/g7_s196; F=src/modules/mc_indi_rate_control/IndiInjectionStep.cpp
m() { echo "### $1 $F:$2 $3"; $D/mut.sh $F $2 "$3" 'IndiInjection|IndiPosInjection'; }
m S0 1 -
m S23 67 's/out.torque_inject.zero();/;/'
