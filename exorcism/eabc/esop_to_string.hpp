#pragma once
#include <string>
#include <vector>
#include <sstream>

// Given bits and mask (as in Exorcism), with nVars variables, produce a C-like cube string
inline std::string cube_to_string(uint32_t bits, uint32_t mask, int nVars) {
    std::vector<std::string> literals;
    for (int v = 0; v < nVars; ++v) {
        if (!(mask & (1u << v))) continue; // don't-care
        if (bits & (1u << v))
            literals.push_back("x" + std::to_string(v));
        else
            literals.push_back("!x" + std::to_string(v));
    }
    if (literals.empty()) return "1"; // constant 1 cube
    std::ostringstream oss;
    for (size_t i = 0; i < literals.size(); ++i) {
        if (i > 0) oss << " & ";
        oss << literals[i];
    }
    return oss.str();
}

// Collect all cubes into a C-like ESOP string as in (cube1) ^ (cube2) ^ (cube3)
inline std::string cubes_to_esop_string(const std::vector<std::string>& cubes) {
    if (cubes.empty()) return "";
    std::ostringstream oss;
    for (size_t i = 0; i < cubes.size(); ++i) {
        if (i > 0) oss << " ^ ";
        oss << "(" << cubes[i] << ")";
    }
    return oss.str();
}
