cmake_minimum_required(VERSION 3.22)
set(IDF_TARGET esp32p4)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
# The board has no radio. Limit the build to main and its dependency graph.
idf_build_set_property(MINIMAL_BUILD ON)
project(turboexo_cluster)
