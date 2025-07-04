from qiskit import QuantumCircuit,QuantumRegister
from qiskit.circuit.library import TGate, HGate, SGate
#from qiskit.quantum_info.random import unitary_group
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

#from src.circuit_to_logic import *
import logging
import os
import sys
import gc
#import memory-profiler

sys.path.append(os.path.join('../src'))

def blif_read(fpath):
    #tracemalloc.start(10)
    file1 = open(fpath, 'r')
    keep_reading = 1
    count = 0
    qc_args              = { "state" : "header" }
    qc_args["inputs"]    = []
    qc_args["outputs"]   = []
    qc_args["nodes"]     = []
    qc_args["rev_nodes"] = []
    qc_args["count"]     = 0
    while keep_reading:
        line = file1.readline()
        if len(line) == 0 or ".end" in line:
            keep_reading = 0
            break
        else:
            print("DCDEBUG line == .end " + str(line == '.end'))
            qc_args = proc_line(qc_args,line)
    
    if(qc_args["state"] == "func_info"):
        #print("DCDEBUG sizeof node" + str(sys.getsizeof(qc_args["nodes"][-1])))
        #print("DCDEBUG sizeof qc_args" + str(sys.getsizeof(qc_args)))                
        #print("DCDEBUG switch ")
        qc_args["nodes"][-1].synth()
        qc_args["nodes"][-1].synth_cf()

    return qc_args

def proc_line(qc_args,line):

    count = qc_args["count"]
    if line == '\n':
        return qc_args
    if line.split()[0] == '.model':
        qc_args["model"] = line.split()[1]
    elif line.split()[0] == '.inputs':
        qc_args["inputs"] = line.split()[1:]
    elif line.split()[0] == '.outputs':
        qc_args["outputs"] = line.split()[1:]
    elif line.split()[0] == '.names':
        #
        #print("DCDEBUG " + str())
        print("DCDEBUG " + line)
        if line.split()[1] == "$false" or line.split()[1] == "$true" or line.split()[1] == "$undef":
            return qc_args
        if (qc_args["state"] != "node_info"):
            if(qc_args["state"] == "func_info"):
                #print("DCDEBUG sizeof node" + str(sys.getsizeof(qc_args["nodes"][-1])))
                #print("DCDEBUG sizeof qc_args" + str(sys.getsizeof(qc_args)))                
                #print("DCDEBUG switch ")
                qc_args["nodes"][-1].synth()
                qc_args["nodes"][-1].synth_cf()
                qc_args["nodes"][-1].func = None
                qc_args["nodes"][-1].bdd  = None

                gc.collect()
            qc_args["state"] = "node_info"
            qc_args["nodes"].append(lut_node("node" + str(count),line.split()[1:-1],line.split()[-1]))
            qc_args["count"] += 1
    elif not line[0] == "#" and not '.end' in line:
        if(qc_args["state"] == "node_info"):
            qc_args["state"] = "func_info"
        if(qc_args["state"] == "func_info"):
            qc_args["nodes"][-1].add_sop_expr(line)

    if(qc_args["state"] == "func_info"):
        #print("DCDEBUG sizeof node" + str(sys.getsizeof(qc_args["nodes"][-1])))
        #print("DCDEBUG sizeof qc_args" + str(sys.getsizeof(qc_args)))                
        #print("DCDEBUG switch ")
        qc_args["nodes"][-1].synth()
        qc_args["nodes"][-1].synth_cf()

    return qc_args

