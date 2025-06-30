import itertools
from qiskit import QuantumCircuit
import numpy as np
import pickle
import os

def evaluate_function_from_truth_table(truth_table, xa, xb, xc):
    """Evaluate Boolean function from truth table"""
    key = f"{xa}{xb}{xc}"
    return truth_table[key]

def compute_coefficients_from_truth_table(truth_table):
    """Compute Walsh-Hadamard coefficients from truth table"""
    n = 3  
    coeffs = {}
    
    for a_bits in itertools.product([0, 1], repeat=n):
        sum_value = 0
        for x_bits in itertools.product([0, 1], repeat=n):
            xa, xb, xc = x_bits
            f_x = evaluate_function_from_truth_table(truth_table, xa, xb, xc)
            f_sign = (-1) ** f_x
            
            a_dot_x = (a_bits[0] * xa) ^ (a_bits[1] * xb) ^ (a_bits[2] * xc)
            chi_sign = (-1) ** a_dot_x
            
            sum_value += f_sign * chi_sign
        
        coeff = sum_value / (2 ** n)
        coeffs["".join(map(str, a_bits))] = coeff
    
    return coeffs

def evaluate_function(expr, xa, xb, xc):
    """Evaluate Boolean expression with given variable values - FIXED for negations"""
    # First handle negations before replacing variables
    expr_eval = expr.replace("~Xa", f"(1-{xa})")
    expr_eval = expr_eval.replace("~Xb", f"(1-{xb})")  
    expr_eval = expr_eval.replace("~Xc", f"(1-{xc})")
    
    # Then replace regular variables
    expr_eval = expr_eval.replace("Xa", str(xa))
    expr_eval = expr_eval.replace("Xb", str(xb))
    expr_eval = expr_eval.replace("Xc", str(xc))
    
    # Handle remaining negations
    expr_eval = expr_eval.replace("~0", "1").replace("~1", "0")
    
    try:
        result = eval(expr_eval) % 2
        return result
    except Exception as e:
        print(f"    Error evaluating expression '{expr_eval}': {e}")
        return 0

def compute_standard_inner_product(func_expr):
    """Compute Walsh-Hadamard coefficients for the Boolean function"""
    n = 3  
    coeffs = {}
    
    for a_bits in itertools.product([0, 1], repeat=n):
        sum_value = 0
        for x_bits in itertools.product([0, 1], repeat=n):
            xa, xb, xc = x_bits
            f_x = evaluate_function(func_expr, xa, xb, xc)
            f_sign = (-1) ** f_x
            
            a_dot_x = (a_bits[0] * xa) ^ (a_bits[1] * xb) ^ (a_bits[2] * xc)
            chi_sign = (-1) ** a_dot_x
            
            sum_value += f_sign * chi_sign
        
        coeff = sum_value / (2 ** n)
        coeffs["".join(map(str, a_bits))] = coeff
    
    return coeffs

def canonical_xor(expr):
    """Return a canonical (sorted) XOR expression"""
    if not expr or expr == "0":
        return "0"
    parts = expr.split('⊕')
    parts = [p for p in parts if p != "0" and p.strip()]
    if not parts:
        return "0"
    parts.sort()
    return '⊕'.join(parts)

def apply_phase_gate(qc, qubit, coeff):
    """Apply appropriate phase gate based on coefficient value"""
    if abs(coeff - 0.25) < 1e-10:
        qc.t(qubit)
    elif abs(coeff + 0.25) < 1e-10:
        qc.tdg(qubit)
    elif abs(coeff - 0.5) < 1e-10:
        qc.s(qubit)
    elif abs(coeff + 0.5) < 1e-10:
        qc.sdg(qubit)
    elif abs(coeff - 0.75) < 1e-10:
        qc.s(qubit)
        qc.t(qubit)
    elif abs(coeff + 0.75) < 1e-10:
        qc.sdg(qubit)
        qc.tdg(qubit)
    elif abs(coeff - 1.0) < 1e-10:
        qc.z(qubit)
    elif abs(coeff + 1.0) < 1e-10:
        qc.z(qubit)

