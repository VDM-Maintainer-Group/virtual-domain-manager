cmake_minimum_required(VERSION 3.12) #for FindPython feature
#specify the C++ standard
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED True)

project(virtual-domain-manager)

#claim building dependency
find_package(Python REQUIRED
            COMPONENTS Interpreter Development)
#default configurations
set(VDM_INSTALL_DIR "/opt/vdm")
set(PYVDM_DIST_DIR ${CMAKE_CURRENT_BINARY_DIR}/pyvdm)
# set(CONFIG_DIR "$HOME/.vdm")
# set(PLUGINS_DIR "$HOME/.vdm/plugins")

# vdm core build
include_directories(assets)
include_directories(interface)
add_subdirectory(capability)
add_subdirectory(core)

# vdm gui build
add_subdirectory(gui)

# pyvdm installation: "pyvdm.interface" + "pyvdm.core" + "pyvdm.gui" + "pyvdm.capability" (binding, todo)
file(GLOB PYVDM_API "./interface/*.py")
add_custom_target(build-pyvdm
        COMMAND ${CMAKE_COMMAND} -E rm -rf ${PYVDM_DIST_DIR}
        COMMAND ${CMAKE_COMMAND} -E make_directory ${PYVDM_DIST_DIR}/interface
        COMMAND ${CMAKE_COMMAND} -E copy ${PYVDM_API} ${PYVDM_DIST_DIR}/interface
        COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_CURRENT_SOURCE_DIR}/core/pyvdm/ ${PYVDM_DIST_DIR}/core
        COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_CURRENT_SOURCE_DIR}/gui/pyvdm/ ${PYVDM_DIST_DIR}/gui
        COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_CURRENT_SOURCE_DIR}/assets/ ${PYVDM_DIST_DIR}/assets
)