def comp_methods(fpath):
    qc_args = blif_read(fpath)
    cost    = 0
    pr_time = 0
    cf_cost = 0
    cf_time = 0
    us_cost = 0    
    need_ancilla = 0
    tot_anc  = 0
    ret_vars = {}
    ret_vars['Circuit'] = fpath.split('/')[-1].split('.')[0]
    num_out_gates = 0
    tot_gates = 0
    tot_nodes = 0
    for gate in qc_args["nodes"]:
        #gate.synth()
        #gate.synth_cf()
        if gate._fanout in qc_args["outputs"]:
            cost += gate.cf_cost
            cf_cost += gate.cf_cost
            us_cost += gate.us_cost
            pr_time += gate.cf_time
            cf_time += gate.cf_time
            num_out_gates += 1
            tot_gates += 1
        else:
            cost    += gate.cost * 2
            pr_time += gate.time
            cf_time += gate.cf_time
            cf_cost += gate.cf_cost * 2
            us_cost += gate.us_cost * 2
            tot_gates += 2
        if gate.det == -1:
            need_ancilla += -1

        tot_nodes += gate.num_nodes
        tot_anc += gate.cf_anc

    ret_vars['Proposed']   = cost
    ret_vars['ESOP']       = cf_cost
    ret_vars['PrTime']     = pr_time
    ret_vars['ESOPTime']   = cf_time    
    #ret_vars['UnitarySynthesis'] = us_cost    
    #ret_vars['NeedAncilla'] = need_ancilla
    #ret_vars['TotalAncilla'] = tot_anc
    ret_vars['TotGates'] = tot_gates
    ret_vars['NumOuts'] = num_out_gates
    ret_vars['AvgNodes'] = round(tot_nodes / tot_gates)
    
    return ret_vars

        
class lut_node:
    def __init__(self,name,fanin,fanout):
        self._name   = name
        self._fanin  = [str.replace('$','') for str in fanin]
        self._fanout = fanout
        self.bdd     = cudd.BDD()
        self.cost    = 0
        for inp in self._fanin:
            self.bdd.declare(inp)
        if len(self._fanin) == 0:
            self.bdd.declare(self._fanout)
        #print("DCDEBUG fanin " + str(self._fanin))
        #print("DCDEBUG fanout " + str(self._fanout))        
        #self.matrix = [[0 for x in range(2 ** (len(self._fanin) + 1))] for y in range (2 ** (len(self._fanin) + 1))]
        self.matrix = numpy.zeros((2 ** (len(self._fanin) + 1), 2 ** (len(self._fanin) + 1)),dtype=int)
        for i in range(2 ** (len(self._fanin) + 1)):
            self.matrix[i][i] = 1
        self.func    = self.bdd.add_expr('False')

    def add_sop_expr(self,expr_str):
        sop_expr  = self.str_to_bdd(expr_str,self.bdd)
        self.func = self.func | sop_expr

    def str_to_bdd(self,expr_str,bdd):
        return bdd.add_expr(expr_str)

    def synth(self):
        qc = QuantumCircuit(1)
        self.num_nodes = len(self.func)
        var_order = self._fanin
        cudd.reorder(self.bdd)
        start = time.time()
        ret_val = self.do_synth(self.func,var_order,qc)
        end   = time.time()
        self.cost = ret_val[1]
        self.qc   = ret_val[0]
        self.time = int((end - start)*1000)
        return ret_val

    def do_synth(self,func,var_order,qc,unbalanced=False,do_unbalanced=False):
        #if len(func) == 1 or len(var_order) == 1:
        qc = QuantumCircuit(len(var_order) + 1)
        if func == self.bdd.add_expr('True'):
            #return CNOT
            qc.x(0)
            return [qc, 0]
        elif len(var_order) == 1:
            qc.cx(0,1)
            return [qc, 0]            
        else:
            if unbalanced == True:
                fact = 1
            else:
                fact = 2
            ret_arr = [qc,0]

            synth_func0 = self.bdd.let({var_order[0]:False},func)
            f0_gen = False
            if synth_func0 == self.bdd.add_expr('True'):
                qc.x(len(var_order)-1)
                f0 = [qc,0]
            elif synth_func0 != self.bdd.add_expr('False'):
                f0 = self.do_synth(synth_func0,var_order[1:],qc,do_unbalanced ^ unbalanced,do_unbalanced)
                qc = xdotg(var_order,f0[0])
                # print("DCDEBUG f0" + str(f0[1]))
                f0_gen = True
            else:
                f0 = [qc,0]

            f1_gen = False                
            synth_func1 = self.bdd.let({var_order[0]:True},func)
            if synth_func1 == self.bdd.add_expr('True'):
                qc.x(len(var_order)-1)
                f1 = [qc,0]
            elif synth_func1 != self.bdd.add_expr('False'):
                f1 = self.do_synth(synth_func1,var_order[1:],qc,do_unbalanced ^ unbalanced, do_unbalanced)
                qc = xdotg(var_order,f1[0])
                f1_gen = True
                # print("DCDEBUG f1" + str(f1[1]))
            else:
                f1 = [qc,0]

            ret_arr = [qc, fact * f0[1] + 4 * f0_gen + fact * f1[1] + 4 * f1_gen]

            return ret_arr

