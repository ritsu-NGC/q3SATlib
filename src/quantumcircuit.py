import itertools
from qiskit import QuantumCircuit
import numpy as np

def evaluate_function(expr, xa, xb, xc):
    """Evaluate Boolean expression with given variable values"""
    expr_eval = expr.replace("Xa", str(xa)).replace("Xb", str(xb)).replace("Xc", str(xc))
    return eval(expr_eval) % 2

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

def apply_phase_gate(qc, qubit, coeff):
    """Apply appropriate phase gate based on coefficient value"""
    if abs(coeff - 0.25) < 1e-10:
        qc.t(qubit)
        print(f"  Apply T gate to q_{qubit} (π/4 phase)")
    elif abs(coeff + 0.25) < 1e-10:
        qc.tdg(qubit)
        print(f"  Apply T† gate to q_{qubit} (-π/4 phase)")
    elif abs(coeff - 0.5) < 1e-10:
        qc.s(qubit)
        print(f"  Apply S gate to q_{qubit} (π/2 phase)")
    elif abs(coeff + 0.5) < 1e-10:
        qc.sdg(qubit)
        print(f"  Apply S† gate to q_{qubit} (-π/2 phase)")
    elif abs(coeff - 0.75) < 1e-10:
        qc.s(qubit)
        qc.t(qubit)
        print(f"  Apply S then T gate to q_{qubit} (3π/4 phase)")
    elif abs(coeff + 0.75) < 1e-10:
        qc.sdg(qubit)
        qc.tdg(qubit)
        print(f"  Apply S† then T† gate to q_{qubit} (-3π/4 phase)")
    elif abs(coeff + 1.00) < 1e-10:
        qc.z(qubit)
        print(f"  Apply Z gate to q_{qubit} (-2π/ phase)")
    elif abs(coeff - 1.00) < 1e-10:
        qc.zdg(qubit)
        print(f"  Apply Z† gate to q_{qubit} (2π/ phase)")

class IntelligentQubitMonitor:
    """Intelligent monitoring with strategic CNOT tracking"""
    
    def __init__(self):
        self.qubit_states = ["X1", "X2", "X3"]  # Current logical state
        self.original_states = ["X1", "X2", "X3"]  # Target states
        self.step_counter = 1
        self.cnot_history = []  # Track CNOTs for intelligent restoration
    
    def apply_cnot(self, control, target):
        """Apply CNOT and update state tracking"""
        control_var = f"X{control+1}"
        current_target = self.qubit_states[target]
        
        # Track this CNOT
        self.cnot_history.append((control, target))
        
        # Update target qubit state based on XOR logic
        if current_target == f"X{target+1}":
            # Simple case: X2 becomes X1⊕X2
            self.qubit_states[target] = f"X{control+1}⊕X{target+1}"
        else:
            # Complex case: handle existing XORs
            if control_var in current_target:
                # Variable already present - XOR cancels it out
                self.qubit_states[target] = self._remove_xor_variable(current_target, control_var)
            else:
                # Add new variable to existing XOR
                self.qubit_states[target] = f"X{control+1}⊕{current_target}"
        
        print(f"  State update: q_{target} becomes {self.qubit_states[target]}")
    
    def _remove_xor_variable(self, expression, var_to_remove):
        """Remove variable from XOR expression"""
        parts = expression.split('⊕')
        remaining_parts = [part for part in parts if part != var_to_remove]
        
        if len(remaining_parts) == 0:
            return "0"
        elif len(remaining_parts) == 1:
            return remaining_parts[0]
        else:
            return '⊕'.join(remaining_parts)
    
    def get_current_states(self):
        """Get current state of all qubits"""
        return self.qubit_states.copy()
    
    def analyze_and_restore(self, qc):
        """Intelligent restoration - only restore qubits that need it"""
        print("\n" + "="*70)
        print("INTELLIGENT QUBIT STATE ANALYSIS AND RESTORATION")
        print("="*70)
        
        print("Current qubit states:")
        for i, current_state in enumerate(self.qubit_states):
            target_state = self.original_states[i]
            status = "✅ ORIGINAL" if current_state == target_state else "❌ NEEDS RESTORE"
            print(f"  q_{i}: {current_state} → Target: {target_state} [{status}]")
        
        print("\nRestoration analysis:")
        
        # Apply restoration CNOTs in reverse order for qubits that need it
        restoration_cnots = []
        
        for i, current_state in enumerate(self.qubit_states):
            target_state = self.original_states[i]
            
            if current_state == target_state:
                print(f"  q_{i}: Already in original state - NO ACTION NEEDED")
            else:
                # Find CNOTs needed to restore this qubit
                cnots_needed = self._find_restoration_cnots(i, current_state, target_state)
                restoration_cnots.extend(cnots_needed)
        
        # Apply restoration CNOTs
        for control, target in restoration_cnots:
            print(f"  Applying restoration CNOT q_{control} → q_{target}")
            qc.cx(control, target)
            self.apply_cnot(control, target)
        
        print(f"\nFinal states after restoration:")
        for i, state in enumerate(self.qubit_states):
            print(f"  q_{i}: {state}")
        
        return qc
    
    def _find_restoration_cnots(self, qubit_idx, current_state, target_state):
        """Find CNOTs needed to restore a qubit to its original state"""
        cnots_needed = []
        
        if target_state == f"X{qubit_idx+1}" and "⊕" in current_state:
            # Need to cancel out extra variables
            parts = current_state.split('⊕')
            for part in parts:
                if part != target_state and part.startswith('X'):
                    var_num = int(part[1:])
                    control_qubit = var_num - 1
                    cnots_needed.append((control_qubit, qubit_idx))
        
        return cnots_needed

