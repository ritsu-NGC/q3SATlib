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
import gen_qc

def run_tpar(qc,filename):
    circ_name = filename + ".qc"
    write_qc_format(qc,circ_name)

    result = subprocess.run(["./t-par",circ_name], stdout=filename + ".log",capture_output=False, text=True)

def run_exp(test_type,runs):
    for i in range(1,runs):
        n         = 12    
        vars_list = [f'x{i}' for i in range(1, n + 1)]
        if test_type == "n3_2n":
            cubes       = 2**(n-1)
            esop3,esop4 = generate_esop_expression(vars_list, terms=cubes, prob_2=2.0, prob_3=1.0, prob_more=0)
        elif test_type == "n3_n":
            cubes       = n
            esop3,esop4 = generate_esop_expression(vars_list, terms=cubes, prob_2=2.0, prob_3=1.0, prob_more=0)
            qk_str      = esop3 + esop4
            pro_str     = esop3 + esop4 #DCTODO Scramble
        elif test_type == "scramble_2n":
            cubes       = 2**(n-1)
            esop3,esop4 = generate_esop_expression(vars_list, terms=cubes, prob_2=1.0, prob_3=1.0, prob_more=1.0)
        elif test_type == "scramble_n":
            cubes       = n
            esop3,esop4 = generate_esop_expression(vars_list, terms=cubes, prob_2=1.0, prob_3=1.0, prob_more=1.0)
        else:
            raise ValueError("Unknown test_type:" + test_type)

        pro_qc = gen_qc(esop3, esop4, vars_list, test_type)    
        qk_qc = PhaseOracle(qk_str)

        run_tpar(pro_qc,"pro_qc"+str(i))
        run_tpar(qk_qc,"qk_qc"+str(i))

    

    

