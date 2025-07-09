from qiskit import QuantumCircuit,QuantumRegister

from dd import cudd
from textwrap import dedent
from qiskit import transpile
import sys
import os



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
from gen_n4 import lut_node
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'quantum_compiler'))
from n_qubit_esop_builder import build_esop_circuit

def partition_esop(esop_str):
    cubes = re.findall(r'\([^\(\)]*\)', esop_str)
    cubes_3_or_less = []
    cubes_more = []
    
    for cube in cubes:
        literals = [lit.strip() for lit in cube[1:-1].split('&')]
        num_lits = len(literals)
        if num_lits <= 3:
            cubes_3_or_less.append(cube)
        else:
            cubes_more.append(cube)
    esop_3_or_less = ' ^ '.join(cubes_3_or_less)
    esop_more = ' ^ '.join(cubes_more)
    return esop_3_or_less, esop_more

def parse_cube(cube_str):
    """
    Given a cube string like '(a & ~b & c)', return a list of variable names: ['a', 'b', 'c']
    Ignores negation (~).
    """
    # Remove parentheses
    #inner = cube_str.strip()[1:-1]
    
    # Split on '&', strip whitespace, remove any '~'
    variables = []
    for literal in cube_str.split('&'):
        literal = literal.strip()
        # Remove leading '~' if present
        var = literal.lstrip('~').strip()
        if var:  # skip empty
            variables.append(var)
    return variables

def extract_variables(boolean_expr):
    """
    Given a Boolean function string, return a sorted list of unique variable names.
    Ignores Python keywords and Boolean operators.
    """
    # Matches identifiers (variable names), e.g., a, x1, var_name
    # Avoids matching Python keywords/operators like 'and', 'or', 'not'
    # You can tweak the regex to disallow names like 'and', 'or', 'not' if needed

    # Find all identifiers (optionally preceded by ~)
    tokens = re.findall(r'~?\b([A-Za-z_]\w*)\b', boolean_expr)
    # Remove duplicates and sort
    unique_vars = sorted(set(tokens))
    return unique_vars

def gen_qc(esop3, esop4, vars_list, test_type):
    #DCTODO
    qc = QuantumCircuit()

    #Gen RTOF LUT
    var_dict = {var_name: index for index, var_name in enumerate(vars_list)}
    #run T-PAR
    qc3 = gen_n3(esop3)
    qc4 = gen_n4(esop4,var_dict)
    qc  = qc4.compose(qc3)
    
    return qc4.compose(qc3)
    
def gen_n3(esop_str):
    """
    Generate a quantum circuit from a 3-variable-or-less ESOP string using the n_qubit_esop_builder.
    """
    # Call the builder function and return the circuit
    circuit = build_esop_circuit(esop_str)
    return circuit

def gen_n4(s,var_dict):
    qc = QuantumCircuit(len(var_dict.keys()) + 1)
    cubes = [cube.strip() for cube in re.split(r'\s*(?:\^|⊕)\s*', s) if cube.strip()]
    for cube in cubes:
        print("DCDEBUG gen_n4 cube " + cube)
        cube = re.sub(r'\(([^)]+)\)', r'\1', cube)
        cz,lits = gen_n4_cube(cube)
        #look up indices of 
        ctrl_connections = [var_dict[var_name] + 1 for var_name in lits]
        connections = [0] + ctrl_connections
        print("DCDEBUG gen_n4 " + str(connections))
        qc = qc.compose(cz,connections)
    return qc
        
def gen_n4_cube(s):
    #DCTODO
    lits = extract_variables(s)
    qc = QuantumCircuit(len(lits) + 1)

    #Gen RTOF LUT
    c = lut_node("node0",lits,"y")
    print("DCDEBUG gen_n4_cube " + s)
    c.add_sop_expr(s)
    result = c.synth()
    qc = qc.compose(result[0])
    qc.z(0)
    qc = qc.compose(result[0].inverse())

    return qc,lits


def write_qc_format(circuit: QuantumCircuit, filename: str):
    """Write a Qiskit QuantumCircuit to a .qc format file"""
    gate_map = {
        'cx': 'tof',
        'ccx': 'tof',
        'x': 'X',
        'h': 'H',
        't': 'T',
        'tdg': 'T*',
        'z': 'Z',
        'y': 'Y',
        's': 'P',
        'sdg': 'P*',
        # Add more as needed
    }
    with open(filename, 'w') as f:
        qubit_indices = [str(i) for i in range(circuit.num_qubits)]
        f.write(f".v {' '.join(qubit_indices)}\n")
        f.write(f".i {' '.join(qubit_indices)}\n")
        f.write(f".o {' '.join(qubit_indices)}\n")                
        f.write("\nBEGIN\n\n")
        for inst, qargs, cargs in circuit.data:
            name = inst.name.lower()
            if name in gate_map:
                gate_label = gate_map[name]
                qubits = [circuit.find_bit(q).index for q in qargs]
                f.write(f"{gate_label} {' '.join(map(str, qubits))}\n")
            else:
                print(f"Warning: Gate {name} not supported in .qc format")
        f.write(f"\nEND")

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
                     


