"""
Optimized quantum Boolean function compiler
Combines Walsh-Hadamard lookup and circuit templates for fast compilation
"""

import pickle
import os
from qiskit import QuantumCircuit
from walsh_lookup import WalshHadamardLookup
from circuit_templates import QuantumCircuitTemplateCache

class OptimizedQuantumCompiler:
    def __init__(self, complete_cache_file="cache_data/complete_circuits_cache.pkl"):
        self.walsh_lookup = WalshHadamardLookup()
        self.template_cache = QuantumCircuitTemplateCache()
        self.complete_cache_file = complete_cache_file
        self.complete_circuit_cache = {}
        self._ensure_cache_directory()
        self._load_complete_cache()
    
    def _ensure_cache_directory(self):
        """Create cache directory if it doesn't exist"""
        cache_dir = os.path.dirname(self.complete_cache_file)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _load_complete_cache(self):
        """Load complete circuit cache"""
        if os.path.exists(self.complete_cache_file):
            try:
                with open(self.complete_cache_file, 'rb') as f:
                    self.complete_circuit_cache = pickle.load(f)
                print(f"✅ Loaded {len(self.complete_circuit_cache)} complete circuits from cache")
            except Exception as e:
                print(f"❌ Error loading complete cache: {e}")
    
    def _save_complete_cache(self):
        """Save complete circuit cache"""
        try:
            with open(self.complete_cache_file, 'wb') as f:
                pickle.dump(self.complete_circuit_cache, f)
        except Exception as e:
            print(f"❌ Error saving complete cache: {e}")
    
    def compile_function_optimized(self, func_expr):
        """Optimized compilation with multi-level caching"""
        # Level 1: Check complete circuit cache
        if func_expr in self.complete_circuit_cache:
            print("⚡ Using cached complete circuit")
            return self.complete_circuit_cache[func_expr]
        
        print("🔄 Compiling new function...")
        
        # Level 2: Fast coefficient lookup O(1)
        coefficients = self.walsh_lookup.get_coefficients(func_expr)
        
        if not coefficients:
            print("❌ Could not compute coefficients")
            return None
        
        # Level 3: Template-based circuit construction
        template = self.template_cache.get_template(coefficients)
        
        if template:
            print("⚡ Using circuit template")
            qc = self.build_from_template(template)
        else:
            print("🔧 Building circuit from scratch")
            # Import here to avoid circular imports
            import quantumcircuit
            qc, _ = quantumcircuit.build_quantum_circuit_with_intelligent_monitoring(coefficients)
        
        # Cache complete result
        self.complete_circuit_cache[func_expr] = qc
        self._save_complete_cache()
        
        return qc
    
    def build_from_template(self, template):
        """Build circuit from precomputed template"""
        qc = QuantumCircuit(3)
        
        for gate_name, qubits in template:
            if gate_name == 'cx':
                qc.cx(qubits[0], qubits[1])
            elif gate_name == 't':
                qc.t(qubits[0])
            elif gate_name == 'tdg':
                qc.tdg(qubits[0])
            elif gate_name == 's':
                qc.s(qubits[0])
            elif gate_name == 'sdg':
                qc.sdg(qubits[0])
            elif gate_name == 'z':
                qc.z(qubits[0])
            elif gate_name == 'x':
                qc.x(qubits[0])
            else:
                print(f"⚠️  Unknown gate in template: {gate_name}")
        
        return qc
    
    def get_cache_stats(self):
        """Get comprehensive cache statistics"""
        walsh_stats = self.walsh_lookup.cache_stats()
        template_stats = self.template_cache.template_stats()
        
        return {
            'walsh_hadamard': walsh_stats,
            'circuit_templates': template_stats,
            'complete_circuits': {
                'total_cached': len(self.complete_circuit_cache),
                'cache_file_exists': os.path.exists(self.complete_cache_file),
                'cache_file_size': os.path.getsize(self.complete_cache_file) if os.path.exists(self.complete_cache_file) else 0
            }
        }
    
    def clear_caches(self):
        """Clear all caches"""
        cache_files = [
            self.walsh_lookup.cache_file,
            self.template_cache.template_file,
            self.complete_cache_file
        ]
        
        for cache_file in cache_files:
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                    print(f"✅ Cleared cache: {cache_file}")
                except Exception as e:
                    print(f"❌ Error clearing cache {cache_file}: {e}")
        
        # Clear in-memory caches
        self.complete_circuit_cache.clear()
        self.walsh_lookup.coefficient_cache.clear()
        self.template_cache.circuit_templates.clear()
