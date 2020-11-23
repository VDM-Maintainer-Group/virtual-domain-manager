cmake_minimum_required(VERSION 3.10)
#specify the C++ standard
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED True)


project(virtual-domain-manager)

#claim building dependency
find_package(python3 REQUIRED)
find_package(python3-pip REQUIRED)

#default configurations
set(CONFIG_DIR "$HOME/.vdm")
set(INSTALL_DIR "/opt/vdm")
set(WORKSPACE_DIR "$HOME/VDM")
set(PLUGINS_DIR "$HOME/.vdm/plugins")

# vdm core build
include_directories(assets)
include_directories(interface)
add_subdirectory(capability)
add_subdirectory(core)

# vdm optional build
add_subdirectory(gui)
#add_executable






