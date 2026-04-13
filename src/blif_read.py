from qiskit import QuantumCircuit,QuantumRegister
#from qiskit.circuit.classicalfunction import classical_function,ClassicalFunction
from qiskit.circuit.library import TGate, HGate, SGate
#from qiskit.quantum_info.random import unitary_group
# from qiskit.transpiler.passes.synthesis import UnitarySynthesis
# from qiskit.quantum_info.synthesis import TwoQubitBasisDecomposer
# from qiskit.extensions.unitary import UnitaryGate
#from qiskit.circuit.classicalfunction.types import Int1
from dd import cudd
from textwrap import dedent
# from tweedledum.synthesis import linear_synth
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
import re

TOKEN = re.compile(r"\s*(ite|TRUE|FALSE|~|\(|\)|,|[A-Za-z_]\w*)\s*")

sys.path.append(os.path.join('../src'))

#from circuit_synthesis import iter_to_bool
#from calc_cost import all_toffoli,conventional_cost,dirty_barenco_cost

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
            qc_args = proc_line(qc_args,line)
            #print("DCDEBUG line == .end " + str(line == '.end'))
            
    print("DCDEBUG state "  + str(qc_args["state"]))
    if(qc_args["state"] == "func_info"):
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
        output_node = 0
        if line.split()[-1] in qc_args["outputs"]:
            output_node = 1
        print("DCDEBUG line " + line)
        print("DCDEBUG " + str(line.split()[1:-1]))
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
            qc_args["nodes"].append(lut_node("node" + str(count),line.split()[1:-1],line.split()[-1],output_node))
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
    qc_args  = blif_read(fpath)
    cost     = 0
    pr_time  = 0
    new_time = 0
    cf_cost  = 0
    cf_time  = 0
    us_cost  = 0
    new_cost = 0
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
            new_cost += gate.cf_cost
            cf_cost += gate.cf_cost
            us_cost += gate.us_cost
            pr_time += gate.cf_time
            cf_time += gate.cf_time
            new_time += gate.cf_time
            num_out_gates += 1
            tot_gates += 1
        else:
            cost    += gate.cost * 2
            new_cost += gate.cost_new * 2
            pr_time += gate.time
            cf_time += gate.cf_time
            new_time += gate.time_new
            cf_cost += gate.cf_cost * 2
            us_cost += gate.us_cost * 2
            tot_gates += 2
        if gate.det == -1:
            need_ancilla += -1

        tot_nodes += gate.num_nodes
        tot_anc += gate.cf_anc

    ret_vars['Previous']   = cost
    ret_vars['Proposed']   = new_cost    
    ret_vars['ESOP']       = cf_cost
    ret_vars['PrTime']     = pr_time
    ret_vars['NewTime']    = new_time
    ret_vars['ESOPTime']   = cf_time    
    #ret_vars['UnitarySynthesis'] = us_cost    
    #ret_vars['NeedAncilla'] = need_ancilla
    #ret_vars['TotalAncilla'] = tot_anc
    ret_vars['TotGates'] = tot_gates
    ret_vars['NumOuts'] = num_out_gates
    ret_vars['AvgNodes'] = round(tot_nodes / tot_gates)
    
    return ret_vars

        
