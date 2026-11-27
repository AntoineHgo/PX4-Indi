#!/usr/bin/env bash
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
G=indi_flight/results/g7_s251
B=$G/brk.sh
$B e1 src/modules/mc_indi_pos_control/IndiEscThrust.hpp 'rotor_thrust_sum / 4.f' 'rotor_thrust_sum / 3.f' unit-IndiEscThrust
$B e2 src/modules/mc_indi_pos_control/IndiEscThrust.hpp 'seen == 0xFu' 'seen != 0' unit-IndiEscThrust
$B e3 src/modules/mc_indi_pos_control/IndiEscThrust.hpp 'if (!(esc_status.esc_online_flags & (1u << j))' 'if (!(esc_status.esc_online_flags | (1u << j))' unit-IndiEscThrust
$B e4 src/lib/indi_rate_control/indi_rate_control.hpp 'kMaxRpmRatio = 1.5f;' 'kMaxRpmRatio = 100.f;' unit-IndiEscThrust
$B e5 src/modules/mc_indi_pos_control/IndiEscThrust.hpp 'age_us <= max_age_us' 'age_us < max_age_us' unit-IndiEscThrust
$B e6 src/modules/mc_indi_pos_control/IndiEscThrust.hpp '(now_us > sample_us) ? (now_us - sample_us) : uint64_t{0}' 'now_us - sample_us' unit-IndiEscThrust
$B e7 src/modules/mc_indi_pos_control/IndiEscThrust.hpp 'if (motor < 0 || motor >= 4)' 'if (motor >= 4)' unit-IndiEscThrust
$B m1 src/modules/mc_indi_rate_control/IndiRateSetpointSource.hpp '| (omega_ff_on << 5);' '| 0;' unit-IndiRateSetpointSource
$B l1 src/lib/indi_rate_control/indi_rate_control.hpp 'void resetSetpointLead() { _sp_lead_reset = true; }' 'void resetSetpointLead() { }' unit-indi_rate_control_test
$B l2 src/lib/indi_rate_control/indi_rate_control.cpp 'landed || _sp_lead_reset' 'landed || true' unit-indi_rate_control_test
echo DONE
