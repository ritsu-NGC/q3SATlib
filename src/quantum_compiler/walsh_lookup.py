"""
Walsh-Hadamard coefficient lookup table implementation
Provides O(1) coefficient retrieval for Boolean functions
"""

import pickle
import os
from itertools import product

class WalshHadamardLookup:
    def __init__(self, cache_file="cache_data/walsh_coefficients_cache.pkl"):
        self.cache_file = cache_file
        self.coefficient_cache = {}
        self._ensure_cache_directory()
        self.load_or_generate_cache()
    
    def _ensure_cache_directory(self):
        """Create cache directory if it doesn't exist"""
        cache_dir = os.path.dirname(self.cache_file)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def evaluate_function(self, expr, xa, xb, xc):
        """Evaluate Boolean expression with given variable values"""
        expr_eval = expr.replace("Xa", str(xa)).replace("Xb", str(xb)).replace("Xc", str(xc))
        return eval(expr_eval) % 2
    
    def generate_function_key(self, func_expr):
        """Generate unique key for Boolean function based on truth table"""
        truth_table = []
        for x_bits in product([0, 1], repeat=3):
            xa, xb, xc = x_bits
            result = self.evaluate_function(func_expr, xa, xb, xc)
            truth_table.append(result)
        return tuple(truth_table)
    
    def load_or_generate_cache(self):
        """Load existing cache or generate complete lookup table"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    self.coefficient_cache = pickle.load(f)
                print(f" Loaded {len(self.coefficient_cache)} cached coefficient sets")
            except Exception as e:
                print(f" Error loading cache: {e}")
                self.generate_complete_cache()
        else:
            print(" Generating complete Walsh-Hadamard lookup table...")
            self.generate_complete_cache()
    
    def generate_complete_cache(self):
        """Precompute coefficients for all 2^8 = 256 possible Boolean functions"""
        print(" Computing coefficients for all 3-variable Boolean functions...")
        
        for i, truth_table in enumerate(product([0, 1], repeat=8)):
            coeffs = self.compute_coefficients_from_truth_table(truth_table)
            self.coefficient_cache[truth_table] = coeffs
            
            if (i + 1) % 64 == 0:
                print(f"   Progress: {i + 1}/256 functions processed")
        
        # Save cache
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.coefficient_cache, f)
            print(f" Generated and cached {len(self.coefficient_cache)} coefficient sets")
        except Exception as e:
            print(f" Error saving cache: {e}")
    
    def compute_coefficients_from_truth_table(self, truth_table):
        """Compute Walsh-Hadamard coefficients from truth table"""
        coeffs = {}
        for a_bits in product([0, 1], repeat=3):
            sum_value = 0
            for i, x_bits in enumerate(product([0, 1], repeat=3)):
                f_x = truth_table[i]
                f_sign = (-1) ** f_x
                
                xa, xb, xc = x_bits
                a_dot_x = (a_bits[0] * xa) ^ (a_bits[1] * xb) ^ (a_bits[2] * xc)
                chi_sign = (-1) ** a_dot_x
                
                sum_value += f_sign * chi_sign
            
            coeff = sum_value / 8
            coeffs["".join(map(str, a_bits))] = coeff
        
        return coeffs
    
    def get_coefficients(self, func_expr):
        """Get coefficients with O(1) lookup"""
        try:
            function_key = self.generate_function_key(func_expr)
            return self.coefficient_cache.get(function_key, {})
        except Exception as e:
            print(f" Error getting coefficients: {e}")
            return {}
    
    def cache_stats(self):
        """Get cache statistics"""
        return {
            'total_functions': len(self.coefficient_cache),
            'cache_file_exists': os.path.exists(self.cache_file),
            'cache_file_size': os.path.getsize(self.cache_file) if os.path.exists(self.cache_file) else 0
        }
