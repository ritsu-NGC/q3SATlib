import logging
import os
import sys
#import graphviz

import pytest
from qiskit import QuantumCircuit
#from qiskit.circuit import classical_function,  Int1

sys.path.append(os.path.join('../src'))
print(sys.path)

from mqt import qcec
from gen_qc import *

class CircuitToLogicTests(object):
    def test_ccz(self):
        qr = QuantumRegister(3,'x')
        fr = QuantumRegister(1,'f')

        qc = QuantumCircuit(qr,fr)
        qc.ccz(qr[0],qr[1],qr[2])
        qc_args = {};
        qc_args["func"] = "x1 & x2 & x3";
        act_qc = build_qc(qc_args)
        results = qcec.verify(qc,act_qc)
        print("DCDEBUG" + str(results.equivalence))
        assert str(results.equivalence) == "equivalent", (results)

    def test_ccz(self):
        qr = QuantumRegister(3,'x')
        fr = QuantumRegister(1,'f')

        qc = QuantumCircuit(qr,fr)
        qc.ccz(qr[0],qr[1],qr[2])
        qc_args = {};
        qc_args["func"] = "x1 & x2 & x3";
        act_qc = build_qc(qc_args)
        results = qcec.verify(qc,act_qc)
        print("DCDEBUG" + str(results.equivalence))
        assert str(results.equivalence) == "equivalent", (results)
