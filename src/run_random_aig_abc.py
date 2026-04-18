#!/usr/bin/env python3
"""
Full pipeline:
 - generate random AAG (ASCII)
 - convert to binary AIG (pure Python writer)
 - run ./abc to map to LUTs and write mapped AIG
 - parse both original and mapped binary AIGs
 - generate TikZ diagrams for both (aig_original.tex, aig_mapped.tex)

Requirements:
 - ./abc must be executable and accessible (script calls ["./abc", "-f", "/dev/stdin"])
 - python3 (std library only)
"""

import subprocess
import tempfile
import random
from pathlib import Path
import sys
from esop_to_aiger import esop_to_aiger
# -------------------------
# 1) Random valid AAG generator
# -------------------------
def generate_valid_aag(num_inputs=6, num_ands=20, num_outputs=3):
    inputs = [2 * (i + 1) for i in range(num_inputs)]
    ands = []
    next_var = num_inputs + 1
    available = inputs.copy()

    for _ in range(num_ands):
        lhs = 2 * next_var
        next_var += 1
        r1 = random.choice(available) ^ random.choice([0, 1])
        r2 = random.choice(available) ^ random.choice([0, 1])
        # ensure we don't accidentally make lhs <= r1 or r2 — AAG allows any, but binary encoding expects ordering for deltas
        ands.append((lhs, r1, r2))
        available.append(lhs)

    outputs = []
    for _ in range(num_outputs):
        lit = random.choice(available) ^ random.choice([0, 1])
        outputs.append(lit)

    M = next_var - 1
    I = num_inputs
    L = 0
    O = num_outputs
    A = num_ands
    return M, I, L, O, A, inputs, ands, outputs

# -------------------------
# 2) Write ASCII AAG
# -------------------------
def write_ascii_aag(path, M, I, L, O, A, inputs, ands, outputs):
    with open(path, "w", encoding="ascii") as f:
        f.write(f"aag {M} {I} {L} {O} {A}\n")
        for lit in inputs:
            f.write(f"{lit}\n")
        # no latches
        for lhs, r1, r2 in ands:
            f.write(f"{lhs} {r1} {r2}\n")
        for lit in outputs:
            f.write(f"{lit}\n")

# -------------------------
# 3) Binary AIG writer (AIGER 1.9 encoding)
#    Header ascii, outputs ascii, then A delta LEB128s
# -------------------------
def encode_varint_unsigned(x):
    out = bytearray()
    while True:
        b = x & 0x7F
        x >>= 7
        if x:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)

def write_binary_aig(path, M, I, L, O, A, inputs, ands, outputs):
    with open(path, "wb") as f:
        header = f"aig {M} {I} {L} {O} {A}\n"
        f.write(header.encode("ascii"))

        # outputs as ascii lines
        for lit in outputs:
            f.write(f"{lit}\n".encode("ascii"))

        # AND gates: must encode delta1 and delta2 for each AND in order
        # The canonical encoding expects each AND to be for lhs = 2*(I + 1 + i)
        # We'll encode using the lhs values we produced. For safety, we must ensure ands are in increasing lhs order.
        sorted_ands = sorted(ands, key=lambda t: t[0])
        for lhs, r1, r2 in sorted_ands:
            # ensure r1 >= r2 to keep consistent (spec doesn't require this, but our encoder earlier used ordering)
            if r1 < r2:
                r1, r2 = r2, r1
            delta1 = lhs - r1
            delta2 = r1 - r2
            f.write(encode_varint_unsigned(delta1))
            f.write(encode_varint_unsigned(delta2))
        # no symbols/footer

