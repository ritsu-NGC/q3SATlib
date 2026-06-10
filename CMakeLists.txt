cmake_minimum_required(VERSION 3.14)
project(q3SATlib LANGUAGES CXX)

add_compile_definitions(USE_Z3)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)
set(CMAKE_CXX_EXTENSIONS False)

include(FetchContent)

# --- Fetch caterpillar, but do NOT build its tests/examples/experiments ---
set(CATERPILLAR_TEST OFF CACHE BOOL "" FORCE)
set(CATERPILLAR_EXAMPLES OFF CACHE BOOL "" FORCE)
set(CATERPILLAR_EXPERIMENTS OFF CACHE BOOL "" FORCE)
set(CATERPILLAR_Z3 ON CACHE BOOL "" FORCE)
FetchContent_Declare(
  caterpillar
  GIT_REPOSITORY https://github.com/gmeuli/caterpillar.git
  GIT_TAG        master
)
FetchContent_MakeAvailable(caterpillar)

# caterpillar's interface target links mockturtle, tweedledum, json —
# but not 'ez', which is needed when including xag_mapping_strategy.hpp.
target_link_libraries(caterpillar INTERFACE ez)


# # --- Fetch fmt (so you don't need it installed system-wide) ---
# # Tweedledum's QASM writer includes <fmt/format.h>.
# FetchContent_Declare(
#   fmt
#   GIT_REPOSITORY https://github.com/fmtlib/fmt.git
#   GIT_TAG        10.2.1
# )
# FetchContent_MakeAvailable(fmt)

add_subdirectory(src)
