from gen_n4 import lut_node
from gen_qc import write_qc_format
import subprocess
from gen_qc import gen_n4, extract_variables
from run_exp import run_exp
from qiskit import transpile
from qiskit import qasm2
# c = lut_node("node0",["x1","x2","x3","x4"],"y")

# c.add_sop_expr("x1 & x2 & x3 & x4")
# print(c._fanin)
# print(c.bdd.to_expr(c.func))
# result = c.synth()

# print(result[0])

# write_qc_format(result[0],"and4.qc")
# with open("test.log","w") as logfile, open("and4.qc","r") as infile:
#     result = subprocess.run(["./t-par/t-par","and4.qc"], stdin=infile, stdout=logfile,capture_output=False, text=True)
# logfile.close()

# result = gen_n4("x1 & x2 & x3 & x4")
# print(result)
#qc = qasm2.load("qk_qc.qasm")
run_exp("n3_2n",10)

# esop3 = "(~d & e) ^ (a & c & ~b) ^ (a & ~d & ~b) ^ (c & a & ~e) ^ (~a & b) ^ (c & e & a) ^ (~b & ~c) ^ (b & ~e)"
# esop4 = "(e & ~b & ~c & ~d) ^ (~d & a & ~c & ~b) ^ (a & e & ~c & ~d) ^ (~a & c & ~b & ~e) ^ (c & ~a & b & ~e) ^ (~a & ~c & ~b & d)"
# vars_list = extract_variables(esop4)
# var_dict = {var_name: index+1 for index, var_name in enumerate(vars_list)}
# var_dict["t"] = 0
# result = gen_n4(esop4,var_dict)
# print("DCDEBUG testn4 ")
# print(result) #DCDEBUG
# write_qc_format(result,"and4.qc")
# with open("test.log","w") as logfile, open("and4.qc","r") as infile:
#     result = subprocess.run(["./t-par/t-par","and4.qc"], stdin=infile, stdout=logfile,capture_output=False, text=True)
# logfile.close()
