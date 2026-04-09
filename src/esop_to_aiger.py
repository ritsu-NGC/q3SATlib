import re
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

# ---------- AIGER builder (ASCII .aag) ----------

class AigerBuilder:
    def __init__(self, num_inputs: int):
        self.num_inputs = num_inputs
        self.next_var = num_inputs + 1  # AIGER variables: 1..M, inputs are 1..I
        self.ands: List[Tuple[int, int, int]] = []  # (lhs_lit, rhs0_lit, rhs1_lit)
        self.outputs: List[int] = []

    @staticmethod
    def lit(var: int, neg: bool = False) -> int:
        """Return AIGER literal (even=positive, odd=negated)."""
        base = 2 * var
        return base ^ (1 if neg else 0)

    @staticmethod
    def inv(l: int) -> int:
        return l ^ 1

    def new_and(self, a_lit: int, b_lit: int) -> int:
        """Create AND gate. Returns lhs literal (positive)."""
        lhs_var = self.next_var
        self.next_var += 1
        lhs_lit = self.lit(lhs_var, False)
        self.ands.append((lhs_lit, a_lit, b_lit))
        return lhs_lit

    def and_many(self, lits: List[int]) -> int:
        if not lits:
            # constant-1 is represented as literal 1 in AIGER (TRUE)
            return 1
        if len(lits) == 1:
            return lits[0]
        cur = lits[0]
        for nxt in lits[1:]:
            cur = self.new_and(cur, nxt)
        return cur

    def or2(self, p: int, q: int) -> int:
        # OR(p,q) = !( !p & !q )
        t = self.new_and(self.inv(p), self.inv(q))
        return self.inv(t)

    def xor2(self, a: int, b: int) -> int:
        # XOR(a,b) = (a & !b) | (!a & b)
        t1 = self.new_and(a, self.inv(b))
        t2 = self.new_and(self.inv(a), b)
        return self.or2(t1, t2)

    def xor_many(self, lits: List[int]) -> int:
        if not lits:
            # XOR of empty set = 0 (FALSE). FALSE is !TRUE = 0 (literal 0)
            return 0
        cur = lits[0]
        for nxt in lits[1:]:
            cur = self.xor2(cur, nxt)
        return cur

    def add_output(self, out_lit: int):
        self.outputs.append(out_lit)

    @property
    def M(self) -> int:
        return self.next_var - 1

    def emit_aag(self) -> str:
        I = self.num_inputs
        L = 0
        O = len(self.outputs)
        A = len(self.ands)
        M = self.M

        lines = []
        lines.append(f"aag {M} {I} {L} {O} {A}")
        # inputs: literals 2,4,6,...,2I
        for i in range(1, I + 1):
            lines.append(str(self.lit(i, False)))
        # outputs:
        for o in self.outputs:
            lines.append(str(o))
        # ands:
        for lhs, r0, r1 in self.ands:
            lines.append(f"{lhs} {r0} {r1}")
        return "\n".join(lines) + "\n"

# ---------- ESOP parsing ----------

LIT_RE = re.compile(r'(!)?x(\d+)\b')

def split_cubes(esop: str) -> List[str]:
    """
    Split into cubes. We treat newlines and multiple spaces as cube separators.
    Also allow '+' or '^' as cube separators if present.
    """
    # Normalize separators between cubes
    s = esop.strip()
    # Replace common cube separators with newline
    s = re.sub(r'[+\^]', '\n', s)
    # Collapse whitespace
    parts = [p.strip() for p in re.split(r'\n+', s) if p.strip()]
    return parts

def tokenize_cube(cube: str) -> List[Tuple[int, bool]]:
    """
    Return list of (var_index, negated) literals from a cube.
    Handles both '&'-separated and concatenated literals like 'x2!x4x7'.
    """
    # Remove '&' and spaces but keep '!' and 'xN'
    cleaned = cube.replace("&", " ")
    # Find all literals
    toks = []
    for m in re.finditer(r'(!)?x(\d+)', cleaned.replace(" ", "")):
        neg = bool(m.group(1))
        var = int(m.group(2))
        toks.append((var, neg))
    return toks

