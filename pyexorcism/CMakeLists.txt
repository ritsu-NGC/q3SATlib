cmake_minimum_required(VERSION 3.15...3.26)

project(
  pyexorcism
  VERSION "0.1.0"
  LANGUAGES CXX)

include(GNUInstallDirs)

add_subdirectory(exorcism)
add_library(pyexorcism STATIC "${PROJECT_SOURCE_DIR}/src/pyexorcism.cpp")
set_target_properties(pyexorcism PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_link_libraries(pyexorcism PRIVATE exorcism) #DCTODO exorcism

target_include_directories(pyexorcism PRIVATE exorcism)



# define the C++ library "pyexorcism"
# add_library(pyexorcism SHARED "${PROJECT_SOURCE_DIR}/src/hello.cpp")




target_include_directories(
  pyexorcism PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>
               $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)

install(DIRECTORY "${PROJECT_SOURCE_DIR}/include/"
        DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})

# Standard installation subdirs for the C++ library are used. The files will end
# up in the specified subdirectories under the Python package root. For example,
# "<python package prefix>/pyexorcism/lib/" if the destination is "lib/".
#
# Installing the objects in the package provides encapsulation and will become
# important later for binary redistribution reasons.
install(
  TARGETS pyexorcism exorcism
  EXPORT pyexorcismTargets
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR})

# The CMake package config and target files are installed under the Python
# package root. This is necessary to ensure that all the relative paths in the
# helloTargets.cmake resolve correctly. It also provides encapsulation.
#
# The actual path used must be selected so that consuming projects can locate it
# via `find_package`. To support finding CMake packages in the Python package
# prefix, using `find_package`s default search path of
# `<prefix>/<name>/share/<name>*/cmake/` is reasonable. Adding the Python
# package installation prefix to CMAKE_PREFIX_PATH in combination with this path
# will allow `find_package` to find this package and any other package installed
# via a Python package if the CMake and Python packages are named the same.
set(PYEXORCISM_CMAKE_PACKAGE_INSTALL_SUBDIR "share/pyexorcism/cmake")

install(
  EXPORT pyexorcismTargets
  NAMESPACE pyexorcism::
  DESTINATION ${PYEXORCISM_CMAKE_PACKAGE_INSTALL_SUBDIR})

include(CMakePackageConfigHelpers)

write_basic_package_version_file(
  pyexorcismConfigVersion.cmake
  VERSION ${PROJECT_VERSION}
  COMPATIBILITY SameMinorVersion)

configure_package_config_file(
  "${PROJECT_SOURCE_DIR}/cmake/pyexorcismConfig.cmake.in" pyexorcismConfig.cmake
  INSTALL_DESTINATION ${PYEXORCISM_CMAKE_PACKAGE_INSTALL_SUBDIR})

install(FILES "${PROJECT_BINARY_DIR}/pyexorcismConfig.cmake"
              "${PROJECT_BINARY_DIR}/pyexorcismConfigVersion.cmake"
        DESTINATION ${PYEXORCISM_CMAKE_PACKAGE_INSTALL_SUBDIR})

# We are using the SKBUILD variable, which is defined when scikit-build is
# running the CMake build, to control building the Python wrapper. This allows
# the C++ project to be installed, standalone, when using the standard CMake
# build flow.
if(DEFINED SKBUILD)

  # call pybind11-config to obtain the root of the cmake package
  execute_process(COMMAND ${PYTHON_EXECUTABLE} -m pybind11 --cmakedir
                  OUTPUT_VARIABLE pybind11_ROOT_RAW)
  string(STRIP ${pybind11_ROOT_RAW} pybind11_ROOT)
  find_package(pybind11 REQUIRED PATHS ${pybind11_ROOT})
  #DCTODO find_package(pybind11 REQUIRED)

  pybind11_add_module(_pyexorcism MODULE
                      "${PROJECT_SOURCE_DIR}/src/pyexorcism/pyexorcism_py.cpp")

  target_link_libraries(_pyexorcism PRIVATE pyexorcism)

  # Installing the extension module to the root of the package
  install(TARGETS _pyexorcism DESTINATION .)

  configure_file("${PROJECT_SOURCE_DIR}/src/pyexorcism/__main__.py.in"
                 "${PROJECT_BINARY_DIR}/src/pyexorcism/__main__.py")

  install(FILES "${PROJECT_BINARY_DIR}/src/pyexorcism/__main__.py" DESTINATION .)

  # The extension module must load the pyexorcism library as a dependency when the
  # extension module is loaded. The easiest way to locate the pyexorcism library is
  # via RPATH. Absolute RPATHs are possible, but they make the resulting
  # binaries not redistributable to other Python installations (conda is broke,
  # wheel reuse is broke, and more!).
  #
  # Placing the pyexorcism library in the package and using relative RPATHs that
  # doesn't point outside of the package means that the built package is
  # relocatable. This allows for safe binary redistribution.
  if(APPLE)
    set_target_properties(
      _pyexorcism PROPERTIES INSTALL_RPATH "@loader_path/${CMAKE_INSTALL_LIBDIR}")
  else()
    set_target_properties(_pyexorcism PROPERTIES INSTALL_RPATH
                                            "$ORIGIN/${CMAKE_INSTALL_LIBDIR}")
  endif()

endif()
