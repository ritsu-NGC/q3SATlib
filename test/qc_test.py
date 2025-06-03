import logging
import os
import sys
#import graphviz

import pytest
from qiskit import QuantumCircuit
from qiskit.circuit.library import PhaseOracle
#from qiskit.circuit import classical_function,  Int1

sys.path.append(os.path.join('../src'))
print(sys.path)

from mqt import qcec
from gen_qc import *
from quantumcircuit import *

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
        print("DCDEBUG" + str(results))

        assert str(results.equivalence) == "equivalent" or str(results.equivalence) == "equivalent_up_to_global_phase", (results)

    def test_build_qc(self):
        func = "xa | xb | xc"
        oracle = PhaseOracle(func)
        qc_args = {};
        qc_args["func"] = "x1 & x2 & x3";
        act_qc = main(func)
        
        results = qcec.verify(oracle,act_qc)


        print("DCDEBUG" + str(results))

        assert str(results.equivalence) == "equivalent", (results)

    # def test_ccz(self):
    #     qr = QuantumRegister(3,'x')
    #     fr = QuantumRegister(1,'f')

    #     qc = QuantumCircuit(qr,fr)
    #     qc.ccz(qr[0],qr[1],qr[2])
    #     qc_args = {};
    #     qc_args["func"] = "x1 & x2 & x3";
    #     act_qc = build_qc(qc_args)
    #     results = qcec.verify(qc,act_qc)
    #     print("DCDEBUG" + str(results.equivalence))
    #     assert str(results.equivalence) == "equivalent", (results)
