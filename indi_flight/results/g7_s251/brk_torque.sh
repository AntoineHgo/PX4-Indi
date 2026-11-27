#!/usr/bin/env bash
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
B=indi_flight/results/g7_s251/brk.sh
$B t1 src/modules/control_allocator/VehicleActuatorEffectiveness/ActuatorEffectivenessRotors.cpp 'ct * position.cross(axis) - ct * km * axis' 'ct * position.cross(axis) + ct * km * axis' functional-IndiMeasuredTorque
$B t2 src/modules/mc_indi_rate_control/IndiMeasuredTorque.cpp 'math::constrain(ratio * ratio, 0.f, 1.f)' 'math::constrain(ratio, 0.f, 1.f)' functional-IndiMeasuredTorque
$B t3 src/modules/mc_indi_rate_control/IndiMeasuredTorque.cpp 'actuator(motor) = sample.u;' 'actuator(motor ^ 1) = sample.u;' functional-IndiMeasuredTorque
$B t4 src/modules/mc_indi_rate_control/IndiMeasuredTorque.cpp 'actuator(motor) = sample.u;' 'actuator(3 - motor) = sample.u;' functional-IndiMeasuredTorque
$B t5 src/lib/control_allocation/control_allocation/ControlAllocationPseudoInverse.cpp '_control_allocation_scale(2) = _mix.col(2).max();' '_control_allocation_scale(2) = 1.f;' functional-IndiMeasuredTorque
$B t6 src/modules/control_allocator/VehicleActuatorEffectiveness/ActuatorEffectivenessRotors.cpp 'ct * position.cross(axis) -' '-ct * position.cross(axis) -' functional-IndiMeasuredTorque
echo DONE
