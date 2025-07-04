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
import gen_qc.py


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

def generate_esop_expression(variables, terms=4, 
                             prob_2=1.0, prob_3=1.0, prob_more=1.0):
    """
    Generate an ESOP (Exclusive Sum of Products) expression as a string.
    - variables: list of variable names (e.g., ['a', 'b', 'c', 'd'])
    - terms: number of product terms in the ESOP
    - prob_2: relative probability of picking a 2-literal product (default 1.0)
    - prob_3: relative probability of picking a 3-literal product (default 1.0)
    - prob_more: relative probability of picking a >3-literal product (default 1.0)
    
    Returns:
        A tuple of two strings:
        - ESOP of cubes with 3 or fewer literals
        - ESOP of the rest (cubes with more than 3 literals)
    """
    n_vars = len(variables)
    min_lits = 2
    max_lits = n_vars if n_vars > 3 else 3

    weightings = []
    sizes = []
    if n_vars >= 2:
        sizes.append(2)
        weightings.append(prob_2)
    if n_vars >= 3:
        sizes.append(3)
        weightings.append(prob_3)
    if n_vars > 3:
        sizes.append(random.randint(4, n_vars))
        weightings.append(prob_more)
        
    # Normalize weights
    total = sum(weightings)
    if total == 0:
        weightings = [1] * len(weightings)
        total = sum(weightings)
    norm_weights = [w / total for w in weightings]

    def random_term():
        k = random.choices(sizes, weights=norm_weights)[0]
        k = min(k, n_vars)
        vars_chosen = random.sample(variables, k)
        literals = []
        for v in vars_chosen:
            if random.choice([True, False]):
                literals.append(v)
            else:
                literals.append(f'~{v}')
        return ' & '.join(literals)

    terms_list = [f'({random_term()})' for _ in range(terms)]
    esop_expr = ' ^ '.join(terms_list)
    # Partition the ESOP into two parts as requested
    esop_3_or_less, esop_more = partition_esop(esop_expr)
    return esop_3_or_less, esop_more

def run_exp(test_type):
    if test_type == "3vars":
        esop3,esop4 = generate_esop_expression(vars, terms=5, prob_2=2.0, prob_3=1.0, prob_more=0)
    elif test_type == "3vars_reorder":
        esop3,esop4 = generate_esop_expression(vars, terms=5, prob_2=2.0, prob_3=1.0, prob_more=0)
        qk_str      = esop3 + esop4
        pro_str     = esop3 + esop4 #DCTODO
    elif test_type == "4vars":
        esop3,esop4 = generate_esop_expression(vars, terms=5, prob_2=1.0, prob_3=1.0, prob_more=1.0)

    pro_qc = gen_qc(esop3, esop4, test_type)
    qk_qc  = PhaseOracle(qk_str)
