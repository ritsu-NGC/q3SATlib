cmake_minimum_required(VERSION 3.14)
# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(APPLE)
  set(CMAKE_MODULE_LINKER_FLAGS "${CMAKE_MODULE_LINKER_FLAGS} -undefined dynamic_lookup")
endif()



add_executable(esop_to_qasm
  ${CMAKE_CURRENT_SOURCE_DIR}/esop_to_qasm.cpp
)
# for each target that uses it:

target_link_libraries(esop_to_qasm
  PRIVATE
    caterpillar
    tweedledum
)
target_link_libraries(esop_to_qasm PRIVATE z3)

target_compile_definitions(esop_to_qasm PRIVATE USE_Z3)
# Put the binary in the top-level build folder (convenient to run)
set_target_properties(esop_to_qasm PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
)