# -------------------------
# 4) Run ABC with inline script
# -------------------------
def run_abc_script(abc_commands):
    proc = subprocess.run(
        ["/home/dizzy/abc/abc", "-f", "/dev/stdin"],
        input=abc_commands,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return proc

# -------------------------
# 5) Binary AIG parser (reads header ascii + outputs ascii + binary ands)
#    Returns M,I,L,O,A, inputs(as literals), ands list (lhs, r1, r2), outputs list
# -------------------------
def read_binary_aig(path):
    with open(path, "rb") as f:
        # read header line ascii
        header_line = f.readline().decode("ascii")
        if not header_line.startswith("aig"):
            raise ValueError("Not a valid binary AIG (missing 'aig' header)")
        parts = header_line.strip().split()
        if len(parts) != 6:
            raise ValueError("Unexpected AIG header format")
        # parse header
        _, M_s, I_s, L_s, O_s, A_s = parts
        M = int(M_s); I = int(I_s); L = int(L_s); O = int(O_s); A = int(A_s)

        # read O output lines (ascii decimal literals)
        outputs = []
        for _ in range(O):
            line = f.readline().decode("ascii")
            if not line:
                raise EOFError("Unexpected EOF while reading outputs")
            outputs.append(int(line.strip()))

        # read A AND nodes from remaining bytes using LEB128 varints:
        # For each AND i (0..A-1), lhs = 2*(I + 1 + i)
        # decode delta1, delta2, then r1 = lhs - delta1, r2 = r1 - delta2
        ands = []
        # Helper to decode unsigned LEB128 from file
        def read_varint(fileobj):
            shift = 0
            result = 0
            while True:
                b = fileobj.read(1)
                if not b:
                    raise EOFError("Unexpected EOF while reading varint")
                byte = b[0]
                result |= ((byte & 0x7F) << shift)
                if (byte & 0x80) == 0:
                    break
                shift += 7
            return result

        for i in range(A):
            lhs_var = I + 1 + i
            lhs = 2 * lhs_var
            delta1 = read_varint(f)
            delta2 = read_varint(f)
            r1 = lhs - delta1
            r2 = r1 - delta2
            ands.append((lhs, r1, r2))

        # inputs are variables 1..I -> literals 2..2I
        inputs = [2 * i for i in range(1, I + 1)]

        return M, I, L, O, A, inputs, ands, outputs

# -------------------------
# 6) TikZ writer (same logic as earlier)
# -------------------------
def write_aig_tikz(filename, M, inputs, ands, outputs, title="AIG", xsep=3.0, ysep=1.2):
    # inputs, ands, outputs are lists of literals (ints)
    input_vars = [lit // 2 for lit in inputs]
    parents = {}
    and_vars = []
    for (lhs_lit, r1_lit, r2_lit) in ands:
        lhs_v = lhs_lit // 2
        a_v, a_inv = (r1_lit // 2, bool(r1_lit & 1))
        b_v, b_inv = (r2_lit // 2, bool(r2_lit & 1))
        parents[lhs_v] = [(a_v, a_inv), (b_v, b_inv)]
        and_vars.append(lhs_v)

    used_vars = set(input_vars) | set(and_vars)

    levels = {}
    for v in input_vars:
        levels[v] = 0

    for v in and_vars:
        ps = parents.get(v, [])
        parent_levels = []
        for (pv, inv) in ps:
            if pv not in levels:
                levels[pv] = 0
            parent_levels.append(levels[pv])
        levels[v] = (max(parent_levels) if parent_levels else 0) + 1

    output_vars = [lit // 2 for lit in outputs]
    max_level = max(levels.values()) if levels else 0
    out_level = max_level + 1

    level_nodes = {}
    for v in sorted(used_vars, key=lambda x: (levels.get(x, 0), x)):
        lvl = levels.get(v, 0)
        level_nodes.setdefault(lvl, []).append(v)

    positions = {}
    for lvl, nodes in sorted(level_nodes.items()):
        n = len(nodes)
        start = - (n - 1) / 2.0 * ysep
        for i, v in enumerate(nodes):
            x = lvl * xsep
            y = start + i * ysep
            positions[v] = (x, y)

    # outputs positions
    out_positions = []
    n_out = len(outputs)
    start_out = - (n_out - 1) / 2.0 * ysep
    for i, lit in enumerate(outputs):
        x = out_level * xsep
        y = start_out + i * ysep
        out_positions.append((lit, (x, y)))

    p = Path(filename)
    with p.open("w", encoding="utf8") as f:
        f.write("% Auto-generated TikZ AIG diagram\n")
        f.write("\\documentclass[tikz,border=2mm]{standalone}\n")
        f.write("\\usepackage{tikz}\n")
        f.write("\\usetikzlibrary{shapes,arrows.meta,positioning}\n")
        f.write("\\begin{document}\n")
        f.write("\\begin{tikzpicture}[every node/.style={font=\\small}, >=Stealth]\n\n")

        # nodes
        for v in sorted(used_vars):
            x, y = positions[v]
            if v in input_vars:
                f.write(f"\\node[draw, rectangle, minimum width=8mm, minimum height=4mm] (n{v}) at ({x:.3f},{y:.3f}) {{In{v}}};\n")
            else:
                f.write(f"\\node[draw, circle, minimum size=7mm] (n{v}) at ({x:.3f},{y:.3f}) {{{v}}};\n")

        # edges
        for lhs_v in and_vars:
            ps = parents[lhs_v]
            for (pv, inv) in ps:
                if pv not in positions:
                    positions[pv] = (-1.0 * xsep, 0.0)
                    f.write(f"\\node[draw, rectangle] (n{pv}) at ({positions[pv][0]:.3f},{positions[pv][1]:.3f}) {{{pv}}};\n")
                if inv:
                    f.write(f"\\draw[->] (n{pv}) -- node[midway,draw,circle,fill=white,inner sep=0.6pt] {{}} (n{lhs_v});\n")
                else:
                    f.write(f"\\draw[->] (n{pv}) -- (n{lhs_v});\n")

        # outputs
        for idx, (lit, (x, y)) in enumerate(out_positions):
            v = lit // 2
            inv = bool(lit & 1)
            f.write(f"\\node[draw, rectangle, minimum width=10mm] (out{idx}) at ({x:.3f},{y:.3f}) {{Out{idx}}};\n")
            if v not in positions:
                positions[v] = ((out_level-1) * xsep, y)
                f.write(f"\\node[draw, circle] (n{v}) at ({positions[v][0]:.3f},{positions[v][1]:.3f}) {{{v}}};\n")
            if inv:
                f.write(f"\\draw[->] (n{v}) -- node[midway,draw,circle,fill=white,inner sep=0.6pt] {{}} (out{idx});\n")
            else:
                f.write(f"\\draw[->] (n{v}) -- (out{idx});\n")

        f.write("\n\\end{tikzpicture}\n")
        f.write("\\end{document}\n")
    print(f"Wrote TikZ file: {p.absolute()}")

# -------------------------
# 7) Main pipeline
# -------------------------
def aig_to_blif(aig_bin, directory):
    workdir     = Path(directory)
    blif_out    = workdir / "mapped.blif"
    verilog_out = workdir / "mapped.v"
    mapped_aig  = workdir / "mapped_out.aig"
    tikz_orig   = workdir / "aig_original.tex"
    tikz_mapped = workdir / "aig_mapped.tex"

    # run ABC: read binary aig, strash, print stats, if -K 6, strash, write mapped aig + other outputs
    abc_script  = f"""
    read {aig_bin}
    strash
    print_stats
    if -K 2
    strash
    print_stats
    write_blif {blif_out}
    write_verilog {verilog_out}
    write_aiger {mapped_aig}
    """

    print("Running ./abc ... (this may take a moment)")
    proc = run_abc_script(abc_script)
    print("=== ABC STDOUT ===")
    print(proc.stdout)
    print("=== ABC STDERR ===")
    print(proc.stderr, file=sys.stderr)

    # parse original binary AIG and write TikZ
    try:
        parsed_orig = read_binary_aig(aig_bin)
    except Exception as e:
        print("Error parsing original binary AIG:", e, file=sys.stderr)
        return

    M2, I2, L2, O2, A2, inputs2, ands2, outputs2 = parsed_orig
    write_aig_tikz(tikz_orig, M2, inputs2, ands2, outputs2, title="Original AIG")
    print("Original AIG TikZ written to:", tikz_orig)

    # parse mapped AIG (written by ABC)
    if not mapped_aig.exists():
        print("Mapped AIG not found; ABC may have failed to write it.", file=sys.stderr)
        return

    try:
        parsed_mapped = read_binary_aig(mapped_aig)
    except Exception as e:
        print("Error parsing mapped binary AIG:", e, file=sys.stderr)
        # still continue; original diagram exists
        return

    M3, I3, L3, O3, A3, inputs3, ands3, outputs3 = parsed_mapped
    write_aig_tikz(tikz_mapped, M3, inputs3, ands3, outputs3, title="Mapped AIG")
    print("Mapped AIG TikZ written to:", tikz_mapped)

    # final summary
    print("\nAll artifacts in:", workdir)
    print("Files created:")
    for p in [aig_bin, blif_out, verilog_out, mapped_aig, tikz_orig, tikz_mapped]:
        print(" -", p)

if __name__ == "__main__":
    esop = r"""
    !x5 ^ !x4 ^ x2x3!x4 ^ x2x3x5 ^ x3 ^ !x2
    """.strip()

    res = esop_to_aiger(esop)

    with open("out.aag", "w", encoding="utf-8") as f:
        f.write(res.aag)

    with open("out.aig", "wb") as f:
        f.write(res.aig)

    aig_to_blif('out.aig')
