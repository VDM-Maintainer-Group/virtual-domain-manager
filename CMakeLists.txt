cmake_minimum_required(VERSION 3.12) #for FindPython feature
#specify the C++ standard
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED True)

project(virtual-domain-manager)
find_package(Python REQUIRED
            COMPONENTS Interpreter Development)

#default configurations
file(READ "VERSION" ver)
string(REGEX MATCH "VERSION_MAJOR[ \t]*=[ \t]*([0-9]*)" _ ${ver})
set(_ver_major ${CMAKE_MATCH_1})
string(REGEX MATCH "VERSION_MINOR[ \t]*=[ \t]*([0-9]*)" _ ${ver})
set(_ver_minor ${CMAKE_MATCH_1})
string(REGEX MATCH "VERSION_PATCH[ \t]*=[ \t]*([0-9]*)" _ ${ver})
set(_ver_patch ${CMAKE_MATCH_1})
#
set(VDM_VERSION ${_ver_major}.${_ver_minor}.${_ver_patch})
# set(ENV{CARGO_PKG_VERSION} ${VDM_VERSION})
set(VDM_INSTALL_DIR "/opt/vdm")

# vdm capability build
# add_subdirectory(capability)

# vdm daemon build
include(ExternalProject)
ExternalProject_Add(
        daemon
        SOURCE_DIR ${PROJECT_SOURCE_DIR}/daemon
        CONFIGURE_COMMAND ""#pip3 install maturin
        BUILD_IN_SOURCE true
        BUILD_ALWAYS true
        BUILD_COMMAND cargo build --release
        # BUILD_COMMAND python3 -m maturin build --release --manylinux off --out ${CMAKE_CURRENT_BINARY_DIR}
        INSTALL_COMMAND "" #pip3 install -U ${CMAKE_CURRENT_BINARY_DIR}/*linux*.whl
        TEST_COMMAND "" #cargo test
        LOG_BUILD ON)

# vdm core build
include_directories(assets)
include_directories(interface)
add_subdirectory(core)

# vdm gui build
add_subdirectory(gui)

# pyvdm build: "pyvdm.interface" + "pyvdm.core" + "pyvdm.gui"
set(PYVDM_DIST_DIR ${CMAKE_CURRENT_BINARY_DIR}/pyvdm)
file(GLOB PYVDM_API "./interface/*.py")
file(GLOB PYVDM_WRAPPER "./capability/__wrapper__/serde_wrapper_py/wrapper.py")
file(GLOB PYVDM_SBS "./capability/build.py")
set(PYVDM_DAEMON "./daemon/target/release/libvdm_capability_daemon.so")
add_custom_target(build-pyvdm
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        COMMAND ${CMAKE_COMMAND} -E rm -rf ${PYVDM_DIST_DIR}
        # copy and gather files
        COMMAND ${CMAKE_COMMAND} -E make_directory ${PYVDM_DIST_DIR}/interface
        COMMAND ${CMAKE_COMMAND} -E copy ${PYVDM_API} ${PYVDM_DIST_DIR}/interface
        COMMAND ${CMAKE_COMMAND} -E copy ${PYVDM_WRAPPER} ${PYVDM_DIST_DIR}/interface
        COMMAND ${CMAKE_COMMAND} -E copy ${PYVDM_SBS} ${PYVDM_DIST_DIR}
        COMMAND ${CMAKE_COMMAND} -E copy_directory "./core/pyvdm/" ${PYVDM_DIST_DIR}/core
        COMMAND ${CMAKE_COMMAND} -E copy ${PYVDM_DAEMON} ${PYVDM_DIST_DIR}/daemon/vdm_capability_daemon.so
        COMMAND ${CMAKE_COMMAND} -E copy_directory "./gui/pyvdm/" ${PYVDM_DIST_DIR}/gui
        COMMAND ${CMAKE_COMMAND} -E copy_directory "./assets/" ${PYVDM_DIST_DIR}/assets
        #
        COMMAND ${CMAKE_COMMAND} -E touch ${PYVDM_DIST_DIR}/__init__.py
        COMMAND ${CMAKE_COMMAND} -E touch ${PYVDM_DIST_DIR}/daemon/__init__.py
        COMMAND ${CMAKE_COMMAND} -E echo "__version__ = \\\"${VDM_VERSION}\\\"" >  ${PYVDM_DIST_DIR}/__init__.py
        #
        COMMAND python3 setup.py bdist_wheel
)
