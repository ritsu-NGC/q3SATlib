from gen_n4 import lut_node
from gen_qc import write_qc_format
import subprocess

c = lut_node("node0",["x1","x2","x3","x4"],"y")

c.add_sop_expr("x1 & x2 & x3 & x4")
print(c._fanin)
print(c.bdd.to_expr(c.func))
result = c.synth()

print(result[0])

write_qc_format(result[0],"and4.qc")
with open("test.log","w") as logfile, open("and4.qc","r") as infile:
    result = subprocess.run(["./t-par/t-par","and4.qc"], stdin=infile, stdout=logfile,capture_output=False, text=True)
logfile.close()
