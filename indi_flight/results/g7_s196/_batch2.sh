D=indi_flight/results/g7_s196
m() { echo "### $1 $2:$3 $4"; $D/mut.sh $2 $3 "$4" 'IndiInjection|IndiPosInjection'; }
for pre in "I src/modules/mc_indi_rate_control/IndiInjection.cpp 114" "P src/modules/mc_indi_pos_control/IndiPosInjection.cpp 114"; do
set -- $pre; p=$1; f=$2; rl=$3
m ${p}5 $f 124 's/1e6f/1e5f/'
m ${p}9 $f 40 's/axis > 3/axis > 4/'
m ${p}12 $f 76 's/k == last_k/k == last_k - 100000/'
m ${p}14 $f 61 's/!(f_max > f_min)/false/'
m ${p}15 $f 46 's/n_periods == _n_periods/true/'
m ${p}16 $f 58 's/_started = false;/;/'
m ${p}19 $f 61 's/n_periods < 1/n_periods < 0/'
m ${p}20 $f 61 's/!(period > 0.f)/false/'
m ${p}21 $f 61 's/!(f_min > 0.f)/false/'
m ${p}22 $f 40 's/axis < 0 ||/false ||/'
done
m I18 src/modules/mc_indi_rate_control/IndiInjection.cpp 114 's/_started = false;/;/'
m P18 src/modules/mc_indi_pos_control/IndiPosInjection.cpp 114 's/reset();/;/'
