############################################################################
#
#   Copyright (c) 2019 PX4 Development Team. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name PX4 nor the names of its contributors may be
#    used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
############################################################################

px4_add_library(IndiInjection
	IndiInjection.cpp
	IndiInjection.hpp
)
target_compile_options(IndiInjection PRIVATE ${MAX_CUSTOM_OPT_LEVEL})
target_include_directories(IndiInjection PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

px4_add_library(IndiInjectionStep
	IndiInjectionStep.cpp
	IndiInjectionStep.hpp
)
target_compile_options(IndiInjectionStep PRIVATE ${MAX_CUSTOM_OPT_LEVEL})
target_include_directories(IndiInjectionStep PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(IndiInjectionStep PUBLIC IndiInjection IndiRateControl)

px4_add_library(IndiSafety
	IndiRateFeedforwardGate.cpp
	IndiRateFeedforwardGate.hpp
	RateSetpointWatchdog.cpp
	RateSetpointWatchdog.hpp
	TorqueStampTracker.cpp
	TorqueStampTracker.hpp
)
target_compile_options(IndiSafety PRIVATE ${MAX_CUSTOM_OPT_LEVEL})
target_include_directories(IndiSafety PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

px4_add_library(IndiMeasuredTorque
	IndiErpmArmingCheck.cpp
	IndiErpmArmingCheck.hpp
	IndiMeasuredTorque.cpp
	IndiMeasuredTorque.hpp
)
target_compile_options(IndiMeasuredTorque PRIVATE ${MAX_CUSTOM_OPT_LEVEL})
target_include_directories(IndiMeasuredTorque PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(IndiMeasuredTorque PUBLIC ControlAllocation mathlib)

px4_add_module(
	MODULE modules__mc_indi_rate_control
	MAIN mc_indi_rate_control
	COMPILE_FLAGS
		${MAX_CUSTOM_OPT_LEVEL}
	SRCS
		McIndiRateControl.cpp
		McIndiRateControl.hpp
	MODULE_CONFIG
		mc_indi_rate_control_params.yaml
	DEPENDS
		IndiRateControl
		IndiInjection
		IndiInjectionStep
		IndiMeasuredTorque
		IndiSafety
		VehicleActuatorEffectiveness
		mathlib
		px4_work_queue
	)

px4_add_unit_gtest(SRC IndiInjectionTest.cpp LINKLIBS IndiInjection)
px4_add_functional_gtest(SRC IndiErpmArmingCheckTest.cpp LINKLIBS IndiMeasuredTorque VehicleActuatorEffectiveness)
px4_add_functional_gtest(SRC IndiMeasuredTorqueTest.cpp LINKLIBS IndiMeasuredTorque VehicleActuatorEffectiveness)
px4_add_unit_gtest(SRC IndiRateSetpointWatchdogTest.cpp LINKLIBS IndiSafety)
px4_add_unit_gtest(SRC IndiRateFeedforwardGateTest.cpp LINKLIBS IndiSafety)
px4_add_unit_gtest(SRC IndiRateSetpointSourceTest.cpp)
px4_add_unit_gtest(SRC IndiTorqueStampTrackerTest.cpp LINKLIBS IndiSafety)
px4_add_unit_gtest(SRC IndiInjectionStepTest.cpp LINKLIBS IndiInjectionStep)
