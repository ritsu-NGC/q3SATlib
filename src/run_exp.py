from qiskit import QuantumCircuit,QuantumRegister,transpile
from qiskit.circuit.library import PhaseOracle
from qiskit.qasm2 import dump
from qiskit.synthesis.boolean.boolean_expression_synth import synth_phase_oracle_from_esop


from dd import cudd
from dd.autoref import BDD
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
from gen_qc import partition_esop,gen_qc,write_qc_format,gen_n4_cube
from exorcism import exorcism


def run_tpar(qc,filename):
    circ_name = filename + ".qc"
    write_qc_format(qc,circ_name)
    with open(filename + ".log","w") as logfile, open(filename + ".qc","r") as infile:
        result = subprocess.run(["./t-par/t-par"], stdin=infile, stdout=logfile,capture_output=False, text=True)


def normalize_cube(cube):
    """
    Returns a normalized, hashable string for a cube, e.g. (a & ~b & c) => ('a','~b','c')
    Ignores literal order.
    """
    literals = [lit.strip() for lit in cube[1:-1].split('&')]
    # Sort literals to make order unimportant
    return tuple(sorted(literals))

def generate_esop_expression(variables, min_terms=0, max_terms=4, 
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
    total = sum(weightings)
    if total == 0:
        weightings = [1] * len(weightings)
        total = sum(weightings)
    norm_weights = [w / total for w in weightings]

    # Uniquify cubes using a set
    seen_cubes = set()
    unique_terms = []
    tries = 0
    terms = random.randint(min_terms, max_terms) 
    max_tries = terms * 10  # avoid infinite loop in pathological cases

    while len(unique_terms) < terms and tries < max_tries:
        k = random.choices(sizes, weights=norm_weights)[0]
        k = min(k, n_vars)
        vars_chosen = random.sample(variables, k)
        literals = []
        for v in vars_chosen:
            if random.choice([True, False]):
                literals.append(v)
            else:
                literals.append(f'~{v}')
        cube = f"({' & '.join(literals)})"
        norm = normalize_cube(cube)
        if norm not in seen_cubes:
            seen_cubes.add(norm)
            unique_terms.append(cube)
        tries += 1

    esop_expr = ' ^ '.join(unique_terms)
    return esop_expr
    #esop_3_or_less, esop_more = partition_esop(esop_expr)
    #return esop_3_or_less, esop_more
def cz_replacement(control, target):
    """Returns a circuit to replace a CZ gate between control and target."""
    qc = QuantumCircuit(2)
    qc.s(control)
    qc.s(target)
    qc.cx(control,target)
    qc.s(target)
    qc.cx(control, target)
    return qc

def ccz_replacement(control1, control2, target):
    """Returns a circuit to replace a CCZ gate using H + Toffoli."""
    qc = QuantumCircuit(3)
    qc.cx(target,control2)
    qc.t(control1)
    qc.tdg(control2)
    qc.t(target)

    qc.cx(target,control1)
    qc.cx(control2,target)
    qc.cx(control1,control2)

    qc.tdg(control1)
    qc.tdg(control2)
    qc.t(target)

    qc.cx(control2,control1)
    qc.cx(control1,target)
    qc.cx(target,control2)

    qc.t(control2)

    qc.cx(target,control2)
    qc.cx(control1,control2)
    return qc

def preprocess_qk(original_circuit,vars_list):
    """Returns a new circuit where CZ and CCZ gates are replaced by defined circuits."""

    qr_old = original_circuit.qregs[0]
    n = len(qr_old)
    # Create new register with one extra qubit
    qr_new = QuantumRegister(n + 1, 'q')
    new_qc = QuantumCircuit(qr_new)
    var_dict = {var_name: index for index, var_name in enumerate(vars_list)}
    
    for inst, qargs, cargs in original_circuit.data:
        name = inst.name.lower()
        if name == 'cz':
            ctrl, tgt = [qr_old.index(q) + 1 for q in qargs]
            rep = cz_replacement(0, 1)
            new_qc = new_qc.compose(rep, [ctrl, tgt])
            #            new_qc = new_qc.compose(rep, [qargs[ctrl], qargs[tgt]])

        elif name == 'ccz':
            ctrl1, ctrl2, tgt = [qr_old.index(q) + 1 for q in qargs]
            rep = ccz_replacement(0, 1, 2)
            new_qc = new_qc.compose(rep, [ctrl1,ctrl2,tgt])
            #            new_qc = new_qc.compose(rep, [qargs[ctrl1], qargs[ctrl2], qargs[tgt]])
        elif re.fullmatch(r'c.*z*', name):
            #n-input and
            nvars = [f'x{i+1}' for i in range(len(qargs))]
            n_and = ' & '.join(nvars)
            rep,lits = gen_n4_cube(n_and)

            target_indices = [original_circuit.qubits.index(q) + 1 for q in qargs]
            connections = [0] + target_indices

            print("DCDEBUG preprocess_qk connections " + str(connections))
            new_qc = new_qc.compose(rep, connections)            

            # ctrl_connections = [qargs.index(q) for q in qargs]
            # #DCDEBUG ctrl_connections = [var_dict[var_name] + 1 for var_name in lits]
            # connections = [0] + ctrl_connections
            # print("DCDEBUG preprocess_qk connections " + str(connections))
            # new_qc = new_qc.compose(rep,connections)
        else:
            # preserve other instructions
            new_qargs = [qr_old.index(q) + 1 for q in qargs]
            new_qc.append(inst, new_qargs)

    return new_qc

##################### Run QK #################################
def parse_c_format_esop(esop_str, var_order):
    """
    Parses a C-format ESOP string (e.g., a & !b ^ c ^ !d & e)
    into Qiskit's expected ESOP string format:
    ('01-1', '11-0', ...) where 1=var, 0=negated var, -=don't care.
    """
    esop_cubes = []
    for cube_str in esop_str.split('^'):
        cube_str = cube_str.strip()
        # Find all literals in the current cube
        literals = {}
        for var_match in re.finditer(r'!?[a-zA-Z_][a-zA-Z0-9_]*', cube_str):
            var = var_match.group()
            if var.startswith('!') or var.startswith('~'):
                varname = var[1:]
                literals[varname] = '0'
            else:
                varname = var
                literals[varname] = '1'
        # Build the string for this cube
        cube_bits = ''
        for v in var_order:
            cube_bits += literals.get(v, '-')
        esop_cubes.append(cube_bits)
    return tuple(esop_cubes)
 ##################### Run QK #################################

#########          SCRAMBLE            ########################
def c_esop_to_bdd(esop_str, var_order):
    bdd = BDD()
    for v in var_order:
        bdd.add_var(v)

    terms = [term.strip().removeprefix('(').removesuffix(')') for term in esop_str.split('^')]
    term_nodes = []
    for term in terms:
        if not term:
            continue
        literals = [l.strip() for l in term.split('&')]
        and_node = None
        for lit in literals:
            if lit.startswith('!') or lit.startswith('~'):
                var = lit[1:].strip()
                node = ~bdd.var(var)
            else:
                var = lit
                node = bdd.var(var)
            if and_node is None:
                and_node = node
            else:
                and_node = bdd.apply('and', and_node, node)
        term_nodes.append(and_node)
    if not term_nodes:
        root = bdd.false
    else:
        root = term_nodes[0]
        for t in term_nodes[1:]:
            root = bdd.apply('xor', root, t)
    return bdd, root

def assignment_to_c_cube(assignment, var_order):
    literals = []
    for v in var_order:
        val = assignment.get(v, None)
        if val is True:
            literals.append(v)
        elif val is False:
            literals.append(f'!{v}')
    return ' & '.join(literals) if literals else '1'

def bdd_to_c_esop_string_with_large_cube(bdd, root, var_order, min_literals=4):
    cubes = []
    for assignment in bdd.pick_iter(root, care_vars=set(var_order)):
        cubes.append(assignment_to_c_cube(assignment, var_order))
    # Look for a cube with >min_literals literals
    found = any(c.count('&') + 1 > min_literals for c in cubes)
    return cubes, found

def find_esop_with_large_cube(esop_str, var_order, min_literals=4, max_attempts=1000, seed=None):
    if seed is not None:
        random.seed(seed)
    for attempt in range(max_attempts):
        random_order = var_order[:]
        random.shuffle(random_order)
        bdd, root = c_esop_to_bdd(esop_str, random_order)
        cubes, found = bdd_to_c_esop_string_with_large_cube(bdd, root, random_order, min_literals)
        last_cubes = cubes
        if found:
            # Return the variable order and the ESOP string
            esop_str_c = ' ^ '.join(cubes)
            return random_order, esop_str_c

    if not found:
        esop_str_c = ' ^ '.join(last_cubes)
        return random_order, esop_str_c


#########          SCRAMBLE            ########################
#########          OPTIMIZE            ########################
def optimize_esop(esop_str,var_names,fUseQCost=1):
    ret_str = []
    results = []
    def on_cube(bits, mask):
        """
        Convert bits and mask to C-style Boolean string (optionally with variable names).
        - bits, mask: integers (bitmasks)
        - n_vars: number of variables
        - var_names: optional list of variable names
        Returns: String, e.g. '01-1' or '!a & b & c'
        """
        nonlocal ret_str
        cube_str = []
        for i in range(len(var_names)):
            m = (mask >> i) & 1
            b = (bits >> i) & 1
            if not m:
                s = '-'
            else:
                s = '1' if b else '0'
            cube_str.append(s)
        cube_str = cube_str[::-1]  # Reverse to match variable order if LSB = last variable
        # If variable names are given, produce an expression
        if var_names:
            literals = []
            for val, name in zip(cube_str, var_names):
                if val == '1':
                    literals.append(name)
                elif val == '0':
                    literals.append('~' + name)
                # Skip '-' (don't care)
            cube_var_str = '('
            cube_var_str += ' & '.join(literals) if literals else '1'
            cube_var_str += ')'
            ret_str.append(cube_var_str)
            
        else:
            ret_str.append(''.join(cube_str))
        return 0

    # This call won't do meaningful minimization (no ESOP input), but demonstrates calling
    #result = exorcism.exorcism(nIns=3, nOuts=1, onCube=on_cube)
    result = exorcism(esop_str=esop_str, nIns=len(var_names), nOuts=1, onCube=on_cube, Quality=0,Verbosity=1,nCubesMax=1000,fUseQCost=fUseQCost)

    return ' ^ '.join(ret_str)

#########          OPTIMIZE            ########################
def run_exp(test_type,runs,directory="."):
    for i in range(1,runs+1):
        n         = 8
        vars_list = [f'x{j}' for j in range(1, n + 1)]
        if test_type == "n3_2n":
            max_cubes   = 2**(n-1)            
            min_cubes   = 2 * n
            esop        = generate_esop_expression(vars_list, min_terms=min_cubes, max_terms=max_cubes, prob_2=2.0, prob_3=1.0, prob_more=0)
            esop3,esop4 = partition_esop(esop)
            qk_str      = esop
            pro_str     = esop
        elif test_type == "n3_n":
            max_cubes   = 2 * n
            min_cubes   = 1
            esop        = generate_esop_expression(vars_list, min_terms=min_cubes, max_terms=max_cubes, prob_2=2.0, prob_3=1.0, prob_more=0)
            esop3,esop4 = partition_esop(esop)
            qk_str      = esop
            pro_str     = esop
        elif test_type == "scramble_2n": #DCTODO
            max_cubes   = 2**(n-1)            
            min_cubes   = 2 * n
            esop        = generate_esop_expression(vars_list, min_terms=min_cubes, max_terms=max_cubes, prob_2=1.0, prob_3=1.0, prob_more=0.5)

            print("DCDEBUG run_exp og esop " + esop)
            # random_order, large_cube_esop = find_esop_with_large_cube(
            #     esop, vars_list, min_literals=n/2, max_attempts=1000
            # )
            # qk_str      = large_cube_esop
            # pro_str     = large_cube_esop
            qk_str = optimize_esop(esop,vars_list,0)
            pro_str = optimize_esop(esop,vars_list,1)
            esop3,esop4 = partition_esop(pro_str)
        elif test_type == "scramble_n":
            max_cubes   = 2 * n
            min_cubes   = 1
            esop        = generate_esop_expression(vars_list, min_terms=min_cubes, max_terms=max_cubes,prob_2=1.0, prob_3=1.0, prob_more=0.5)
            print("DCDEBUG run_exp og esop " + esop)

            # random_order, large_cube_esop = find_esop_with_large_cube(
            #     esop, vars_list, min_literals=n/2, max_attempts=1000
            # )
            
            # qk_str      = large_cube_esop
            # pro_str     = large_cube_esop
            qk_str = optimize_esop(esop,vars_list,0)
            pro_str = optimize_esop(esop,vars_list)
            esop3,esop4 = partition_esop(pro_str)            
        else:
            raise ValueError("Unknown test_type:" + test_type)
        print("DCDEBUG run_exp esop3 " + esop3 + " esop4 " + esop4)
        pro_qc = gen_qc(esop3, esop4, vars_list, test_type)    
        print("DCDEBUG run_exp qk_str " + qk_str)
        print("DCDEBUG run_exp pro_str " + pro_str)        
        print("DCDEBUG run_exp tpar pro")
        run_tpar(pro_qc,directory + "/pro_qc"+str(i))
        with open(directory + "/pro_qc"+str(i)+".qc", 'a') as f:
            f.write(f"\n# {pro_str}\n")

        qk_qc_str = parse_c_format_esop(qk_str,vars_list)
        print("DCDEBUG run_exp qk_qc_str " + str(qk_qc_str))

        num_vars = len(vars_list) #DCDEBUG
        for cube in qk_qc_str:#DCDEBUG
            assert len(cube) == num_vars, f"Cube {cube} does not match num_vars {num_vars}"#DCDEBUG
        qk_qc = synth_phase_oracle_from_esop(qk_qc_str, len(vars_list))
        qk_qc = preprocess_qk(qk_qc,vars_list)

        # with open("qk_qc" + str(i) + ".qasm","w") as f:#DCDEBUG
        #     dump(qk_qc,f)#DCDEBUG
        # with open("qk_qc" + str(i) + ".txt","w") as f:#DCDEBUG
        #     f.write(str(qk_qc.decompose().draw(output="text")))#DCDEBUG
        print("DCDEBUG run_exp tpar qk_qc")        
        run_tpar(qk_qc,directory + "/qk_qc"+str(i))

    
        with open(directory + "/qk_qc"+str(i)+".qc", 'a') as f:
            f.write(f"\n# {qk_str}\n")

    

