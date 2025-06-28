#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "exorcism/exorcism.hpp"  // or wherever the entrypoint is

namespace py = pybind11;

// Example function: wrap string-based ESOP minimization
std::string minimize_pla(const std::string& pla_text) {
    // Create a temporary file or stringstream interface to the EXORCISM library
    // This is a placeholder: you must hook into actual exorcism C++ APIs
    return exorcism::minimize(pla_text);  // Pseudo-code
}

PYBIND11_MODULE(pyexorcism, m) {
    m.def("minimize_pla", &minimize_pla, "Minimize a PLA string using EXORCISM");
}