class lut_node:
    def __init__(self,name,fanin,fanout,output_node):
        print("DCDEBUG fanin " + str(fanin))
        self._name       = name
        self._fanin      = [str.replace('$','') for str in fanin]
        self._fanout     = fanout
        self.bdd         = cudd.BDD()
        self.cost        = 0
        self.output_node = output_node
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

    def add_sop_expr(self,line):
        sop_expr  = self.str_to_bdd(line,self._fanin,self.bdd)
        self.set_matrix(line)
        self.func = self.func | sop_expr

    def set_matrix(self,line):
        bit_strings = []

        for x in line[0]:
            temp_strings = []
            if x == '-':
                temp_strings.append('0')
                temp_strings.append('1')
            else:
                temp_strings.append(x)
            new_strings = []
            if len(bit_strings) > 0:
                for string in bit_strings:
                    for new_bit in temp_strings:
                        new_strings.append(string + new_bit)
            else:
                for new_bit in temp_strings:
                    new_strings.append(new_bit)
            bit_strings = new_strings
        #print("DCDEBUG " + str(bit_strings))
        #print("DCDEBUG " + str(self.matrix))        
        for string in bit_strings:
            self.matrix[int(string + '0',2),int(string + '1',2)] = 1
            self.matrix[int(string + '0',2),int(string + '0',2)] = 0
            self.matrix[int(string + '1',2),int(string + '0',2)] = 1
            self.matrix[int(string + '1',2),int(string + '1',2)] = 0

        #print("DCDEBUG " + str(self.matrix))        
    def str_to_bdd(self,line,bdd_vars,bdd):
        
        #print("DCDEBUG bdd_vars " + str(bdd_vars))
        line_arr = line.split()
        #print("DCDEBUG line_arr " + str(line_arr))
        count    = 0
        expr_str = ""
        if len(bdd_vars) == 0:
            return bdd.add_expr("True")
        for kbit in line_arr[0]:
            #print("DCDEBUG count " + str(count))
            if count > 0 and not kbit == "-" and not expr_str == "":
                expr_str += " & "
            if kbit == "1":
                expr_str += bdd_vars[count]
            elif kbit == "0":
                expr_str += "~" + bdd_vars[count]
            count += 1
        return bdd.add_expr(expr_str)
    def synth(self):
        var_order = self._fanin  # e.g. ["a", "b", "carry", ...]
        print("DCDEBUG var_order synth " + str(var_order))
        # Register name can include the variable names (purely cosmetic, but helpful for debugging)
        self.qr = QuantumRegister(len(var_order)+1, name="v_" + "_".join(var_order))
        self.qc = QuantumCircuit(self.qr)
        # Practical: map each variable name to its qubit position
        var_to_q = {name: self.qr[i+1] for i, name in enumerate(var_order)}
        var_to_q["target"] = self.qr[0]
        if(self.output_node):
            # synthesize phase gate
            dd_str = self.bdd.to_expr(self.func)
            print("DCDEBUG dd_str " + dd_str)
            c_str  = dd_to_c_expr(dd_str)
            print("DCDEBUG c_str " + c_str)            
            qc = get_rtof(self.qc,var_to_q[var_order[0]],var_to_q[var_order[1]],0)
        else:
            qc = get_rtof(self.qc,var_to_q[var_order[0]],var_to_q[var_order[1]],0)
        

            
    def old_synth(self):
        self.num_nodes = len(self.func)
        # var_order = self._fanin
        # cudd.reorder(self.bdd)
        # start = time.time()
        # qc = QuantumCircuit(len(var_order))
        var_order = self._fanin  # e.g. ["a", "b", "carry", ...]
        cudd.reorder(self.bdd)
        start = time.time()

        # Register name can include the variable names (purely cosmetic, but helpful for debugging)
        qr = QuantumRegister(len(var_order)+1, name="v_" + "_".join(var_order))
        qc = QuantumCircuit(qr)

        # Practical: map each variable name to its qubit position
        var_to_q = {name: qr[i+1] for i, name in enumerate(var_order)}
        var_to_q["target"] = qr[0]

        ret_val = self.do_synth(self.func,var_order,qc)
        end   = time.time()
        self.cost = ret_val[1]
        self.qc   = ret_val[0]
        self.time = int((end - start)*1000)

        start = time.time()
        ret_val = self.do_synth_new(self.func,var_order,var_to_q,qc,unbalanced=True,do_unbalanced=True)
        end   = time.time()
        self.cost_new = ret_val[1]
        self.qc_new   = ret_val[0]
        self.time_new = int((end - start)*1000)

    def do_synth_new(self,func,var_order,var_to_q,qc,unbalanced=False,do_unbalanced=False):
        #if len(func) == 1 or len(var_order) == 1:
        if func == self.bdd.add_expr('True') or len(var_order) == 1:
            #return CNOT
            print("DCDEBUG " + str(var_order) + " " + str(var_order[0]) + str(var_to_q))
            self.qc.cx(var_to_q[var_order[0]],var_to_q["target"])
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
                f0 = [qc,0]
            elif synth_func0 != self.bdd.add_expr('False'):
                f0 = self.do_synth_new(synth_func0,var_order[1:],var_to_q,qc,do_unbalanced ^ unbalanced,do_unbalanced)
                #print("DCDEBUG f0" + str(f0[1]))
                f0_gen = True
            else:
                f0 = [qc,0]

            f1_gen = False                
            synth_func1 = self.bdd.let({var_order[0]:True},func)
            if synth_func1 == self.bdd.add_expr('True'):
                f1 = [qc,0]
            elif synth_func1 != self.bdd.add_expr('False'):
                f1 = self.do_synth_new(synth_func1,var_order[1:],var_to_q,qc,do_unbalanced ^ unbalanced, do_unbalanced)
                f1_gen = True
                #print("DCDEBUG f1" + str(f1[1]))
            else:
                f1 = [qc,0]

            f0_gen_dav = False
            if synth_func0 == self.bdd.add_expr('True'):
                f0_dav = [qc,0]
            elif synth_func0 != self.bdd.add_expr('False'):
                f0_dav = self.do_synth_new(synth_func0,var_order[1:],var_to_q,qc,unbalanced,do_unbalanced)
                f0_gen_dav = True
            else:
                f0_dav = [qc,0]

            f1_gen_dav = False                
            if synth_func1 == self.bdd.add_expr('True'):
                f1_dav = [qc,0]
            elif synth_func1 != self.bdd.add_expr('False'):
                f1_dav = self.do_synth_new(synth_func1,var_order[1:],var_to_q,qc,unbalanced, do_unbalanced)
                f1_gen_dav = True
            else:
                f1_dav = [qc,0]

                
            f2_gen = False
            synth_func2 = xor_node(synth_func0,synth_func1,self.bdd)
            if synth_func2 == self.bdd.add_expr('True'):
                f2 = [qc,0]
            elif synth_func2 != self.bdd.add_expr('False'):
                f2 = self.do_synth_new(synth_func2,var_order[1:],var_to_q,qc,do_unbalanced ^ unbalanced, do_unbalanced)
                f2_gen = True
                #print("DCDEBUG f2" + str(f2[1]))
            else:
                f2 = [qc,0]

            shannon = [qc, fact * f0[1] + 4 * f0_gen + fact * f1[1] + 4 * f1_gen]
            davio_p = [qc, f0_dav[1] + fact * f2[1] + 4 * f2_gen]
            davio_n = [qc, f1_dav[1] + fact * f2[1] + 4 * f2_gen]

            ret_arr = min([shannon,davio_p,davio_n],key=lambda x: x[1])

            return ret_arr

    def do_synth(self,func,var_order,qc,unbalanced=False,do_unbalanced=False):
        #if len(func) == 1 or len(var_order) == 1:
        if func == self.bdd.add_expr('True') or len(var_order) == 1:
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
                ret_arr = [qc,ret_arr[1] + fact * synth0[1] + 4]
            synth_func1 = self.bdd.let({var_order[0]:True},func)
            if synth_func1 == self.bdd.add_expr('True'):
                ret_arr = [qc,ret_arr[1]]
            elif synth_func1 != self.bdd.add_expr('False'):
                synth1 = self.do_synth(synth_func1,var_order[1:],qc,do_unbalanced ^ unbalanced, do_unbalanced)
                ret_arr = [qc,ret_arr[1] + fact * synth1[1] + 4]


            return ret_arr

    def synth_cf(self):
        qc           = QuantumCircuit(1)
        self.det     = numpy.linalg.det(self.matrix)
        #print('DCDEBUG synth CF')
        if len(self._fanin) == 0:
            self.cf_qc   = qc
            self.cf_cost = 0
            self.cf_anc  = 0
            self.us_cost = 0
            self.cf_time = 0
        else:
            start        = time.time()
            # self.cf_qc   = ClassicalFunction(dedent(iter_to_bool(self.bdd,self.func))).synth()
            end          = time.time()
            #cf_cost_tmp  = dirty_barenco_cost(self.cf_qc,[self._fanout])
            #self.cf_cost = cf_cost_tmp[0]
            f = open('cf.tex','w')
            #print(self.cf_qc.draw(output="latex_source"),file=f)
            self.cf_qc   = None
            #self.cf_anc  = cf_cost_tmp[1]
            self.us_cost = 0
            self.cf_time = int((end - start)*1000)
            # #decomposer   = TwoQubitBasisDecomposer([CXGate(), XGate(), TGate()])
            # #synthesizer  = UnitarySynthesis(['x','cx','t'])
            #self.us_qc   = synthesizer.synthesize(self.matrix)
            #print("DCDEBUG det " + str(self.det))
            if self.det == 1 and False:
                self.us_qc   = QuantumCircuit(len(self._fanin) + 1)
                terms        = numpy.append(self._fanin,self._fanout)
                new_terms    = list(range(0,len(self._fanin) + 1))
                unitary_gate = UnitaryGate(self.matrix)
                self.us_qc.append(unitary_gate,new_terms)
                
                temp_qc      = transpile(self.us_qc,basis_gates=['u3','cx','u'])
                tot_ops      = temp_qc.count_ops()
                self.us_cost += dict(tot_ops)['u3'] + dict(tot_ops)['u']
            else:
                self.us_cost += 0
                #self.us_cost += cf_cost_tmp[0]
            #DCDEBUG
        gc.collect()

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

