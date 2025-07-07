"""
Quantum circuit template caching system
Provides precomputed gate sequences for common coefficient patterns
"""

import pickle
import os
from itertools import product

class QuantumCircuitTemplateCache:
    def __init__(self, template_file="cache_data/circuit_templates.pkl"):
        self.template_file = template_file
        self.circuit_templates = {}
        self._ensure_cache_directory()
        self.load_or_generate_templates()
    
    def _ensure_cache_directory(self):
        """Create cache directory if it doesn't exist"""
        cache_dir = os.path.dirname(self.template_file)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def generate_coefficient_signature(self, coefficients):
        """Create signature from non-zero coefficients"""
        signature = []
        for key in sorted(coefficients.keys()):
            if abs(coefficients[key]) > 1e-10:
                quantized = self.quantize_coefficient(coefficients[key])
                signature.append((key, quantized))
        return tuple(signature)
    
    def quantize_coefficient(self, coeff):
        """Map coefficient to standard quantum gate values"""
        standard_values = [0.25, -0.25, 0.5, -0.5, 0.75, -0.75, 1.0, -1.0]
        return min(standard_values, key=lambda x: abs(x - coeff))
    
    def load_or_generate_templates(self):
        """Load or generate circuit templates"""
        if os.path.exists(self.template_file):
            try:
                with open(self.template_file, 'rb') as f:
                    self.circuit_templates = pickle.load(f)
                print(f" Loaded {len(self.circuit_templates)} circuit templates")
            except Exception as e:
                print(f" Error loading templates: {e}")
                self.generate_common_templates()
        else:
            print("Generating circuit templates...")
            self.generate_common_templates()
    
    def generate_common_templates(self):
        """Generate templates for common coefficient patterns"""
        # Single qubit patterns
        single_qubit_templates = {
            (('001', 0.25),): [('t', [2])],
            (('001', -0.25),): [('tdg', [2])],
            (('001', 0.5),): [('s', [2])],
            (('001', -0.5),): [('sdg', [2])],
            (('001', 1.0),): [('z', [2])],
            
            (('010', 0.25),): [('t', [1])],
            (('010', -0.25),): [('tdg', [1])],
            (('010', 0.5),): [('s', [1])],
            (('010', -0.5),): [('sdg', [1])],
            (('010', 1.0),): [('z', [1])],
            
            (('100', 0.25),): [('t', [0])],
            (('100', -0.25),): [('tdg', [0])],
            (('100', 0.5),): [('s', [0])],
            (('100', -0.5),): [('sdg', [0])],
            (('100', 1.0),): [('z', [0])],
        }
        
        # Two qubit patterns
        two_qubit_templates = {
            (('011', 0.25),): [('cx', [1, 2]), ('t', [2]), ('cx', [1, 2])],
            (('011', -0.25),): [('cx', [1, 2]), ('tdg', [2]), ('cx', [1, 2])],
            (('011', 0.5),): [('cx', [1, 2]), ('s', [2]), ('cx', [1, 2])],
            
            (('110', 0.25),): [('cx', [0, 1]), ('t', [1]), ('cx', [0, 1])],
            (('110', -0.25),): [('cx', [0, 1]), ('tdg', [1]), ('cx', [0, 1])],
            (('110', 0.5),): [('cx', [0, 1]), ('s', [1]), ('cx', [0, 1])],
            
            (('101', 0.25),): [('cx', [0, 2]), ('t', [2]), ('cx', [0, 2])],
            (('101', -0.25),): [('cx', [0, 2]), ('tdg', [2]), ('cx', [0, 2])],
            (('101', 0.5),): [('cx', [0, 2]), ('s', [2]), ('cx', [0, 2])],
        }
        
        # Three qubit patterns
        three_qubit_templates = {
            (('111', 0.25),): [
                ('cx', [0, 2]), ('cx', [1, 2]), ('t', [2]), 
                ('cx', [1, 2]), ('cx', [0, 2])
            ],
            (('111', -0.25),): [
                ('cx', [0, 2]), ('cx', [1, 2]), ('tdg', [2]), 
                ('cx', [1, 2]), ('cx', [0, 2])
            ],
        }
        
        # Combine all templates
        self.circuit_templates = {
            **single_qubit_templates,
            **two_qubit_templates,
            **three_qubit_templates
        }
        
        # Save templates
        try:
            with open(self.template_file, 'wb') as f:
                pickle.dump(self.circuit_templates, f)
            print(f" Generated and saved {len(self.circuit_templates)} circuit templates")
        except Exception as e:
            print(f" Error saving templates: {e}")
    
    def get_template(self, coefficients):
        """Get precomputed circuit template"""
        signature = self.generate_coefficient_signature(coefficients)
        return self.circuit_templates.get(signature, None)
    
    def add_custom_template(self, coefficients, gate_sequence):
        """Add custom template to cache"""
        signature = self.generate_coefficient_signature(coefficients)
        self.circuit_templates[signature] = gate_sequence
        
        # Save updated templates
        try:
            with open(self.template_file, 'wb') as f:
                pickle.dump(self.circuit_templates, f)
        except Exception as e:
            print(f" Error saving updated templates: {e}")
    
    def template_stats(self):
        """Get template cache statistics"""
        return {
            'total_templates': len(self.circuit_templates),
            'template_file_exists': os.path.exists(self.template_file),
            'template_file_size': os.path.getsize(self.template_file) if os.path.exists(self.template_file) else 0
        }
