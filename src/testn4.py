from gen_n4 import lut_node
from gen_qc import write_qc_format
import subprocess
from gen_qc import gen_n4, extract_variables
from run_exp import run_exp
from qiskit import transpile
from qiskit import qasm2
import os

#from read_logs import optimize_esop
from run_exp import partition_esop,optimize_esop,run_tpar,parse_c_format_esop,synth_phase_oracle_from_esop,preprocess_qk
from gen_qc import gen_qc
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
#run_exp("scramble_n",1)

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
vars_list=["x1","x2","x3","x4","x5","x6","x7"]
test_type="scramble_n"
# esop = "(~x7 & x5 & ~x2 & x3 & x4) ^ (x2 & ~x3 & ~x7 & ~x1 & ~x4) ^ (~x5 & x4 & x8) ^ (x1 & x7) ^ (~x7 & x5 & ~x1 & x8 & ~x6) ^ (~x7 & x6 & x1 & x2 & ~x3) ^ (~x6 & ~x3 & ~x7) ^ (~x6 & x4 & x3) ^ (x2 & ~x3 & ~x8) ^ (x2 & x6) ^ (x3 & ~x4 & ~x6) ^ (x5 & ~x2 & ~x6) ^ (x6 & x8)"
# pro_str = "(x2 & ~x3 & ~x5 & x6 & ~x7) ^ (~x2 & ~x3 & x4 & x6 & ~x7) ^ (~x3 & x4 & ~x7) ^ (~x1 & ~x3 & ~x4 & ~x6 & x7) ^ (~x1 & ~x2 & x4) ^ (~x1 & ~x2 & x3 & ~x4 & ~x5 & x6) ^ (x1 & x5 & ~x7)"
esop = "(~x7 & x5 & ~x2 & x3 & x4) ^ (x2 & ~x3 & ~x7 & ~x1 & ~x4) ^ (~x5 & x4 & x8) ^ (x1 & x7) ^ (~x7 & x5 & ~x1 & x8 & ~x6) ^ (~x7 & x6 & x1 & x2 & ~x3) ^ (~x6 & ~x3 & ~x7) ^ (~x6 & x4 & x3) ^ (x2 & ~x3 & ~x8) ^ (x2 & x6) ^ (x3 & ~x4 & ~x6) ^ (x5 & ~x2 & ~x6) ^ (x6 & x8)"
pro_str = "(~x3 & ~x4) ^ (~x2 & ~x3 & x6) ^ (x2 & x3) ^ (~x1 & ~x2 & x3 & ~x7) ^ (x1 & ~x2 & ~x5) ^ (x1 & x7) ^ (x5 & x6) ^ (~x1 & x2 & ~x5 & x6 & x7) ^ (~x1 & ~x4 & ~x5 & x6 & ~x7) ^ (~x1 & x3 & x4 & x5 & ~x6)"
esop3,esop4 = partition_esop(pro_str)            
pro_qc = gen_qc(esop3, esop4, vars_list, test_type)
run_tpar(pro_qc,"./testn4_pro")
print("DCDEBUG esop " + esop)
qk_qc_str = parse_c_format_esop(esop,vars_list)
print("DCDEBUG qk_qc_str " + str(qk_qc_str))
qk_qc = synth_phase_oracle_from_esop(qk_qc_str, len(vars_list))
qk_qc = preprocess_qk(qk_qc,vars_list)

with open("qk_qc.txt","w") as f:
    f.write(str(qk_qc.draw(output='text')))
run_tpar(qk_qc,"./testn4_qk")

