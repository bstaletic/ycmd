#include <Python.h>

int main() {
        Py_Initialize();
        PyObject* ua = PyUnicode_Decode("a", 1, "latin1", NULL);
        PyObject* ba = PyUnicode_AsEncodedString(ua, "latin1", NULL);
        Py_XDECREF(ba);
        Py_XDECREF(ua);
        Py_Finalize();
}
