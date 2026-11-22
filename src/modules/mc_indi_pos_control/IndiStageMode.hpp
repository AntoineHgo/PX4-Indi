#pragma once

#include <cmath>

/**
 * Pure decision logic of the INDI outer loop (no PID fallback).
 * Header only, no PX4 dependency, so it is unit tested on its own.
 */

enum class StageMode : unsigned char {
	Bypass = 0,         ///< INDI not requested (disarmed, or position/velocity/climb control off): stock setpoint
	Indi = 1,           ///< normal INDI cycle
	IndiModelAccel = 2, ///< runs on the modelled specific force: measured acceleration stale, or on the ground / takeoff ramp
	Hold = 3            ///< zero-order hold of the last attitude setpoint and thrust
};

/**
 * @param want    INDI requested (computeWantIndi)
 * @param att_ok  attitude fresh, finite, norm >= 0.5
 * @param acc_ok  acceleration fresh and finite
 * @param accel_command_ok commanded acceleration finite
 * @param rate_ok work item rate > 5 Hz
 * @param model_force ground or takeoff ramp (useModelledForce): the measured acceleration holds the ground reaction
 * A failure of IndiAccelControl::update() is handled by the caller (Indi/IndiModelAccel -> Hold).
 */
inline StageMode selectStageMode(bool want, bool att_ok, bool acc_ok, bool accel_command_ok, bool rate_ok, bool model_force = false)
{
	if (!want) {
		return StageMode::Bypass;
	}

	if (!att_ok || !accel_command_ok || !rate_ok) {
		return StageMode::Hold;
	}

	return (acc_ok && !model_force) ? StageMode::Indi : StageMode::IndiModelAccel;
}

/** INDI is requested: armed in a position/velocity/climb-rate mode, whatever the takeoff state. */
inline bool computeWantIndi(bool armed, bool pos, bool vel, bool climb)
{
	return armed && (pos || vel || climb);
}

/**
 * The modelled specific force (not the measured one) is used on the ground and during the takeoff ramp, where the
 * measured acceleration contains the ground reaction. Measured only in flight without ground contact.
 */
inline bool useModelledForce(bool takeoff_flight, bool ground_contact, bool maybe_landed)
{
	return !takeoff_flight || ground_contact || maybe_landed;
}

/** Climb rate only (no position, no velocity control): INDI collective, stock thrust direction. */
inline bool deriveZOnly(bool pos, bool vel)
{
	return !(pos || vel);
}

/**
 * Climb-rate-only mode on the ground: with minimum thrust 0 the stock chain gives a zero thrust vector, whose
 * direction the library rejects (Hold). A finite zero vector means "no tilt": use straight up.
 */
inline bool isZeroThrustDir(float x, float y, float z)
{
	const float norm_squared = x * x + y * y + z * z;
	return std::isfinite(norm_squared) && (norm_squared < 1e-12f);
}

/** Hold with no held INDI output: minimum thrust 0 unless flying, never hover thrust on ground. */
inline float holdFallbackThrust(bool flying, float hover_thrust)
{
	return flying ? (std::isfinite(hover_thrust) ? hover_thrust : 0.5f) : 0.f;
}

/** Arm or disarm edge: the INDI state (blend, held setpoint, stale latch, differencing) restarts for the next arm. */
inline bool shouldResetStageState(bool prev_armed, bool armed)
{
	return prev_armed != armed;
}

/** Rising edge of position control: the INDI state is stale from the non-position mode. */
inline bool shouldResetOnPosControlEntry(bool prev_pos_enabled, bool pos_enabled)
{
	return !prev_pos_enabled && pos_enabled;
}

/** Hold -> run edge: the time base did not advance in Hold, so the differencing and filters restart. */
inline bool shouldResetOnHoldToRun(bool prev_was_hold, bool can_run)
{
	return prev_was_hold && can_run;
}

/** Sample interval: below kStageDtMin it is clamped, above kStageDtMax (rate < 5 Hz) the loop holds. */
static constexpr float kStageDtMin = 0.002f;
static constexpr float kStageDtMax = 0.2f; // library kMaxDt is 0.5

inline bool stageIntervalOk(float raw_dt_s)
{
	return std::isfinite(raw_dt_s) && (raw_dt_s <= kStageDtMax);
}

/** The dt the library sees: the true interval, lower-clamped (and capped at kStageDtMax; longer intervals hold). */
inline float stageDt(float raw_dt_s)
{
	return std::isfinite(raw_dt_s) ? fminf(fmaxf(raw_dt_s, kStageDtMin), kStageDtMax) : kStageDtMax;
}
