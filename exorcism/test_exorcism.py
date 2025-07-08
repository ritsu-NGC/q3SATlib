import exorcism


vEsop = "(x5 & !x2 & !x3 & !x4) ^ (!x4 & x1 & !x3 & !x2) ^ (x1 & x5 & !x3 & !x4) ^ (!x1 & x3 & !x2 & !x5) ^ (x3 & !x1 & x2 & !x5) ^ (!x1 & !x3 & !x2 & x4)"

def on_cube(bits, mask):
    print(f"Cube: bits={bits}, mask={mask}")

# This call won't do meaningful minimization (no ESOP input), but demonstrates calling
#result = exorcism.exorcism(nIns=3, nOuts=1, onCube=on_cube)
result = exorcism.exorcism(esop_str=vEsop, nIns=5, nOuts=1, onCube=on_cube, Quality=0,Verbosity=1,nCubesMax=1000,fUseQCost=1)

print("Exorcism result:", result)