def build_quantum_circuit_with_intelligent_monitoring(coefficients):
    """Build quantum circuit with intelligent monitoring and strategic CNOT placement"""
    n_qubits = 3
    qc = QuantumCircuit(n_qubits)
    monitor = IntelligentQubitMonitor()
    
    print("\n" + "="*70)
    print("QUANTUM CIRCUIT WITH INTELLIGENT MONITORING")
    print("="*70)
    
    print(f"Initial states: {monitor.get_current_states()}\n")
    
    # Step 1: Apply single qubit phase gates first
    print("STEP 1: Processing single-qubit coefficients")
    print("-" * 50)
    
    for a_string, coeff in coefficients.items():
        if abs(coeff) > 1e-10:
            involved_qubits = [i for i, bit in enumerate(a_string) if bit == '1']
            
            if len(involved_qubits) == 1:
                target_qubit = involved_qubits[0]
                print(f"Step {monitor.step_counter}: Single-qubit term a = {a_string} → {coeff}")
                apply_phase_gate(qc, target_qubit, coeff)
                print(f"  States: {monitor.get_current_states()}\n")
                monitor.step_counter += 1
    
    # Step 2: Process multi-qubit terms strategically
    print("STEP 2: Processing multi-qubit coefficients")
    print("-" * 50)
    
    # X2⊕X3 (a = "011")
    if "011" in coefficients and abs(coefficients["011"]) > 1e-10:
        coeff = coefficients["011"]
        print(f"Step {monitor.step_counter}: CNOT q_1 → q_2 for X2⊕X3")
        qc.cx(1, 2)
        monitor.apply_cnot(1, 2)
        
        apply_phase_gate(qc, 2, coeff)
        print(f"  Current states: {monitor.get_current_states()}\n")
        monitor.step_counter += 1
    
    # X1⊕X2⊕X3 (a = "111")
    if "111" in coefficients and abs(coefficients["111"]) > 1e-10:
        coeff = coefficients["111"]
        print(f"Step {monitor.step_counter}: CNOT q_0 → q_2 for X1⊕X2⊕X3")
        qc.cx(0, 2)
        monitor.apply_cnot(0, 2)
        
        apply_phase_gate(qc, 2, coeff)
        print(f"  Current states: {monitor.get_current_states()}\n")
        monitor.step_counter += 1
    
    # Strategic optimization CNOT for X1⊕X3 preparation
    if "111" in coefficients and abs(coefficients["111"]) > 1e-10:
        print(f"Step {monitor.step_counter}: Strategic CNOT q_1 → q_2 (optimization)")
        qc.cx(1, 2)
        monitor.apply_cnot(1, 2)
        print(f"  Current states: {monitor.get_current_states()}\n")
        monitor.step_counter += 1
    
    # X1⊕X3 coefficient (a = "101")
    if "101" in coefficients and abs(coefficients["101"]) > 1e-10:
        coeff = coefficients["101"]
        # Apply CNOT q_0 → q_2 to map X1⊕X3 onto q_2
        qc.cx(0, 2)
        monitor.apply_cnot(0, 2)
        
        apply_phase_gate(qc, 2, coeff)
        print(f"  Current states: {monitor.get_current_states()}\n")
        monitor.step_counter += 1

    
    # X1⊕X2 (a = "110")
    if "110" in coefficients and abs(coefficients["110"]) > 1e-10:
        coeff = coefficients["110"]
        print(f"Step {monitor.step_counter}: CNOT q_0 → q_1 for X1⊕X2")
        qc.cx(0, 1)
        monitor.apply_cnot(0, 1)
        
        apply_phase_gate(qc, 1, coeff)
        print(f"  Current states: {monitor.get_current_states()}\n")
        monitor.step_counter += 1
    
    # INTELLIGENT RESTORATION - Only restore qubits that need it
    qc = monitor.analyze_and_restore(qc)
    
    print("="*70)
    return qc

def main():
    """Main function with intelligent monitoring"""
    func_input = input("Enter the Boolean function (use Xa, Xb, Xc as variables): ")
    
    # Generate coefficients
    print("\nGenerating Walsh-Hadamard coefficients...")
    coefficients = compute_standard_inner_product(func_input)
    
    # Display non-zero coefficients
    print("\nNon-zero coefficients:")
    for a, c in coefficients.items():
        if abs(c) > 1e-10:
            print(f"a = {a} → {c}")
    
    # Build circuit with intelligent monitoring
    quantum_circuit = build_quantum_circuit_with_intelligent_monitoring(coefficients)
    
    # Display results
    # print(f"\nFINAL CIRCUIT STATISTICS:")
    # print(f"Qubits: {quantum_circuit.num_qubits}")
    # print(f"Depth: {quantum_circuit.depth()}")
    # print(f"Gates: {quantum_circuit.count_ops()}")
    
    # print(f"\nCircuit Diagram:")
    print(quantum_circuit.draw(output='text'))
    
    return quantum_circuit

if __name__ == "__main__":
    circuit = main()
