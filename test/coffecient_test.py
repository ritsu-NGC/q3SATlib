import pytest
import sys
import os

sys.path.append(os.path.join('../src/test'))

from testquantum import *

class CoffecientsToFunctionTests:
    example_coeffs = {
        '000': 0.75,
        '001': 0.25,
        '010': -0.5,
        '011': -0.25,
        '100': 0.25,
        '101': -0.25,
        '110': -0.25,
        '111': 0.25
    }

    expected_truth_table = [
        ((0, 0, 0), 0),
        ((0, 0, 1), 0),
        ((0, 1, 0), 0),
        ((0, 1, 1), 0),
        ((1, 0, 0), 0),
        ((1, 0, 1), 0),
        ((1, 1, 0), 0),
        ((1, 1, 1), 1),
    ]

    expected_sum_of_minterms = '(Xa & Xb & Xc)'

    def test_reconstruct_function_from_coeffs(self):
        for x_bits, expected in self.expected_truth_table:
            assert reconstruct_function_from_coeffs(self.example_coeffs, x_bits) == expected

    def test_build_truth_table_from_coeffs(self):
        truth_table = build_truth_table_from_coeffs(self.example_coeffs)
        assert truth_table == self.expected_truth_table

    def test_generate_sum_of_minterms(self):
        truth_table = build_truth_table_from_coeffs(self.example_coeffs)
        minterm_expr = generate_sum_of_minterms(truth_table)
        assert minterm_expr == self.expected_sum_of_minterms
