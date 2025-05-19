from qiskit import *

def build_qc(qc_args):
    qr_out = QuantumRegister(3)
    p_out  = QuantumRegister(4,'p')
    qc_out = QuantumCircuit(qr_out,p_out)
    qc_out.ccz(qr_out[0],qr_out[1],qr_out[2])
    return qc_out
                     



