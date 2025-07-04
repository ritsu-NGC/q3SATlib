from gen_n4 import lut_node
c = lut_node("node0",["x1","x2","x3","x4"],"y")

c.add_sop_expr("x1 & x2 & x3 & x4")
print(c._fanin)
print(c.bdd.to_expr(c.func))
result = c.synth()

print(result[0])