class IntelligentQubitMonitor:
    """Intelligent monitoring with strategic CNOT tracking"""
    
    def __init__(self):
        self.qubit_states = ["X1", "X2", "X3"]
        self.original_states = ["X1", "X2", "X3"]
        self.step_counter = 1
        self.cnot_history = []
        self.state_history = [
            [self.qubit_states[0]],
            [self.qubit_states[1]],
            [self.qubit_states[2]]]
    
    def apply_cnot(self, control, target):
        """Apply CNOT and update state tracking"""
        control_var = f"X{control+1}"
        current_target = self.qubit_states[target]
        
        self.cnot_history.append((control, target))
        if current_target == f"X{target+1}":
            self.qubit_states[target] = f"X{control+1}⊕X{target+1}"
        else:
            if control_var in current_target:
                self.qubit_states[target] = self._remove_xor_variable(current_target, control_var)
            else:
                self.qubit_states[target] = f"X{control+1}⊕{current_target}"
        
        for i in range(3):
            self.state_history[i].append(self.qubit_states[i])
    
    def _remove_xor_variable(self, expression, var_to_remove):
        """Remove variable from XOR expression"""
        if not expression or expression == "0":
            return "0"
        parts = expression.split('⊕')
        remaining_parts = [part for part in parts if part != var_to_remove and part.strip()]
        
        if len(remaining_parts) == 0:
            return "0"
        elif len(remaining_parts) == 1:
            return remaining_parts[0]
        else:
            return '⊕'.join(remaining_parts)
    
    def analyze_and_restore(self, qc):
        """Intelligent restoration - only restore qubits that need it"""
        restoration_cnots = []
        
        for i, current_state in enumerate(self.qubit_states):
            target_state = self.original_states[i]
            
            if current_state == target_state:
                continue
            else:
                cnots_needed = self._find_restoration_cnots(i, current_state, target_state)
                restoration_cnots.extend(cnots_needed)
        
        for control, target in restoration_cnots:
            qc.cx(control, target)
            self.apply_cnot(control, target)
        
        return qc
    
    def _find_restoration_cnots(self, qubit_idx, current_state, target_state):
        """Find CNOTs needed to restore a qubit to its original state"""
        cnots_needed = []
        
        if target_state == f"X{qubit_idx+1}" and "⊕" in current_state:
            parts = current_state.split('⊕')
            for part in parts:
                if part != target_state and part.startswith('X') and len(part) == 2:
                    try:
                        var_num = int(part[1:])
                        control_qubit = var_num - 1
                        if 0 <= control_qubit < 3:
                            cnots_needed.append((control_qubit, qubit_idx))
                    except ValueError:
                        continue
        
        return cnots_needed

