from skbuild import setup

setup(
    name="pyexorcism-cmake-package",
    version="0.1.0",
    packages=["pyexorcism"],
    package_dir={"": "src"},
    cmake_install_dir="src/pyexorcism",
)

# When building extension modules `cmake_install_dir` should always be set to the
# location of the package you are building extension modules for.
# Specifying the installation directory in the CMakeLists subtley breaks the relative
# paths in the helloTargets.cmake file to all of the library components.
