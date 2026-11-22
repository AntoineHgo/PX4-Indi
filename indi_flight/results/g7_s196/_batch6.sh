D=indi_flight/results/g7_s196; F=src/modules/mc_indi_rate_control/IndiInjectionStep.cpp
m() { echo "### $1 $F:$2 $3"; $D/mut.sh $F $2 "$3" 'IndiInjection|IndiPosInjection'; }
m S0 1 -
m S8 56 's/out.torque_inject.zero();/;/'
m S14 70 's/in.armed/true/'
m S15 70 's/in.landed/false/'
m S19 75 's/out.rates_sp_pre_inject.zero();/;/'
m S23 67 's/out.torque_inject.zero();/;/'