def xor_node(node0,node1,bdd):
    return ~node0 & node1 | node0 & ~node1
    

def get_rtof(qc,x0,x1,f):
    #ret_qc = QuantumCircuit(qc.qubits)
    ret_qc = qc.copy()
    ret_qc.clear()
    #DCDEBUG ret_qc.s(f)
    ret_qc.h(f)
    ret_qc.t(f)
    ret_qc.cx(x1,f)
    ret_qc.tdg(f)
    ret_qc.cx(x0,f)
    ret_qc.t(f)
    ret_qc.cx(x1,f)
    ret_qc.tdg(f)
    ret_qc.h(f)
    #DCDEBUG ret_qc.sdg(f)
    #print("DCDEBUG get_rtof")
    #print(ret_qc.draw())
    return ret_qc

def get_rtof_alt(qc,x0,x1,f):
    #ret_qc = QuantumCircuit(qc.qubits)
    ret_qc = qc.copy()
    ret_qc.clear()
    #DCDEBUG ret_qc.s(f)
    ret_qc.h(f)
    ret_qc.tdg(f)
    ret_qc.cx(x1,f)
    ret_qc.t(f)
    ret_qc.cx(x0,f)
    ret_qc.tdg(f)
    ret_qc.cx(x1,f)
    ret_qc.t(f)
    ret_qc.h(f)
    #DCDEBUG ret_qc.sdg(f)
    #print("DCDEBUG get_rtof")
    #print(ret_qc.draw())
    return ret_qc

