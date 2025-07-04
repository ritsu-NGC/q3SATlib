from qiskit import QuantumCircuit,QuantumRegister
from dd import cudd
from textwrap import dedent
from qiskit import transpile

#DCDEBUG
import tracemalloc
import linecache
import os
import numpy
import numpy.linalg
import time
import subprocess

#from src.circuit_to_logic import *
import logging
import os
import sys
import gc
#import memory-profiler
import random
import re
#import pyexorcism

def partition_esop(esop_str):
    # Find all cubes (parenthesized terms)
    cubes = re.findall(r'\([^\(\)]*\)', esop_str)
    cubes_3_or_less = []
    cubes_more = []
    
    for cube in cubes:
        # Count the number of variable literals (i.e. variable names, possibly with ~)
        # Split on & and strip whitespace
        literals = [lit.strip() for lit in cube[1:-1].split('&')]
        num_lits = len(literals)
        if num_lits <= 3:
            cubes_3_or_less.append(cube)
        else:
            cubes_more.append(cube)

    # Rebuild ESOP expressions
    esop_3_or_less = ' ^ '.join(cubes_3_or_less)
    esop_more = ' ^ '.join(cubes_more)
    return esop_3_or_less, esop_more

def run_tpar(qc,filename):
    circ_name = filename + ".qc"
    write_qc_format(qc,circ_name)

    result = subprocess.run(["./t-par",circ_name], stdout=filename + ".log",capture_output=False, text=True)

def gen_qc(esop3, esop4, test_type):
    #DCTODO
    qc = QuantumCircuit()

    #Gen RTOF LUT
    
    #run T-PAR
    qc3 = gen_n3(esop3)
    qc4 = gen_n4(esop4)
    qc  = qc3 + qc4
    
    return qc3 + qc4
    
def gen_n3(s):
    #CHITRANSHU TODO
    qc = QuantumCircuit()
    return qc

def gen_n4(s):
    #DCTODO
    qc = QuantumCircuit()

    #Gen RTOF LUT
    
    #run T-PAR


    return qc

def write_qc_format(circuit: QuantumCircuit, filename: str):
    """Write a Qiskit QuantumCircuit to a .qc format file"""
    gate_map = {
        'cx': 'CNOT',
        'ccx': 'TOF',
        'x': 'X',
        'h': 'H',
        't': 'T',
        'tdg': 'TDG',
        'z': 'Z',
        'y': 'Y',
        's': 'S',
        'sdg': 'SDG',
        # Add more as needed
    }
    with open(filename, 'w') as f:
        for inst, qargs, cargs in circuit.data:
            name = inst.name.lower()
            if name in gate_map:
                gate_label = gate_map[name]
                qubits = [circuit.find_bit(q).index for q in qargs]
                f.write(f"{gate_label} {' '.join(map(str, qubits))}\n")
            else:
                print(f"Warning: Gate {name} not supported in .qc format")

# # Example usage:
# qc = QuantumCircuit(3)
# qc.h(0)
# qc.cx(0, 1)
# qc.ccx(0, 1, 2)
# write_qc_format(qc, "output.qc")

def build_qc(qc_args):
    qr_out = QuantumRegister(3)
    p_out  = QuantumRegister(4,'p')
    qc_out = QuantumCircuit(qr_out,p_out)
    qc_out.ccz(qr_out[0],qr_out[1],qr_out[2])
    return qc_out
                     



