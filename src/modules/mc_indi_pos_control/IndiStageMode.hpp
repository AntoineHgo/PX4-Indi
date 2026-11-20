#pragma once

/**
 * Pure decision logic of the INDI outer-loop stage (D-STAGE-STALE, owner rule F-1: no PID fallback).
 * Header only, no PX4 dependency, so it is unit tested on its own.
 */

enum class StageMode : unsigned char {
	Bypass = 0,         ///< stage not requested (disarmed, or position/velocity/climb control off): stock setpoint, nothing INDI
	Indi = 1,           ///< normal INDI cycle
	IndiModelAccel = 2, ///< stage runs on the modelled specific force: acceleration stale (D-STAGE-STALE a) or ground/ramp (D-F7-GROUND)
	Hold = 3            ///< zero-order hold of the last attitude setpoint and thrust
};

/**
 * @param want    stage requested (computeWantIndi)
 * @param att_ok  attitude fresh, finite, norm >= 0.5
 * @param acc_ok  acceleration fresh and finite
 * @param aref_ok commanded acceleration finite
 * @param rate_ok work item rate > 5 Hz
 * @param model_force ground or takeoff ramp (useModelledForce): the measured acceleration holds the ground reaction
 * A failure of IndiAccelControl::update() is handled by the caller (Indi/IndiModelAccel -> Hold).
 */
inline StageMode selectStageMode(bool want, bool att_ok, bool acc_ok, bool aref_ok, bool rate_ok, bool model_force = false)
{
	if (!want) {
		return StageMode::Bypass;
	}

	if (!att_ok || !aref_ok || !rate_ok) {
		return StageMode::Hold;
	}

	return (acc_ok && !model_force) ? StageMode::Indi : StageMode::IndiModelAccel;
}

/** The stage is requested (D-F7-GROUND): armed in a position/velocity/climb-rate mode, whatever the takeoff state. */
inline bool computeWantIndi(bool armed, bool pos, bool vel, bool climb)
{
	return armed && (pos || vel || climb);
}

/**
 * D-F7-GROUND: the stage uses the modelled specific force (not the measured one) on the ground and during the takeoff
 * ramp, where the measured acceleration contains the ground reaction. Measured only from takeoff state flight
 * without ground contact.
 */
inline bool useModelledForce(bool takeoff_flight, bool ground_contact, bool maybe_landed)
{
	return !takeoff_flight || ground_contact || maybe_landed;
}

/** D-ALTCTL-Z: climb rate only (no position, no velocity control): INDI collective, stock thrust direction. */
inline bool deriveZOnly(bool pos, bool vel)
{
	return !(pos || vel);
}

/** Arm or disarm edge: the stage state (blend b, held setpoint, stale latch, differencing) restarts for the next arm. */
inline bool shouldResetStageState(bool prev_armed, bool armed)
{
	return prev_armed != armed;
}
