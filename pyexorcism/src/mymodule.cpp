#include <Python.h>

// A simple function to be called from Python
static PyObject* say_hello(PyObject* self, PyObject* args) {
    return PyUnicode_FromString("Hello from C++!");
}

static PyMethodDef MyMethods[] = {
    {"say_hello", say_hello, METH_NOARGS, "Say hello from C++"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef mymodule = {
    PyModuleDef_HEAD_INIT,
    "mymodule",   // Module name
    NULL,         // Module docstring
    -1,           // Size of per-interpreter state of the module
    MyMethods
};

PyMODINIT_FUNC PyInit_mymodule(void) {
    return PyModule_Create(&mymodule);
}
