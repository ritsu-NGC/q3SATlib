#define PY_SSIZE_T_CLEAN
#include <string>
#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include "eabc/exor.h"
#include "exor.cpp"
#include <string>
#include <vector>
#include <sstream>
#include <cctype>
#include <cassert>

#include "esop_parser.cpp"

//#include "exorcism/eabc/exor.h"
//#include "exorcism/esop_parser.cpp"

// Declare EXORCISM main (you may need to change this name)
int exorcism_main(const std::string& esop, int nVars) {
  abc::exorcism::Vec_Wec_t * vEsop;
  int         ret;
  
  vEsop = parse_esop(esop,nVars);
  ret   = Abc_ExorcismMain(vEsop,nVars,1,"file.pla",1,0,2**nVars,0);
  vEsop.free()
}


// Wrapper function for Python
static PyObject* pyexorcism_run(PyObject* self, PyObject* args) {
    const char* input_file;
    const char* output_file;
    const char* esop;
    const int argc;
    int result;

    if (!PyArg_ParseTuple(args, "ss", &input_file, &output_file))
        return NULL;

    // Simulate CLI args
    // char* argv[] = {
    //     "exorcism",
    //     "-t",                  // for ESOP
    //     (char*)input_file,
    //     "-o",
    //     (char*)output_file,
    //     NULL
    // };
    argc = 5;
    esop = "x1x2 ^ x2x3^ x3x4 ^ x4x5 ^ x5x1"
    result = exorcism_main(esop, 5);

    return PyLong_FromLong(result);
}

// Define methods
static PyMethodDef ExorcismMethods[] = {
    {"run", pyexorcism_run, METH_VARARGS, "Run EXORCISM on a PLA file"},
    {NULL, NULL, 0, NULL}
};

// Define module
static struct PyModuleDef exorcismmodule = {
    PyModuleDef_HEAD_INIT,
    "pyexorcism",
    NULL,
    -1,
    ExorcismMethods
};

// Module init
PyMODINIT_FUNC PyInit_pyexorcism(void) {
    return PyModule_Create(&exorcismmodule);
}
// Utility: trim whitespace
