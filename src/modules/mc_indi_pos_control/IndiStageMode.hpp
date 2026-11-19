#pragma once

/**
 * Pure decision logic of the INDI outer-loop stage (D-STAGE-STALE, owner rule F-1: no PID fallback).
 * Header only, no PX4 dependency, so it is unit tested on its own.
 */

enum class StageMode : unsigned char {
	Bypass = 0,         ///< stage not requested: stock setpoint (ground handling, takeoff ramp)
	Indi = 1,           ///< normal INDI cycle
	IndiModelAccel = 2, ///< acceleration stale/non-finite: stage runs on the modelled specific force
	Hold = 3            ///< zero-order hold of the last attitude setpoint and thrust
};

/**
 * @param want    stage requested (computeWantIndi)
 * @param att_ok  attitude fresh, finite, norm >= 0.5
 * @param acc_ok  acceleration fresh and finite
 * @param aref_ok commanded acceleration finite
 * @param rate_ok work item rate > 5 Hz
 * A failure of IndiAccelControl::update() is handled by the caller (Indi/IndiModelAccel -> Hold).
 */
inline StageMode selectStageMode(bool want, bool att_ok, bool acc_ok, bool aref_ok, bool rate_ok)
{
	if (!want) {
		return StageMode::Bypass;
	}

	if (!att_ok || !aref_ok || !rate_ok) {
		return StageMode::Hold;
	}

	return acc_ok ? StageMode::Indi : StageMode::IndiModelAccel;
}

/** The stage is requested: armed, a position/velocity/climb-rate mode, takeoff state flight, no ground contact. */
inline bool computeWantIndi(bool armed, bool pos, bool vel, bool climb, bool takeoff_flight, bool ground_contact)
{
	return armed && (pos || vel || climb) && takeoff_flight && !ground_contact;
}

/** D-ALTCTL-Z: climb rate only (no position, no velocity control): INDI collective, stock thrust direction. */
inline bool deriveZOnly(bool pos, bool vel)
{
	return !(pos || vel);
}
