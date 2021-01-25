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
set(PYVDM_INSTALL_DIR ${Python_SITELIB}/pyvdm)
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
INSTALL(FILES ${PYVDM_API}
        DESTINATION ${PYVDM_INSTALL_DIR}/interface)
INSTALL(DIRECTORY "./core/pyvdm/"
        DESTINATION ${PYVDM_INSTALL_DIR}/core)
INSTALL(DIRECTORY "./assets"
        DESTINATION ${PYVDM_INSTALL_DIR}/assets)
INSTALL(DIRECTORY "./gui/pyvdm/"
        DESTINATION ${PYVDM_INSTALL_DIR}/gui)
add_custom_target(uninstall COMMAND sudo rm -rf ${PYVDM_INSTALL_DIR})