def get_rtof_inv(qc,x0,x1,f):
#    ret_qc = QuantumCircuit(qc.qubits)
    ret_qc = qc.copy()
    ret_qc.clear()
    ret_qc.s(f)
    ret_qc.h(f)
    ret_qc.tdg(f)
    ret_qc.cx(x1,f)
    ret_qc.t(f)
    ret_qc.cx(x0,f)
    ret_qc.tdg(f)
    ret_qc.cx(x1,f)
    ret_qc.t(f)
    ret_qc.h(f)    
    ret_qc.sdg(f)
    return ret_qc.to_instruction(label="rtofdg")

def tokenize(s: str):
    pos = 0
    out = []
    while pos < len(s):
        m = TOKEN.match(s, pos)
        if not m:
            raise ValueError(f"Unexpected text at {pos}: {s[pos:pos+20]!r}")
        out.append(m.group(1))
        pos = m.end()
    return out

def parse_expr(tokens, i=0):
    tok = tokens[i]

    if tok == '~':
        inner, j = parse_expr(tokens, i + 1)
        return ('not', inner), j

    if tok == '(':
        inner, j = parse_expr(tokens, i + 1)
        if tokens[j] != ')':
            raise ValueError("Expected ')'")
        return inner, j + 1

    if tok == 'ite':
        # ite ( cond , then , else )
        if tokens[i + 1] != '(':
            raise ValueError("Expected '(' after ite")
        cond, j = parse_expr(tokens, i + 2)
        if tokens[j] != ',':
            raise ValueError("Expected ',' after ite condition")
        tbranch, j = parse_expr(tokens, j + 1)
        if tokens[j] != ',':
            raise ValueError("Expected ',' after ite then-branch")
        ebranch, j = parse_expr(tokens, j + 1)
        if tokens[j] != ')':
            raise ValueError("Expected ')' after ite else-branch")
        return ('ite', cond, tbranch, ebranch), j + 1

    if tok in ('TRUE', 'FALSE') or re.match(r"[A-Za-z_]\w*", tok):
        return ('atom', tok), i + 1

    raise ValueError(f"Unexpected token: {tok}")

def emit_c(ast):
    kind = ast[0]

    if kind == 'atom':
        v = ast[1]
        if v == 'TRUE':  return '1'
        if v == 'FALSE': return '0'
        return v

    if kind == 'not':
        return f"(!{emit_c(ast[1])})"

    if kind == 'ite':
        c, t, e = ast[1], ast[2], ast[3]
        # ite(c,t,e) == (c&t) | (!c&e)
        return f"(({emit_c(c)} & {emit_c(t)}) | ((!{emit_c(c)}) & {emit_c(e)}))"

    raise ValueError(f"Unknown AST node: {kind}")

def dd_to_c_expr(s: str) -> str:
    tokens = tokenize(s)
    ast, j = parse_expr(tokens, 0)
    if j != len(tokens):
        raise ValueError("Trailing tokens after parse")
    return emit_c(ast)


