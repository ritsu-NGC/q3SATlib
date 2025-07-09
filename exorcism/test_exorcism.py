import exorcism


vEsop = "(x5 & !x2 & !x3 & !x4) ^ (!x4 & x1 & !x3 & !x2) ^ (x1 & x5 & !x3 & !x4) ^ (!x1 & x3 & !x2 & !x5) ^ (x3 & !x1 & x2 & !x5) ^ (!x1 & !x3 & !x2 & x4)"
n_vars = 5
var_names = ["x5","x4","x3","x2","x1"]
ret_str = ""
results = []
def on_cube(bits, mask):
    """
    Convert bits and mask to C-style Boolean string (optionally with variable names).
    - bits, mask: integers (bitmasks)
    - n_vars: number of variables
    - var_names: optional list of variable names
    Returns: String, e.g. '01-1' or '!a & b & c'
    """
    global ret_str
    cubes_str = []
    for i in range(n_vars):
        m = (mask >> i) & 1
        b = (bits >> i) & 1
        if not m:
            s = '-'
        else:
            s = '1' if b else '0'
        cubes_str.append(s)
    cube_str = cube_str[::-1]  # Reverse to match variable order if LSB = last variable
    print("DCDEBUG " + ''.join(cube_str))
    # If variable names are given, produce an expression
    if var_names:
        literals = []
        for val, name in zip(cube_str, var_names):
            if val == '1':
                literals.append(name)
            elif val == '0':
                literals.append('!' + name)
            # Skip '-' (don't care)
        ret_str = ret_str + ' & '.join(literals) if literals else '1'
    else:
        ret_str = ret_str + ''.join(cube_str)

    return 0

# This call won't do meaningful minimization (no ESOP input), but demonstrates calling
#result = exorcism.exorcism(nIns=3, nOuts=1, onCube=on_cube)
result = exorcism.exorcism(esop_str=vEsop, nIns=5, nOuts=1, onCube=on_cube, Quality=0,Verbosity=1,nCubesMax=1000,fUseQCost=1)
print("ret_str " + ret_str)
print("Exorcism result:", result)

def old_on_cube(bits, mask):
    print(f"Cube: bits={bits}, mask={mask}")
