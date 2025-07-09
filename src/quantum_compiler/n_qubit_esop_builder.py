import re
import sys
import os
from qiskit import QuantumCircuit
from qiskit.circuit import Instruction

# Import your existing 3-qubit program
try:
    from quantumcircuit import (
        compute_standard_inner_product, 
        build_quantum_circuit_with_intelligent_monitoring,
        extract_qiskit_circuit_info,
        qiskit_to_qc_format
    )
    print(" Successfully imported quantumcircuit.py")
except ImportError as e:
    print(f" Error importing quantumcircuit.py: {e}")
    print("Make sure quantumcircuit.py is in the same directory")
    sys.exit(1)

class NQubitESOPBuilder:
    """Build n-qubit quantum circuits from ESOP expressions using existing 3-qubit compiler"""
    def build_circuit_programmatically(self, esop_expr):
        """Programmatic interface - builds circuit and returns Qiskit QuantumCircuit No interactive input required"""
        print(f" Building circuit programmatically for: {esop_expr}")

        try:
            # Build the complete circuit
            circuit = self.build_complete_circuit(esop_expr)

            if circuit is not None:
                print(f" Successfully built {circuit.num_qubits}-qubit circuit with {len(circuit.data)} gates")
                return circuit
            else:
                print(" Failed to build circuit")
                return None

        except Exception as e:
            print(f" Error building circuit programmatically: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def __init__(self):
        self.total_qubits = 0
        self.variables = []
        self.variable_to_qubit = {}
        self.qubit_to_variable = {}
        self.terms = []
        self.final_circuit = None
        self.term_circuits = []
        self.qc_content = None
        
    def parse_esop_expression(self, esop_expr):
        """Parse ESOP expression and extract terms and variables"""
        print(f"Parsing ESOP expression: {esop_expr}")
        
        # Clean the expression
        esop_expr = esop_expr.replace(" ", "").replace("(", "").replace(")", "")
        
        # Split by XOR operators
        terms = re.split(r'[\^⊕]', esop_expr)
        
        # Extract variables from each term
        self.terms = []
        all_variables = set()
        
        for term in terms:
            if term.strip():
                # Find all variables in this term (X followed by alphanumeric)
                variables_in_term = re.findall(r'X[a-zA-Z0-9]+', term.upper())
                if variables_in_term:
                    self.terms.append(variables_in_term)
                    all_variables.update(variables_in_term)
        
        # Create sorted variable list and mappings
        self.variables = sorted(list(all_variables))
        self.total_qubits = len(self.variables)
        
        # Create bidirectional mappings
        self.variable_to_qubit = {var: i for i, var in enumerate(self.variables)}
        self.qubit_to_variable = {i: var for i, var in enumerate(self.variables)}
        
        print(f" Found {self.total_qubits} qubits: {self.variables}")
        print(f" Terms: {self.terms}")
        print(f"  Variable mapping: {self.variable_to_qubit}")
        
        return self.terms, self.variables
    
    def get_extended_program_variables(self, num_vars):
        """Get extended program variable names beyond Xa, Xb, Xc"""
        # Extended alphabet mapping: X1->Xa, X2->Xb, X3->Xc, X4->Xd, X5->Xe, etc.
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        program_vars = []
        
        for i in range(num_vars):
            if i < len(alphabet):
                program_vars.append(f"X{alphabet[i]}")
            else:
                # For more than 26 variables, use double letters
                first_letter = alphabet[(i // 26) - 1]
                second_letter = alphabet[i % 26]
                program_vars.append(f"X{first_letter}{second_letter}")
        
        return program_vars
    
    def map_term_to_extended_format(self, term_variables):
        """Map ESOP term variables to extended program format (Xa, Xb, Xc, Xd, Xe, ...)"""
        program_vars = self.get_extended_program_variables(len(term_variables))
        
        if len(term_variables) > 26:
            print(f"  Warning: Term has {len(term_variables)} variables, which exceeds typical limits")
        
        # Create mapping from original variables to program variables
        var_mapping = {}
        for i, var in enumerate(term_variables):
            if i < len(program_vars):
                var_mapping[var] = program_vars[i]
        
        print(f" Variable mapping for this term: {var_mapping}")
        return var_mapping
    
    def create_boolean_expression_for_term(self, term_variables):
        """Create boolean expression for the extended program format"""
        var_mapping = self.map_term_to_extended_format(term_variables)
        
        if len(term_variables) == 1:
            return var_mapping[term_variables[0]]
        elif len(term_variables) == 2:
            return f"{var_mapping[term_variables[0]]}*{var_mapping[term_variables[1]]}"
        elif len(term_variables) == 3:
            return f"{var_mapping[term_variables[0]]}*{var_mapping[term_variables[1]]}*{var_mapping[term_variables[2]]}"
        elif len(term_variables) == 4:
            return f"{var_mapping[term_variables[0]]}*{var_mapping[term_variables[1]]}*{var_mapping[term_variables[2]]}*{var_mapping[term_variables[3]]}"
        elif len(term_variables) == 5:
            return f"{var_mapping[term_variables[0]]}*{var_mapping[term_variables[1]]}*{var_mapping[term_variables[2]]}*{var_mapping[term_variables[3]]}*{var_mapping[term_variables[4]]}"
        else:
            # For more than 5 variables, create a general expression
            mapped_vars = [var_mapping[var] for var in term_variables]
            return "*".join(mapped_vars)
    
    def generate_circuit_for_term(self, term_variables, term_index):
        """Generate quantum circuit for a single term using existing 3-qubit program"""
        print(f"\n Processing term {term_index + 1}: {' * '.join(term_variables)}")
        
        # Create boolean expression for extended program format
        bool_expr = self.create_boolean_expression_for_term(term_variables)
        if bool_expr is None:
            return None, None
        
        print(f"   Mapped to: {bool_expr}")
        
        try:
            # Use your existing 3-qubit program
            # Note: This will only work for terms with ≤3 variables due to your existing program's limitation
            if len(term_variables) > 3:
                print(f"    Warning: Term has {len(term_variables)} variables, but existing program supports max 3")
                print(f"   Taking first 3 variables: {term_variables[:3]}")
                term_variables = term_variables[:3]
                bool_expr = self.create_boolean_expression_for_term(term_variables)
                print(f"   Reduced expression: {bool_expr}")
            
            coefficients = compute_standard_inner_product(bool_expr)
            small_circuit, monitor = build_quantum_circuit_with_intelligent_monitoring(coefficients)
            
            print(f" Generated {small_circuit.num_qubits}-qubit circuit with {len(small_circuit.data)} gates")
            
            # Create qubit mapping from small circuit to large circuit
            qubit_mapping = {}
            for i, var in enumerate(term_variables):
                if i < small_circuit.num_qubits:
                    large_circuit_qubit = self.variable_to_qubit[var]
                    qubit_mapping[i] = large_circuit_qubit
            
            print(f"    Qubit mapping to large circuit: {qubit_mapping}")
            return small_circuit, qubit_mapping
            
        except Exception as e:
            print(f"   Error generating circuit: {e}")
            import traceback
            traceback.print_exc()
            return None, None
   
    def place_circuit_in_large_circuit(self, large_circuit, small_circuit, qubit_mapping):
        """Place small circuit gates in the correct positions of large circuit"""
        print(f"    Placing circuit: {qubit_mapping}")
        
        gates_added = 0
        for instruction, qargs, cargs in small_circuit.data:
            # Map small circuit qubit indices to large circuit qubit indices
            try:
                mapped_qargs = []
                for qarg in qargs:
                    small_qubit_index = small_circuit.qubits.index(qarg)
                    large_qubit_index = qubit_mapping[small_qubit_index]
                    mapped_qargs.append(large_circuit.qubits[large_qubit_index])
                
                # Add the gate to large circuit
                large_circuit.append(instruction, mapped_qargs, cargs)
                gates_added += 1
                print(f"      Placed {instruction.name} gate on qubits {[large_circuit.qubits.index(q) for q in mapped_qargs]} (variables: {[self.qubit_to_variable[large_circuit.qubits.index(q)] for q in mapped_qargs]})")
                
            except Exception as e:
                print(f"     Error placing gate {instruction.name}: {e}")
        
        print(f"    Placed {gates_added} gates")
        return gates_added
    
    def generate_qc_format(self):
        """Generate QC format from the final circuit"""
        if self.final_circuit is None:
            print(" No circuit to convert to QC format!")
            return None
        
        try:
            qubit_names, gate_sequence = extract_qiskit_circuit_info(self.final_circuit)
            self.qc_content = qiskit_to_qc_format(qubit_names, gate_sequence)
            return self.qc_content
        except Exception as e:
            print(f" Error generating QC format: {e}")
            return None
    
    def show_qc_format(self):
        """Display the QC format of the circuit"""
        if self.qc_content is None:
            self.generate_qc_format()
        
        if self.qc_content:
            print(f"\n{'='*60}")
            print(f" QC FORMAT")
            print(f"{'='*60}")
            print(self.qc_content)
        else:
            print(" No QC format available!")
    
    def build_complete_circuit(self, esop_expr):
        """Build complete n-qubit circuit from ESOP expression"""
        print(f"\n{'='*60}")
        print(f" BUILDING N-QUBIT ESOP CIRCUIT")
        print(f"{'='*60}")
        
        # Parse the expression
        terms, variables = self.parse_esop_expression(esop_expr)
        
        # Create the large quantum circuit
        self.final_circuit = QuantumCircuit(self.total_qubits)
        print(f"\n  Created {self.total_qubits}-qubit quantum circuit")
        
        # Show variable to qubit mapping
        print(f"\n  Global Variable to Qubit Mapping:")
        for var, qubit in self.variable_to_qubit.items():
            extended_var = self.get_extended_program_variables(qubit + 1)[qubit]
            print(f"    {var} → Qubit {qubit} → Program Variable {extended_var}")
        
        # Process each term
        total_gates_added = 0
        successful_terms = 0
        
        for i, term in enumerate(terms):
            print(f"\n{'─'*40}")
            print(f"Term {i+1}/{len(terms)}: {' * '.join(term)}")
            
            # Generate small circuit for this term
            small_circuit, qubit_mapping = self.generate_circuit_for_term(term, i)
            
            if small_circuit is not None and qubit_mapping is not None:
                # Place the small circuit in the large circuit
                gates_added = self.place_circuit_in_large_circuit(
                    self.final_circuit, small_circuit, qubit_mapping
                )
                total_gates_added += gates_added
                successful_terms += 1
                
                # Store for analysis
                self.term_circuits.append({
                    'term': term,
                    'circuit': small_circuit,
                    'mapping': qubit_mapping,
                    'gates': gates_added
                })
            else:
                print(f"    Failed to process term {i+1}")
        
        print(f"\n{'='*60}")
        print(f" CIRCUIT BUILDING COMPLETE")
        print(f"{'='*60}")
        print(f" Successfully processed: {successful_terms}/{len(terms)} terms")
        print(f" Total gates added: {total_gates_added}")
        print(f" Final circuit depth: {self.final_circuit.depth()}")
        print(f" Final circuit size: {self.total_qubits} qubits, {len(self.final_circuit.data)} gates")
        
        # Automatically generate QC format
        self.generate_qc_format()
        print(f"\n QC format generated automatically!")
        
        return self.final_circuit
    
    def show_circuit_analysis(self):
        """Show detailed analysis of the built circuit"""
        if self.final_circuit is None:
            print(" No circuit built yet!")
            return
        
        print(f"\n{'='*60}")
        print(f" CIRCUIT ANALYSIS")
        print(f"{'='*60}")
        
        print(f" Total Qubits: {self.total_qubits}")
        print(f" Variables: {', '.join(self.variables)}")
        print(f" Total Gates: {len(self.final_circuit.data)}")
        print(f" Circuit Depth: {self.final_circuit.depth()}")
        
        # Gate type analysis
        gate_counts = {}
        for instruction, qargs, cargs in self.final_circuit.data:
            gate_name = instruction.name
            gate_counts[gate_name] = gate_counts.get(gate_name, 0) + 1
        
        print(f"\n Gate Type Breakdown:")
        for gate_type, count in gate_counts.items():
            print(f"    {gate_type}: {count}")
        
        print(f"\n Term-by-Term Breakdown:")
        for i, term_info in enumerate(self.term_circuits):
            term = term_info['term']
            mapping = term_info['mapping']
            gates = term_info['gates']
            
            print(f"  Term {i+1}: {' * '.join(term)}")
            print(f"    Qubit mapping: {mapping}")
            print(f"    Variable mapping: {[self.qubit_to_variable[q] for q in mapping.values()]}")
            print(f"    Gates added: {gates}")
        
        print(f"\n  Variable to Qubit Mapping:")
        for var, qubit in self.variable_to_qubit.items():
            extended_var = self.get_extended_program_variables(qubit + 1)[qubit]
            print(f"    {var} → Qubit {qubit} → Program Variable {extended_var}")
        
        # Show detailed gate list
        print(f"\n Detailed Gate List:")
        for i, (instruction, qargs, cargs) in enumerate(self.final_circuit.data):
            qubit_indices = [self.final_circuit.qubits.index(q) for q in qargs]
            variable_names = [self.qubit_to_variable[idx] for idx in qubit_indices]
            print(f"  Gate {i+1}: {instruction.name} on qubit(s) {qubit_indices} (variables: {variable_names})")
    
    def save_circuit(self, filename=None):
        """Save the circuit to .qc format"""
        if self.final_circuit is None:
            print(" No circuit to save!")
            return
        
        if filename is None:
            filename = f"esop_{self.total_qubits}qubit_circuit.qc"
        
        try:
            if self.qc_content is None:
                self.generate_qc_format()
            
            with open(filename, 'w') as f:
                f.write(self.qc_content)
            
            print(f" Circuit saved to: {filename}")
            return self.qc_content
            
        except Exception as e:
            print(f" Error saving circuit: {e}")
            return None

def interactive_mode():
    """Interactive mode for building ESOP circuits"""
    builder = NQubitESOPBuilder()
    
    print(" N-Qubit ESOP Quantum Circuit Builder")
    print("Uses your existing 3-qubit quantumcircuit.py program")
    print(" Extended variable mapping: X1→Xa, X2→Xb, X3→Xc, X4→Xd, X5→Xe, ...")
    print(" Automatic QC format generation")
    print("="*60)
    
    while True:
        print("\n Options:")
        print("1. Build circuit from ESOP expression")
        print("2. Show circuit diagram")
        print("3. Show detailed circuit analysis")
        print("4. Show QC format")
        print("5. Save circuit to .qc file")
        print("6. Start new circuit")
        print("7. Exit")
        
        choice = input("\nChoose option (1-7): ").strip()
        
        if choice == "1":
            esop_expr = input("Enter ESOP expression (e.g., 'X1*X2 ^ X2*X3 ^ X3*X4 ^ X4*X5 ^ X5*X1'): ")
            try:
                circuit = builder.build_complete_circuit(esop_expr)
                if circuit:
                    print("\n Circuit built successfully!")
                    print(" QC format is ready! Use option 4 to view it.")
                else:
                    print(" Failed to build circuit")
            except Exception as e:
                print(f" Error: {e}")
                import traceback
                traceback.print_exc()
        
        elif choice == "2":
            if builder.final_circuit:
                print("\n Circuit Diagram:")
                print(builder.final_circuit.draw(output='text'))
            else:
                print(" No circuit built yet!")
        
        elif choice == "3":
            builder.show_circuit_analysis()
        
        elif choice == "4":
            builder.show_qc_format()
        
        elif choice == "5":
            filename = input("Enter filename (press Enter for default): ").strip()
            if not filename:
                filename = None
            result = builder.save_circuit(filename)
            if result:
                print(" Circuit saved successfully!")
        
        elif choice == "6":
            builder = NQubitESOPBuilder()
            print(" Started new circuit builder")
        
        elif choice == "7":
            print(" Goodbye!")
            break
        
        else:
            print(" Invalid choice!")

def quick_build(esop_expr):
    """Quick function to build circuit from ESOP expression"""
    builder = NQubitESOPBuilder()
    circuit = builder.build_complete_circuit(esop_expr)
    return circuit, builder.qc_content

def example_usage():
    """Show example usage"""
    print(" Example: Building circuit for 'X1*X2 ^ X2*X3 ^ X3*X4 ^ X4*X5 ^ X5*X1'")
    
    esop_expr = "X1*X2 ^ X2*X3 ^ X3*X4 ^ X4*X5 ^ X5*X1"
    circuit, qc_content = quick_build(esop_expr)
    
    if circuit:
        print("\n Final Circuit:")
        print(circuit.draw(output='text'))
        
        print(f"\n Circuit Statistics:")
        print(f"   Qubits: {circuit.num_qubits}")
        print(f"   Gates: {len(circuit.data)}")
        print(f"   Depth: {circuit.depth()}")
        
        print(f"\n QC Format:")
        print("="*40)
        print(qc_content)
        print("="*40)
        
        return circuit
    else:
        print(" Failed to build example circuit")
        return None


def build_esop_circuit(esop_expr):
    """
    Standalone function to build ESOP circuit - easy to import and use
    """
    builder = NQubitESOPBuilder()
    return builder.build_complete_circuit(esop_expr)