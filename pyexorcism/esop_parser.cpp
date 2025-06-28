#include "eabc/exor.h"
//#include "eabc/vecWec.h"
#include <string>
#include <sstream>
#include <iostream>
#include <cassert>
#include <cctype>

// Utility: trim whitespace from both ends
static inline std::string trim(const std::string& s) {
    size_t start = s.find_first_not_of(" \t\n\r");
    size_t end = s.find_last_not_of(" \t\n\r");
    return (start == std::string::npos) ? "" : s.substr(start, end - start + 1);
}

// Parse a literal like "x2'" or "x0"
static inline int parse_literal(const std::string& lit) {
    assert(lit.size() >= 2 && lit[0] == 'x');
    size_t i = 1;
    int var_idx = 0;
    while (i < lit.size() && std::isdigit(lit[i])) {
        var_idx = var_idx * 10 + (lit[i] - '0');
        ++i;
    }
    bool neg = (i < lit.size() && lit[i] == '\'');
    return 2 * var_idx + (neg ? 1 : 0);
}

// Parse a cube like "x0 x1' x2"
static void parse_cube_to_vec(const std::string& cube, int nVars, abc::exorcism::Vec_Int_t* vCube) {
    std::istringstream iss(cube);
    std::string lit;
    while (iss >> lit) {
        abc::exorcism::Vec_IntPush(vCube, parse_literal(lit));
    }
    // Output: for single-output ESOP, output 0 is encoded as -1 (as in EXORCISM)
    abc::exorcism::Vec_IntPush(vCube, -1);
}

// Parse an ESOP string into a Vec_Wec_t*
abc::exorcism::Vec_Wec_t* parse_esop(const std::string& esop, int nVars) {
    abc::exorcism::Vec_Wec_t* vEsop = abc::exorcism::Vec_WecAlloc(8); // Start with capacity 8 cubes
    std::istringstream iss(esop);
    std::string cube;
    while (std::getline(iss, cube, '+')) {
        cube = trim(cube);
        if (cube.empty()) continue;
        abc::exorcism::Vec_Int_t* vCube = abc::exorcism::Vec_WecPushLevel(vEsop);  // allocate new level
        parse_cube_to_vec(cube, nVars, vCube);
    }
    return vEsop;
}

// Print the contents of a Vec_Wec_t for inspection
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

int main() {
    std::string esop_str = "x0 x1' x2 + x0' x1 x2' + x1 x2";
    int nVars = 3;
    abc::exorcism::Vec_Wec_t* vEsop = parse_esop(esop_str, nVars);

    // Print out the result
    print_vecwec(vEsop);

    // Cleanup: free vEsop if your API provides a function for this
    // Vec_WecFree(vEsop); // Uncomment if available

    return 0;
}
