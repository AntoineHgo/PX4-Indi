D=indi_flight/results/g7_s196
m() { echo "### $1 $2:$3 $4"; $D/mut.sh $2 $3 "$4" 'IndiInjection|IndiPosInjection'; }
for pre in "I src/modules/mc_indi_rate_control/IndiInjection.cpp" "P src/modules/mc_indi_pos_control/IndiPosInjection.cpp"; do
set -- $pre; p=$1; f=$2
m ${p}1 $f 92 's/_phase\[k\] = -2.0/_phase[k] = 2.0/'
m ${p}2 $f 101 's/d += /d -= /'
m ${p}3 $f 101 's/2.0 \* M_PI \* _freq/M_PI * _freq/'
m ${p}4 $f 101 's/(double)_amp \*/0.5 * (double)_amp */'
m ${p}5 $f 124 's/1e6f/1e5f/'
m ${p}6 $f 133 's/t >= /t > /'
m ${p}7 $f 133 's/(double)_n_periods/((double)_n_periods + 1.0)/'
m ${p}8 $f 118 's/if (landed)/if (false)/'
m ${p}9 $f 40 's/axis > 3/axis > 4/'
m ${p}10 $f 72 's/per_decade/(per_decade+1)/'
m ${p}11 $f 76 's/ || k \* df > (double)f_max + 0.5 \* df//'
m ${p}12 $f 76 's/ || k == last_k//'
m ${p}13 $f 109 's/_axis == 0 ||/false ||/'
m ${p}14 $f 61 's/!(f_max > f_min)/false/'
m ${p}15 $f 46 's/n_periods == _n_periods/true/'
m ${p}16 $f 58 's/_started = false;/;/'
m ${p}17 $f 113 's/if (!armed)/if (false)/'
done
m I18 src/modules/mc_indi_rate_control/IndiInjection.cpp 114 's/_started = false;/;/'
m P18 src/modules/mc_indi_pos_control/IndiPosInjection.cpp 114 's/reset();/;/'
