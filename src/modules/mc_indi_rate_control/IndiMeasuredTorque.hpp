/****************************************************************************
 *
 *   Copyright (c) 2026 PX4 Development Team. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in
 *    the documentation and/or other materials provided with the
 *    distribution.
 * 3. Neither the name PX4 nor the names of its contributors may be
 *    used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 * AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 ****************************************************************************/

/**
 * @file IndiMeasuredTorque.hpp
 *
 * Torque produced by the measured rotor speeds (ESC rpm telemetry), for the INDI rate controller.
 *
 * The rotor speed gives the normalised thrust u = (omega / omega_max)^2 of each motor. The torque is the
 * control allocation's own mapping of that actuator vector, so the effectiveness matrix, the trim and the
 * normalisation are the ones the control allocator uses (same library, same configuration).
 *
 * No dynamic allocation, no uORB: the caller feeds plain samples and gets plain values back.
 */

#pragma once

#include <stdint.h>

#include <matrix/matrix/math.hpp>
#include <control_allocation/control_allocation/ControlAllocationPseudoInverse.hpp>

/**
 * Control allocation that can also evaluate the control produced by a given actuator vector.
 * The base class only offers this for the actuator setpoint it computed itself.
 */
class IndiControlAllocation : public ControlAllocationPseudoInverse
{
public:
	/**
	 * @param actuator Actuator vector, same units and order as the actuator setpoint. NaN means zero thrust.
	 * @return control produced by the actuator vector, same expression as getAllocatedControl()
	 */
	matrix::Vector<float, ControlAllocation::NUM_AXES> getControlFromActuators(const ActuatorVector &actuator) const;

	/** Neutral actuator values, the actuator vector that produces zero control */
	const ActuatorVector &actuatorTrim() const { return _actuator_trim; }
};

class IndiMeasuredTorque
{
public:
	static constexpr int MAX_MOTORS = 12; ///< same as the number of motor outputs (actuator_motors)
	static constexpr uint64_t SAMPLE_MAX_AGE_US = 20000; ///< an older ESC sample makes the measured torque invalid
	static constexpr float MAX_OMEGA_RATIO = 1.5f; ///< above this multiple of omega_max a rotor speed is implausible

	struct Result {
		float torque[3] {};          ///< roll, pitch, yaw, normalised like the torque setpoint
		uint64_t timestamp_sample{0}; ///< time of the oldest ESC sample used
		uint8_t motor_valid_mask{0}; ///< motors (0..7) whose sample was used
		bool valid{false};           ///< all rotors fresh and the torque finite
	};

	/**
	 * Configure the allocation from an effectiveness configuration, as the control allocator does.
	 * Axes with only marginal authority are dropped, the normalisation is recomputed.
	 *
	 * @param num_rotors number of actuators (columns) of the matrix, motors first and in motor order
	 */
	void setEffectiveness(const ActuatorEffectiveness::EffectivenessMatrix &effectiveness,
			      const ControlAllocation::ActuatorVector &trim,
			      const ControlAllocation::ActuatorVector &linearization_point, int num_rotors, bool normalize_rpy);

	/** Rotor speed at full thrust in rad/s, 0 or negative disables the measured torque */
	void setRotorSpeedMax(float omega_max) { _omega_max = omega_max; }

	bool enabled() const { return (_omega_max > 0.f) && (_num_rotors > 0); }

	/** Forget the sample of a motor that is offline */
	void setMotorOffline(int motor);

	/**
	 * Store the rotor speed sample of a motor.
	 *
	 * A failed telemetry frame (error count increments) is reported by the ESC as the last good value with a fresh
	 * timestamp: the previous sample and its time are kept, so a run of dropped frames ages it out.
	 *
	 * @param motor motor index
	 * @param rpm rotor speed of the ESC report in rpm
	 * @param error_count esc_errorcount of the report
	 * @param timestamp timestamp of the report
	 */
	void setMotorSample(int motor, float rpm, uint32_t error_count, uint64_t timestamp);

	/**
	 * Torque produced by the latest samples. Rotors without a fresh sample are evaluated at the trim
	 * (zero control) and make the result invalid.
	 */
	Result compute(uint64_t now) const;

	/** Control produced by an actuator vector (NaN counts as zero thrust) */
	matrix::Vector<float, ControlAllocation::NUM_AXES> torqueFromActuators(const ControlAllocation::ActuatorVector &actuator)
	const
	{
		return _allocation.getControlFromActuators(actuator);
	}

	const IndiControlAllocation &allocation() const { return _allocation; }

private:
	struct Sample {
		uint64_t timestamp_good{0}; ///< timestamp of the last sample that was not a repeated (dropped) one
		float u{0.f};               ///< normalised thrust (omega / omega_max)^2 of that sample
		uint32_t error_count{0};
		bool online{false};
		bool has_value{false};      ///< a sample was received since the motor was last seen offline
		bool u_valid{false};        ///< the last sample was finite, non negative and plausible
	};

	IndiControlAllocation _allocation;
	Sample _samples[MAX_MOTORS] {};
	float _omega_max{0.f};
	int _num_rotors{0};
};