def compute_num_inputs(cubes: List[List[Tuple[int, bool]]]) -> int:
    mx = 0
    for cube in cubes:
        for var, _neg in cube:
            mx = max(mx, var)
    return mx

# ---------- Binary AIGER encoding ----------

def _encode_uvarint(x: int) -> bytes:
    """AIGER uses 7-bit groups with continuation bit (like little-endian base-128)."""
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

def emit_aig_binary(builder: AigerBuilder) -> bytes:
    """
    Emit binary AIGER (.aig) from the already-built network.
    Note: we don't emit symbols/comments here (optional in format).
    """
    I = builder.num_inputs
    L = 0
    O = len(builder.outputs)
    A = len(builder.ands)
    M = builder.M

    # Header is text (ASCII)
    header = f"aig {M} {I} {L} {O} {A}\n".encode("ascii")

    # Inputs are implicit in binary AIGER (not listed), but outputs ARE listed as text lines.
    # Latches would also be listed as text lines if L>0.
    out_lines = bytearray()
    for o in builder.outputs:
        out_lines.extend(f"{o}\n".encode("ascii"))

    # AND gates in binary delta encoding:
    # Each AND is (lhs rhs0 rhs1) with lhs = 2*var (even).
    # Must be in increasing lhs order (we already build sequentially).
    gates = bytearray()
    for lhs, r0, r1 in builder.ands:
        # Canonicalize: rhs0 <= rhs1
        if r0 > r1:
            r0, r1 = r1, r0
        d1 = lhs - r1
        d2 = r1 - r0
        if d1 < 0 or d2 < 0:
            raise ValueError("Invalid AIGER delta (ordering violated).")
        gates.extend(_encode_uvarint(d1))
        gates.extend(_encode_uvarint(d2))

    return bytes(header + out_lines + gates)

# ---------- Conversion ----------

@dataclass
class ConversionResult:
    builder: AigerBuilder
    aag: str
    aig: bytes
    cube_output_literals: List[int]
    final_output_literal: int

def esop_to_aiger(esop_text: str) -> ConversionResult:
    cube_strs = split_cubes(esop_text)
    print("DCDEBUG " + str(cube_strs))
    parsed_cubes = [tokenize_cube(c) for c in cube_strs]

    print("DCDEBUG " + str(parsed_cubes))

    num_inputs = compute_num_inputs(parsed_cubes)

    print("DCDEBUG " + str(num_inputs))
    b = AigerBuilder(num_inputs=num_inputs)

    cube_outs: List[int] = []

    # Build each cube as AND of its literals
    for cube in parsed_cubes:
        lits = [b.lit(var, neg) for var, neg in cube]
        cube_outs.append(b.and_many(lits))

    # Final ESOP output = XOR of cube outputs

    # final_out = b.xor_many(cube_outs)
    final_out = b

    # Outputs: first each cube output, then final output
    for co in cube_outs:
        b.add_output(co)
    #b.add_output(final_out)

    return ConversionResult(
        builder=b,
        aag=b.emit_aag(),
        aig=emit_aig_binary(b),
        cube_output_literals=cube_outs,
        final_output_literal=final_out,
    )

# ---------- CLI/demo ----------

if __name__ == "__main__":
    esop = r"""
 !x5 ^ !x4 ^ x2!x2!x4 ^ x3 ^ !x2
""".strip()

    res = esop_to_aiger(esop)

    with open("out.aag", "w", encoding="utf-8") as f:
        f.write(res.aag)

    with open("out.aig", "wb") as f:
        f.write(res.aig)

    print("Wrote out.aag and out.aig")
    print("Cube outputs (literals):", res.cube_output_literals)
    print("Final output (literal):", res.final_output_literal)
