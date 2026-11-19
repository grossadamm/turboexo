cmake_minimum_required(VERSION 3.16)
project(cluster_core_tests LANGUAGES CXX)

enable_testing()

add_executable(cluster_core_tests
    core_tests.cpp
    ../core/calibration.cpp
    ../core/controls.cpp
    ../core/history.cpp
    ../core/protocol.cpp
    ../core/replay.cpp
)
target_compile_features(cluster_core_tests PRIVATE cxx_std_17)
set_target_properties(cluster_core_tests PROPERTIES CXX_EXTENSIONS OFF)
target_include_directories(cluster_core_tests PRIVATE ../include)

option(CLUSTER_SANITIZE "Enable address and undefined-behavior sanitizers" ON)
if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options(cluster_core_tests PRIVATE -Wall -Wextra -Wpedantic -Werror)
    if(CLUSTER_SANITIZE)
        target_compile_options(cluster_core_tests PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
        target_link_options(cluster_core_tests PRIVATE -fsanitize=address,undefined)
    endif()
endif()
add_test(NAME cluster_core_tests COMMAND cluster_core_tests)
