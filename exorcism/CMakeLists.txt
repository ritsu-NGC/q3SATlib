cmake_minimum_required (VERSION 3.6)

project(libabcesop LANGUAGES CXX)

include_directories(${PROJECT_SOURCE_DIR})
include_directories(${PROJECT_SOURCE_DIR}/eabc)

file(GLOB ABC_SRC *.cpp)

# Surpress warnings in external library
if (UNIX)
    add_compile_options("-w")
elseif (MSVC)
    string(REPLACE "/W3" "/w" CMAKE_CXX_FLAGS ${CMAKE_CXX_FLAGS})
endif()

if (STATIC_LIBABC)
    add_library(libabcesop STATIC EXCLUDE_FROM_ALL ${ABC_SRC})
    set_property(TARGET libabcesop PROPERTY OUTPUT_NAME libabcesop)
else()
    add_library(libabcesop SHARED EXCLUDE_FROM_ALL ${ABC_SRC})
    set_property(TARGET libabcesop PROPERTY OUTPUT_NAME libabcesop)
    set_property(TARGET libabcesop PROPERTY POSITION_INDEPENDENT_CODE ON)
endif()
target_include_directories(libabcesop INTERFACE ${PROJECT_SOURCE_DIR})

if (UNIX)
    target_compile_definitions(libabcesop PUBLIC "LIN64" ABC_NO_USE_READLINE)
elseif(WIN32)
    target_compile_definitions(libabcesop PUBLIC ABC_USE_NO_READLINE NOMINMAX  WIN32_NO_DLL _CRT_SECURE_NO_WARNINGS)
endif()

# ---------------- PYBIND11 WRAPPER SECTION ----------------

# Optionally, allow disabling the Python wrapper
option(BUILD_PYTHON "Build Python pybind11 wrapper" ON)

if (BUILD_PYTHON)
   if(PYTHON_INCLUDE_DIR)
      include_directories(${PYTHON_INCLUDE_DIR})
   endif()

    # Find pybind11 (requires it to be installed or available as submodule)
    find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
    find_package(pybind11 REQUIRED)

    # Add your wrapper source file here
    set(PYBIND11_WRAPPER exorcism_pybind.cpp)

    # Build the Python extension module
    pybind11_add_module(exorcism ${PYBIND11_WRAPPER})

    # Link the exorcism library to the Python module
    target_link_libraries(exorcism PRIVATE libabcesop)

    # Ensure include paths are set
    target_include_directories(exorcism PRIVATE ${PROJECT_SOURCE_DIR})

    # (Optional) Set properties for the module
    set_target_properties(exorcism PROPERTIES OUTPUT_NAME "exorcism")
endif()
