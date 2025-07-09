#include <pybind11/pybind11.h>
#include <pybind11/functional.h>
//DCDEBUG #include "exorcism.h"
#include "eabc/exor.h"
#include "eabc/vecWec.h"
#include "eabc/vecInt.h"
#include "eabc/esop_to_string.hpp"

namespace py = pybind11;

#include <string>
#include <sstream>
#include <iostream>
#include <vector>
#include <cassert>
#include <cctype>
#include <algorithm>

// Trim whitespace from both ends
static inline std::string trim(const std::string& s) {
    size_t start = s.find_first_not_of(" \t\n\r");
    size_t end = s.find_last_not_of(" \t\n\r");
    return (start == std::string::npos) ? "" : s.substr(start, end - start + 1);
}

// Parse a literal like "x2" or "!x1"
static inline int parse_literal(const std::string& lit) {
    bool neg = false;
    size_t idx = 0;
    if ((lit[idx] == '!') || (lit[idx] == '~')) {
        neg = true;
        ++idx;
    }
    assert(lit.substr(idx, 1) == "x");
    idx++;
    int var_idx = 0;
    while (idx < lit.size() && std::isdigit(lit[idx])) {
        var_idx = var_idx * 10 + (lit[idx] - '0');
        ++idx;
    }
    return 2 * var_idx + (neg ? 1 : 0);
}

// Parse a cube like "x0 & !x1 & x2"
static void parse_cube_to_vec(const std::string& cube, abc::exorcism::Vec_Int_t* vCube) {
    std::istringstream iss(cube);
    std::string lit;
    while (iss) {
        std::getline(iss, lit, '&');
        lit = trim(lit);
        if (!lit.empty())
            abc::exorcism::Vec_IntPush(vCube, parse_literal(lit));
    }
    // Output: for single-output ESOP, output 0 is encoded as -1 (as in EXORCISM)
    abc::exorcism::Vec_IntPush(vCube, -1);
}

// Parse a C-like ESOP string into a Vec_Wec_t*
abc::exorcism::Vec_Wec_t* parse_esop(const std::string& esop) {
    abc::exorcism::Vec_Wec_t* vEsop = abc::exorcism::Vec_WecAlloc(8); // Start with capacity 8 cubes
    std::istringstream iss(esop);
    std::string cube;
    while (std::getline(iss, cube, '^')) {
        // Remove parentheses and whitespace
        cube.erase(std::remove(cube.begin(), cube.end(), '('), cube.end());
        cube.erase(std::remove(cube.begin(), cube.end(), ')'), cube.end());
        cube = trim(cube);
        if (cube.empty()) continue;
        abc::exorcism::Vec_Int_t* vCube = abc::exorcism::Vec_WecPushLevel(vEsop);  // allocate new level
        parse_cube_to_vec(cube, vCube);
    }
    return vEsop;
}

// Print the contents of a abc::exorcism::Vec_Wec_t for inspection
void print_vecwec(abc::exorcism::Vec_Wec_t* vEsop) {
    for (int i = 0; i < vEsop->nSize; ++i) {
        abc::exorcism::Vec_Int_t* vCube = (abc::exorcism::Vec_Int_t*)((char*)vEsop->pArray + i * sizeof(abc::exorcism::Vec_Int_t));
        std::cout << "Cube " << i << ": [";
        for (int j = 0; j < vCube->nSize; ++j) {
            std::cout << vCube->pArray[j];
            if (j < vCube->nSize - 1)
                std::cout << ", ";
        }
        std::cout << "]" << std::endl;
    }
}


// This wrapper does NOT expose Vec_Wec_t to Python directly.
// For a true minimal example, we require the user to pass a nullptr for vEsop.
int exorcism_null(
    std::string esop_str,
    int nIns,
    int nOuts,
    std::function<void(uint32_t, uint32_t)> onCube,
    int Quality,
    int Verbosity,
    int nCubesMax,
    int fUseQCost)
{
  std::vector<std::string> cube_strings;

  auto on_cube = [&](uint32_t bits, uint32_t mask) {
    cube_strings.push_back(cube_to_string(bits, mask, nIns));
  };

  //DCDEBUGstd::string esop_str = "(x0 & !x1 & x2) ^ (!x0 & x1 & !x2) ^ (x1 & x2)";
  abc::exorcism::Vec_Wec_t* vEsop = parse_esop(esop_str);
  print_vecwec(vEsop);
  // WARNING: This only works for demonstration if Abc_ExorcismMain tolerates nullptr for vEsop!
  return abc::exorcism::Abc_ExorcismMain(vEsop, nIns, nOuts, onCube, Quality, Verbosity, nCubesMax, fUseQCost);
}

PYBIND11_MODULE(exorcism, m) {
    m.def("exorcism", &exorcism_null,
        py::arg("esop_str"),
	py::arg("nIns"),
        py::arg("nOuts"),
        py::arg("onCube"),
        py::arg("Quality") = 0,
        py::arg("Verbosity") = 0,
        py::arg("nCubesMax") = 0,
        py::arg("fUseQCost") = 0,
        "Minimal Python wrapper for Abc_ExorcismMain (demo only: does not pass ESOP)");
}