def display_top(snapshot, key_type='lineno', limit=10):
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        print("#%s: %s:%s: %.1f KiB"
              % (index, frame.filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))

def F_recursive(qubits, circuit, controls, target):
    """
    Recursively add the F operation as shown in the diagram.
    For n=1 (base case), F is identity.
    For n>1, F is recursively defined on n-1 controls,
    with the structure matching the right side of the diagram.
    
    Args:
        qubits: The list of qubit indices (including the ancilla z at the end).
        circuit: The QuantumCircuit to add gates to.
        controls: List of control qubit indices.
        target: Index of the target qubit (z in the diagram).
    """
    n = len(controls)
    if n == 0:
        # Base case: do nothing (identity)
        return
    # Apply H on target (z)
    elif func == self.bdd.add_expr('True') or len(var_order) == 1:
        #DCTODO
        #return CNOT
        return [qc, 0]
    else:
        synth_func0 = self.bdd.let({var_order[0]:False},func)
        ret_arr = [qc,0]
        if unbalanced == True:
            fact = 1
        else:
            fact = 2
            
        if synth_func0 == self.bdd.add_expr('True'):
            ret_arr = [qc,ret_arr[1]]
        elif synth_func0 != self.bdd.add_expr('False'):
            synth0 = self.do_synth(synth_func0,var_order[1:],qc,do_unbalanced ^ unbalanced,do_unbalanced)
            #DCTODO ret_arr = [qc,ret_arr[1] + fact * synth0[1] + 4]
        synth_func1 = self.bdd.let({var_order[0]:True},func)
        if synth_func1 == self.bdd.add_expr('True'):
            ret_arr = [qc,ret_arr[1]]
        elif synth_func1 != self.bdd.add_expr('False'):
            synth1 = self.do_synth(synth_func1,var_order[1:],qc,do_unbalanced ^ unbalanced, do_unbalanced)
            #DCTODO ret_arr = [qc,ret_arr[1] + fact * synth1[1] + 4]

def xdotg(controls, subcirc):
    #[target, var1, var2...]
    target = 0
    control = 1
    new_circ = QuantumCircuit(len(controls) + 1)
    new_circ.barrier()
    new_circ.h(target)

    # CNOT from last control to target
    new_circ.cx(target, control)

    # T on target
    new_circ.t(target)

    # Tdg on target
    new_circ.tdg(control)

    # CNOT from last control to target
    new_circ.cx(control, target)

    # Recursively apply F on n-1 controls
    new_circ = new_circ.compose(subcirc, list(range(1,1+len(controls))))
    new_circ.cx(control, target)
    
    new_circ.t(control)
    # T on target
    new_circ.tdg(target)
    new_circ.cx(target, control)
    # Recursively apply F on n-1 controls
    new_circ = new_circ.compose(subcirc, [0].append(range(2,2+len(controls))))
    # H on target
    new_circ.h(target)
    new_circ.barrier()
    return new_circ

def make_recursive_F_circuit(n):
    """
    Build a QuantumCircuit implementing the recursive F operation for n controls as in the diagram.
    Returns a QuantumCircuit on (n+1) qubits: n input qubits + 1 ancilla z.

    Args:
        n: Number of control qubits.
    Returns:
        QuantumCircuit
    """
    qc = QuantumCircuit(n + 1)
    controls = list(range(n))
    target = n
    F_recursive(list(range(n + 1)), qc, controls, target)
    return qc

# Usage Example:
# qc = make_recursive_F_circuit(3)
# print(qc.draw())
