from qiskit import QuantumCircuit,QuantumRegister
from qiskit.circuit.library import TGate, HGate, SGate
#from qiskit.quantum_info.random import unitary_group
from dd import cudd
#from tweedledum.synthesis import linear_synth
from qiskit import transpile

#DCDEBUG
import tracemalloc
import linecache
import os
import numpy
import numpy.linalg
import time

#from src.circuit_to_logic import *
import logging
import os
import sys
import gc

controls = [0,1,2,3]


target = controls[0]
subcontrols = controls[:-1]
circuit = QuantumCircuit(len(subcontrols))
circuit.h(target)
# T on target
circuit.t(target)

# CNOT from last control to target
circuit.cx(target, subcontrols[-1])
# Tdg on target
circuit.tdg(subcontrols[-1])

# Recursively apply F on n-1 subcontrols
circuit.cx(subcontrols[-1],target)
circuit.cx(subcontrols[-2],subcontrols[-1])
circuit.t(subcontrols[-1])

# CNOT from last control to target
circuit.cx(subcontrols[-1], target)
# T on target
circuit.tdg(target)

# Recursively apply F on n-1 subcontrols
circuit.cx(subcontrols[-2],target)
circuit.tdg(target)
# H on target
circuit.h(target)
print(circuit)
cgate = circuit.to_gate()

new_circ = QuantumCircuit(4)
new_circ.h(target)
# T on target
new_circ.t(target)

# CNOT from last control to target
new_circ.cx(controls[-1], target)
# Tdg on target
new_circ.tdg(target)
print([target] + controls)
# Recursively apply F on n-1 controls
new_circ.append(cgate, controls[:-1])
new_circ.t(target)

# CNOT from last control to target
new_circ.cx(controls[-1], target)
# T on target
new_circ.tdg(target)

# Recursively apply F on n-1 controls
new_circ.append(cgate, controls[:-1])
new_circ.tdg(target)
# H on target
new_circ.h(target)

print(new_circ.decompose())
