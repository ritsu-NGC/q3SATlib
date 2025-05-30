import itertools

def reconstruct_function_from_coeffs(coeffs, x_bits):
    n = len(x_bits)
    result = 0
    for a_bits_str, coeff in coeffs.items():
        a_bits = tuple(int(b) for b in a_bits_str)
        a_dot_x = sum(a * x for a, x in zip(a_bits, x_bits)) % 2
        result += coeff * ((-1) ** a_dot_x)
    # Convert back to Boolean output (0 or 1)
    return int(round((1 - result) / 2)) % 2

def build_truth_table_from_coeffs(coeffs):
    n = 3  # For Xa, Xb, Xc
    truth_table = []
    for x_bits in itertools.product([0, 1], repeat=n):
        output = reconstruct_function_from_coeffs(coeffs, x_bits)
        truth_table.append((x_bits, output))
    return truth_table

def generate_sum_of_minterms(truth_table):
    terms = []
    var_names = ['Xa', 'Xb', 'Xc']
    for x_bits, output in truth_table:
        if output == 1:
            term_parts = []
            for var, bit in zip(var_names, x_bits):
                if bit == 1:
                    term_parts.append(var)
                else:
                    term_parts.append(f"~{var}")
            terms.append('(' + ' & '.join(term_parts) + ')')
    if terms:
        return ' | '.join(terms)
    else:
        return '0'  # Constant zero function

if __name__ == "__main__":
    # === Example: coefficients dictionary ===
    example_coeffs = {
        '000': 0.0,
        '001': 0.0,
        '010': 0.5,
        '011': -0.5,
        '100': 0.5,
        '101': 0.5,
        '110': 0.0,
        '111': 0.0
    }

    truth_table = build_truth_table_from_coeffs(example_coeffs)

    print("Recovered Truth Table:")
    for x_bits, output in truth_table:
        print(f"x = {x_bits} → f(x) = {output}")

    sum_of_minterms = generate_sum_of_minterms(truth_table)
    print("\n✅ Reconstructed Boolean Function (Sum of Minterms):")
    print(sum_of_minterms)
