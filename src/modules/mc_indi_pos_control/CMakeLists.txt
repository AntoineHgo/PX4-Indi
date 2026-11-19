############################################################################
#
#   Copyright (c) 2026 PX4 Development Team. All rights reserved.
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


px4_add_library(IndiPosInjection
	IndiPosInjection.cpp
	IndiPosInjection.hpp
)
target_compile_options(IndiPosInjection PRIVATE ${MAX_CUSTOM_OPT_LEVEL})
target_include_directories(IndiPosInjection PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

px4_add_module(
	MODULE modules__mc_indi_pos_control
	MAIN mc_indi_pos_control
	COMPILE_FLAGS
		${MAX_CUSTOM_OPT_LEVEL}
	SRCS
		McIndiPosControl.cpp
		McIndiPosControl.hpp
	MODULE_CONFIG
		mc_indi_pos_control_params.yaml
	DEPENDS
		IndiAccelControl
		IndiRateControl
		IndiPosInjection
		controllib
		geo
		SlewRate
		mathlib
		px4_work_queue
	)

# The stock position control libraries are defined by src/modules/mc_pos_control, which is configured after this
# directory: link them by name, resolved at generate time (MODULES_MC_POS_CONTROL is a Kconfig dependency).
target_link_libraries(modules__mc_indi_pos_control PRIVATE GotoControl PositionControl Takeoff)
target_include_directories(modules__mc_indi_pos_control PRIVATE ${PX4_SOURCE_DIR}/src/modules/mc_pos_control)

px4_add_unit_gtest(SRC IndiPosInjectionTest.cpp LINKLIBS IndiPosInjection)
px4_add_unit_gtest(SRC IndiStageModeTest.cpp)
px4_add_unit_gtest(SRC FailsafeSetpointTest.cpp)
px4_add_unit_gtest(SRC EkfResetDetectTest.cpp)
px4_add_unit_gtest(SRC HandoverBlendTest.cpp)
px4_add_unit_gtest(SRC HoverThrustSyncTest.cpp LINKLIBS PositionControl)
if(TARGET unit-HoverThrustSync)
	target_include_directories(unit-HoverThrustSync PRIVATE ${PX4_SOURCE_DIR}/src/modules/mc_pos_control)
endif()
