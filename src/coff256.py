import numpy as np
import itertools
import sys

np.set_printoptions(threshold=sys.maxsize)  # Ensure full array print

def generate_all_coefficients_and_truth_tables():
    n = 3
    num_inputs = 2**n
    all_truth_tables = np.array([
        [int(bit) for bit in np.binary_repr(i, width=num_inputs)]
        for i in range(2**num_inputs)
    ], dtype=int)
    a_vectors = list(itertools.product([0, 1], repeat=n))
    x_vectors = list(itertools.product([0, 1], repeat=n))
    chi_signs = np.zeros((len(a_vectors), len(x_vectors)), dtype=int)
    for a_idx, a in enumerate(a_vectors):
        for x_idx, x in enumerate(x_vectors):
            dot_prod = sum(ai*xi for ai, xi in zip(a, x)) % 2
            chi_signs[a_idx, x_idx] = (-1)**dot_prod
    coefficients = np.zeros((256, 8), dtype=float)
    for func_idx, truth_table in enumerate(all_truth_tables):
        f_signs = (-1)**truth_table
        coeffs = (f_signs @ chi_signs.T) / 8
        coefficients[func_idx] = coeffs
    return all_truth_tables, coefficients

# Generate
truth_tables, coefficient_matrix = generate_all_coefficients_and_truth_tables()

# Print all functions and their coefficients
for idx in range(256):
    print(f"Function {idx}:")
    print(f"  Truth table: {truth_tables[idx].tolist()}")
    print(f"  Coefficients: {coefficient_matrix[idx].tolist()}")
    print("-" * 60)
