#include "pyexorcism.hpp"
#include <pybind11/pybind11.h>


PYBIND11_MODULE(_pyexorcism, m) {
    m.doc() = "Example module";
    m.def("pyexorcism", &pyexorcism::pyexorcism, "Runs pyexorcism: string pyexorcism(string)");
}