def build_quantum_circuit_with_intelligent_monitoring(coefficients, verbose=False):
    """Build quantum circuit with intelligent monitoring - OPTIMIZED VERSION"""
    n_qubits = 3
    qc = QuantumCircuit(n_qubits)
    monitor = IntelligentQubitMonitor()
    
    # Step 1: Process single-qubit terms first
    for a_string, coeff in coefficients.items():
        if abs(coeff) > 1e-10:
            involved_qubits = [i for i, bit in enumerate(a_string) if bit == '1']
            
            if len(involved_qubits) == 1:
                target_qubit = involved_qubits[0]
                apply_phase_gate(qc, target_qubit, coeff)
                monitor.step_counter += 1
    
    # Step 2: Process two-qubit terms
    # X2⊕X3 (a = "011")
    if "011" in coefficients and abs(coefficients["011"]) > 1e-10:
        coeff = coefficients["011"]
        qc.cx(1, 2)
        monitor.apply_cnot(1, 2)
        if canonical_xor(monitor.qubit_states[2]) == "X2⊕X3":
            apply_phase_gate(qc, 2, coeff)
            monitor.step_counter += 1
    
    # X1⊕X3 (a = "101")
    if "101" in coefficients and abs(coefficients["101"]) > 1e-10:
        coeff = coefficients["101"]
        qc.cx(0, 2)
        monitor.apply_cnot(0, 2)
        if canonical_xor(monitor.qubit_states[2]) == "X1⊕X3":
            apply_phase_gate(qc, 2, coeff)
            monitor.step_counter += 1
    
    # X1⊕X2 (a = "110")
    if "110" in coefficients and abs(coefficients["110"]) > 1e-10:
        coeff = coefficients["110"]
        qc.cx(0, 1)
        monitor.apply_cnot(0, 1)
        if canonical_xor(monitor.qubit_states[1]) == "X1⊕X2":
            apply_phase_gate(qc, 1, coeff)
            monitor.step_counter += 1
    
    # Step 3: Process three-qubit terms
    # X1⊕X2⊕X3 (a = "111")
    if "111" in coefficients and abs(coefficients["111"]) > 1e-10:
        coeff = coefficients["111"]
        
        current_state = canonical_xor(monitor.qubit_states[2])
        
        if current_state == "0" or current_state == "X3":
            qc.cx(1, 2)
            monitor.apply_cnot(1, 2)
            qc.cx(0, 2)
            monitor.apply_cnot(0, 2)
        elif current_state == "X1⊕X3":
            qc.cx(1, 2)
            monitor.apply_cnot(1, 2)
        elif current_state == "X2⊕X3":
            qc.cx(0, 2)
            monitor.apply_cnot(0, 2)
        
        final_state = canonical_xor(monitor.qubit_states[2])
        if final_state == "X1⊕X2⊕X3":
            apply_phase_gate(qc, 2, coeff)
            monitor.step_counter += 1
    
    # RESTORATION PHASE
    qc = monitor.analyze_and_restore(qc)
    
    return qc, monitor

def precompute_all_256_circuits():
    """Precompute all 256 possible 3-variable Boolean function circuits"""
    print("🚀 Precomputing all 256 circuits...")
    cache = {}
    n = 3
    
    for func_int in range(256):
        if func_int % 32 == 0:
            print(f"  Progress: {func_int}/256 ({func_int/256*100:.1f}%)")
        
        # Create truth table for this function
        truth_table = {}
        for i in range(2**n):
            truth_table[format(i, '03b')] = (func_int >> i) & 1
        
        # Compute coefficients from truth table
        coeffs = compute_coefficients_from_truth_table(truth_table)
        
        # Build circuit
        circuit, monitor = build_quantum_circuit_with_intelligent_monitoring(coeffs, verbose=False)
        
        # Store in cache
        cache[func_int] = {
            'coefficients': coeffs,
            'circuit': circuit,
            'truth_table': truth_table,
            'gates': len(circuit.data),
            'depth': circuit.depth()
        }
    
    print("✅ All 256 circuits precomputed!")
    return cache

def function_to_truth_table(func_expr):
    """Convert Boolean function expression to truth table integer"""
    truth_values = []
    
    for x_bits in itertools.product([0, 1], repeat=3):
        xa, xb, xc = x_bits
        f_x = evaluate_function(func_expr, xa, xb, xc)
        truth_values.append(f_x)
    
    # Convert truth table to integer
    func_int = 0
    for i, val in enumerate(truth_values):
        func_int |= (val << i)
    
    return func_int, truth_values

def lookup_circuit_from_cache(func_expr, cache):
    """Lookup precomputed circuit from cache"""
    try:
        func_int, truth_values = function_to_truth_table(func_expr)
        
        if func_int in cache:
            return cache[func_int], func_int, truth_values
        else:
            return None, func_int, truth_values
    except Exception as e:
        print(f"Error in lookup: {e}")
        return None, None, None

def save_cache_to_file(cache, filename="circuit_cache.pkl"):
    """Save precomputed cache to file"""
    try:
        with open(filename, 'wb') as f:
            pickle.dump(cache, f)
        print(f"💾 Cache saved to {filename}")
    except Exception as e:
        print(f"Error saving cache: {e}")

def load_cache_from_file(filename="circuit_cache.pkl"):
    """Load precomputed cache from file"""
    try:
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                cache = pickle.load(f)
            print(f"📁 Cache loaded from {filename}")
            return cache
        else:
            return None
    except Exception as e:
        print(f"Error loading cache: {e}")
        return None

