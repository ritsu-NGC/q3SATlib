from qiskit import QuantumCircuit
from qiskit.circuit.library import PhaseOracle
from qiskit_aer import Aer, AerSimulator

from quantumcircuit import *

func = "xa | xb | xc"
oracle = PhaseOracle(func)
oracle.save_unitary()

simulator = Aer.get_backend('aer_simulator')
# Another option to create the simulator
# simulator = AerSimulator(method = 'unitary')
#circ = transpile(oracle, simulator)
circ = oracle

# Run and get unitary
result = simulator.run(circ).result()
unitary = result.get_unitary(circ)
print(unitary)
print(oracle.draw(output='text'))

act_qc = main(func)
act_qc.save_unitary()
result = simulator.run(act_qc).result()
unitary = result.get_unitary(act_qc)
print(unitary)
print(act_qc.draw(output='text'))
