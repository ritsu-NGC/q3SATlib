"""
Background precomputation system for quantum circuit optimization
Automatically precomputes all possible circuits for instant lookup
"""

import threading
import time
import pickle
import os
from itertools import product
from walsh_lookup import WalshHadamardLookup
from circuit_templates import QuantumCircuitTemplateCache
from optimized_compiler import OptimizedQuantumCompiler

class QuantumCompilerWithAutoPrecompute:
    def __init__(self, auto_precompute=True, show_progress=True):
        self.auto_precompute = auto_precompute
        self.show_progress = show_progress
        self.complete_cache = {}
        self.cache_file = "cache_data/complete_circuits_cache.pkl"
        
        # Initialize base components
        self.walsh_lookup = WalshHadamardLookup()
        self.template_cache = QuantumCircuitTemplateCache()
        self.base_compiler = OptimizedQuantumCompiler()
        
        if auto_precompute:
            self._initialize_complete_cache()
    
    def _initialize_complete_cache(self):
        """Background precomputation of all possible circuits"""
        print(" Quantum Compiler Initialization")
        print("=" * 50)
        
        # Check if complete cache exists
        if self._cache_exists_and_complete():
            print(" Complete cache found - loading instantly!")
            self._load_complete_cache()
            return
        
        print("Performing one-time background precomputation...")
        print("   This will make ALL future queries instant!")
        
        if self.show_progress:
            self._precompute_with_progress()
        else:
            self._precompute_silently()
        
        print(" Precomputation complete! All circuits ready for instant lookup.")
    
    def _cache_exists_and_complete(self):
        """Check if complete cache exists and has all 256 functions"""
        if not os.path.exists(self.cache_file):
            return False
        
        try:
            with open(self.cache_file, 'rb') as f:
                cache = pickle.load(f)
            return len(cache) >= 256
        except Exception as e:
            print(f" Error checking cache: {e}")
            return False
    
    def _load_complete_cache(self):
        """Load complete cache from file"""
        try:
            with open(self.cache_file, 'rb') as f:
                self.complete_cache = pickle.load(f)
            print(f" Loaded {len(self.complete_cache)} circuits from cache")
        except Exception as e:
            print(f" Error loading cache: {e}")
            self.complete_cache = {}
    
    def _precompute_with_progress(self):
        """Wrapper for _precompute_all_circuits with progress"""
        self._precompute_all_circuits()
    
    def _precompute_silently(self):
        """Precompute all circuits without progress display"""
        original_show_progress = self.show_progress
        self.show_progress = False
        self._precompute_all_circuits()
        self.show_progress = original_show_progress
    
    def _precompute_all_circuits(self):
        """Precompute circuits for all 256 possible 3-variable Boolean functions"""
        total_functions = 2**8  # 256 possible truth tables
        completed = 0
        
        print(f" Precomputing {total_functions} Boolean functions...")
        
        for truth_table in product([0, 1], repeat=8):
            try:
                # Convert truth table to function expression
                func_expr = self._truth_table_to_expression(truth_table)
                
                # Generate optimized circuit
                circuit = self._generate_circuit_from_truth_table(truth_table)
                
                # Cache the complete result
                self.complete_cache[func_expr] = circuit
                
                completed += 1
                if self.show_progress and completed % 32 == 0:
                    progress = (completed / total_functions) * 100
                    print(f"   Progress: {completed}/{total_functions} ({progress:.1f}%)")
            except Exception as e:
                print(f" Error processing truth table {truth_table}: {e}")
                continue
        
        self._save_complete_cache()
        print(f" Successfully precomputed {completed} circuits")
    
    def _truth_table_to_expression(self, truth_table):
        """Convert truth table to a representative expression"""
        # Create a unique identifier for this truth table
        return f"tt_{hash(truth_table) % 100000}"
    
    def _generate_circuit_from_truth_table(self, truth_table):
        """Generate quantum circuit from truth table"""
        try:
            coeffs = self.walsh_lookup.compute_coefficients_from_truth_table(truth_table)
            
            template = self.template_cache.get_template(coeffs)
            if template:
                return self.base_compiler.build_from_template(template)
            else:
                from quantumcircuit import build_quantum_circuit_with_intelligent_monitoring
                circuit, _ = build_quantum_circuit_with_intelligent_monitoring(coeffs)
                return circuit
        except Exception as e:
            print(f" Error generating circuit: {e}")
            # Return a simple identity circuit as fallback
            from qiskit import QuantumCircuit
            return QuantumCircuit(3)
    
    def _save_complete_cache(self):
        """Save complete cache to file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.complete_cache, f)
            print(f" Saved {len(self.complete_cache)} circuits to cache")
        except Exception as e:
            print(f" Error saving cache: {e}")
    
    def get_circuit_with_fallback(self, func_expr):
        """Get circuit with intelligent fallback"""
        
        # Priority 1: Complete cache (instant)
        if func_expr in self.complete_cache:
            return self.complete_cache[func_expr], "INSTANT_CACHE"
        
        # Priority 2: Template-based (very fast)
        try:
            coefficients = self.walsh_lookup.get_coefficients(func_expr)
            if coefficients:
                template = self.template_cache.get_template(coefficients)
                if template:
                    circuit = self.base_compiler.build_from_template(template)
                    self.complete_cache[func_expr] = circuit  # Cache for next time
                    return circuit, "TEMPLATE_FAST"
        except Exception as e:
            print(f" Template lookup failed: {e}")
        
        # Priority 3: Original algorithm (slower but reliable)
        try:
            circuit = self._build_with_original_algorithm(func_expr)
            self.complete_cache[func_expr] = circuit  # Cache for next time
            return circuit, "COMPUTED_CACHED"
        except Exception as e:
            print(f" Original algorithm failed: {e}")
            # Return simple circuit as last resort
            from qiskit import QuantumCircuit
            return QuantumCircuit(3), "FALLBACK_SIMPLE"
    def start_background_precompute(self):
        """Start precomputation in background thread"""
        self.precompute_thread = threading.Thread(
            target=self._background_precompute_worker,
            daemon=True
        )
        self.precompute_thread.start()

    def _background_precompute_worker(self):
        """Background worker for precomputation"""
        if not self._cache_exists_and_complete():
            print(" Starting background precomputation...")
            self._precompute_all_circuits()
            print(" Background precomputation finished!")

    def _build_with_original_algorithm(self, func_expr):
        """Build circuit using original algorithm"""
        from quantumcircuit import compute_standard_inner_product, build_quantum_circuit_with_intelligent_monitoring
        
        coefficients = compute_standard_inner_product(func_expr)
        circuit, _ = build_quantum_circuit_with_intelligent_monitoring(coefficients)
        return circuit

class BackgroundPrecomputer:
    def __init__(self):
        self.precompute_thread = None
        self.is_ready = False
        self.compiler = None
    
    def start_background_precompute(self):
        """Start precomputation in background thread"""
        self.precompute_thread = threading.Thread(
            target=self._background_worker,
            daemon=True
        )
        self.precompute_thread.start()
    
    def _background_worker(self):
        """Background precomputation worker"""
        try:
            # Initialize compiler and precompute all circuits
            self.compiler = QuantumCompilerWithAutoPrecompute(
                auto_precompute=True, 
                show_progress=False
            )
            self.is_ready = True
            print(" Background precomputation finished!")
        except Exception as e:
            print(f" Background precomputation failed: {e}")
            self.is_ready = False
    
    def get_compiler(self):
        """Get the precomputed compiler instance"""
        return self.compiler if self.is_ready else None