def extract_qiskit_circuit_info(qc):
    qubit_names = [f"q{i}" for i in range(qc.num_qubits)]
    gate_sequence = []
    for instr, qargs, cargs in qc.data:
        gate_name = instr.name
        qubits = [qc.qubits.index(q) for q in qargs]
        gate_sequence.append((gate_name, qubits))
    return qubit_names, gate_sequence

def qiskit_to_qc_format(qubit_names, gate_sequence):
    var_line = ".v " + " ".join(qubit_names)
    input_line = ".i " + " ".join(qubit_names)
    lines = [var_line, input_line, "", "BEGIN"]
    for gate, qubits in gate_sequence:
        if gate == 'h':
            lines.append(f"H {qubit_names[qubits[0]]}")
        elif gate == 'cx':
            lines.append(f"tof {qubit_names[qubits[0]]} {qubit_names[qubits[1]]}")
        elif gate == 't':
            lines.append(f"T {qubit_names[qubits[0]]}")
        elif gate == 'tdg':
            lines.append(f"T* {qubit_names[qubits[0]]}")
        elif gate == 's':
            lines.append(f"P {qubit_names[qubits[0]]}")
        elif gate == 'sdg':
            lines.append(f"P* {qubit_names[qubits[0]]}")
        elif gate == 'z':
            lines.append(f"Z {qubit_names[qubits[0]]}")
        elif gate == 'x':
            lines.append(f"X {qubit_names[qubits[0]]}")
        else:
            lines.append(f"# Unsupported gate: {gate} {qubits}")
    lines.append("END")
    return "\n".join(lines)

def main():
    """Main function with precomputation and lookup - no options, only lookup"""
    print("🎯 Quantum Boolean Function Compiler with Precomputation")
    print("🚀 Ultra-fast circuit generation using lookup tables")
    print("="*60)
    
    # Try to load existing cache
    cache = load_cache_from_file()
    
    if cache is None:
        print("📊 No existing cache found. Precomputing all 256 circuits...")
        cache = precompute_all_256_circuits()
        save_cache_to_file(cache)
    else:
        print(f"✅ Loaded cache with {len(cache)} precomputed circuits")
    
    print("\n" + "="*60)
    print("Ready for ultra-fast circuit generation!")
    print("="*60)
    
    while True:
        func_input = input("\nEnter the Boolean function (use Xa, Xb, Xc as variables, ~ for negation) or 'quit' to exit: ")
        if func_input.lower() == 'quit':
            print("👋 Goodbye!")
            break
        
        try:
            print(f"\n🔄 Processing function: {func_input}")
            
            # Lookup from cache
            result, func_int, truth_values = lookup_circuit_from_cache(func_input, cache)
            
            if result is not None:
                print(f"⚡ Found in cache! Function integer: {func_int}")
                print(f"📊 Truth table: {truth_values}")
                
                circuit = result['circuit']
                coefficients = result['coefficients']
                
                print(f"\n📋 Circuit Diagram:")
                print(circuit.draw(output='text'))
                
                print(f"\n🔍 Detailed Gate List:")
                for i, (instruction, qargs, cargs) in enumerate(circuit.data):
                    qubit_indices = [circuit.qubits.index(q) for q in qargs]
                    print(f"  Gate {i+1}: {instruction.name} on qubit(s) {qubit_indices}")
                
                print(f"\n📈 Coefficients: {coefficients}")
                
                # Generate and save circuit file
                qubit_names, gate_sequence = extract_qiskit_circuit_info(circuit)
                qc_file_content = qiskit_to_qc_format(qubit_names, gate_sequence)
                
                filename = "generated_circuit.qc"
                with open(filename, "w") as f:
                    f.write(qc_file_content)
                
                print(f"\n💾 Circuit saved to: {filename}")
                print(f"\n📊 Circuit Statistics:")
                print(f"   Qubits: {circuit.num_qubits}")
                print(f"   Gates: {len(circuit.data)}")
                print(f"   Depth: {circuit.depth()}")
                print(f"   Function Integer: {func_int}")
                
            else:
                print(f"❌ Function not found in cache (this shouldn't happen!)")
                print(f"Function integer: {func_int}")
            
        except Exception as e:
            print(f"❌ Error generating circuit: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
