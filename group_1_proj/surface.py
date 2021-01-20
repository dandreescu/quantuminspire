import os
import random
import numpy as np
import matplotlib.pyplot as plt

from qiskit.quantum_info import Operator
from quantuminspire.credentials import load_account, get_token_authentication

from qiskit.circuit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit import execute

from quantuminspire.qiskit import QI

QI_EMAIL = os.getenv('QI_EMAIL')
QI_PASSWORD = os.getenv('QI_PASSWORD')
QI_URL = os.getenv('API_URL', 'https://api.quantum-inspire.com/')


def xxxx(circ, s, edges):   # stabilize a (2 or 4 qubit) x-face (https://arxiv.org/pdf/1208.0928.pdf fig 1.c)
    circ.h(s)
    if edges[0]:            # if the upper qubits exist
        circ.cx(s, edges[1])
        circ.cx(s, edges[0])
    if edges[2]:            # if the lower qubits exist
        circ.cx(s, edges[3])
        circ.cx(s, edges[2])
    circ.h(s)


def zzzz(circ, s, edges):   # stabilize a (2 or 4 qubit) z-face (https://arxiv.org/pdf/1208.0928.pdf fig 1.b)
    if edges[0]:            # if the left qubits exist
        circ.cx(edges[0], s)
        circ.cx(edges[2], s)
    if edges[1]:            # if the right qubits exist
        circ.cx(edges[1], s)
        circ.cx(edges[3], s)


class SurfaceQubit:

    def __init__(self, d):
        assert d % 2 == 1
        self.d = d
        self.data = QuantumRegister(d ** 2, "data")
        self.syndrome = QuantumRegister(d ** 2 - 1, "syndrome")
        self.readout = ClassicalRegister(d ** 2 - 1, "readout")
        self.circuit = QuantumCircuit(self.data, self.syndrome, self.readout)

    def stabilize(self):                # traverse all x and z faces and measure stabilizers
        it = iter(self.syndrome)
        for i in range(self.d - 1):     # the (d-1)*(d-1) grid of square faces
            for j in range(self.d - 1):
                s = next(it)            # syndrome qubit
                ul = i * self.d + j     # upper-left data qubit index
                ur = ul + 1             # upper-right data qubit index
                ll = ul + self.d        # lower-left data qubit index
                lr = ll + 1             # upper-right data qubit index
                qubits = [self.data[k] for k in [ul, ur, ll, lr]]
                if i + j % 2 == 0:      # chessboard pattern
                    xxxx(self.circuit, s, qubits)
                else:
                    zzzz(self.circuit, s, qubits)

        for i in range(self.d // 2):    # the 4 edges * d/2 two-qubit stabilizers
            s = next(it)                # upper edge
            ll = 2 * i
            lr = ll + 1
            xxxx(self.circuit, s, [None, None, self.data[ll], self.data[lr]])

            s = next(it)                # lower edge
            ur = self.d ** 2 - 1 - i
            ul = ur - 1
            xxxx(self.circuit, s, [self.data[ul], self.data[ur], None, None])

            s = next(it)                # right edge
            ul = 2 * i * self.d + self.d - 1
            ll = ul + self.d
            zzzz(self.circuit, s, [self.data[ul], None, self.data[ll], None])

            s = next(it)                # left edge
            ur = 2 * i * self.d + self.d
            lr = ul + self.d
            zzzz(self.circuit, s, [None, self.data[ur], None, self.data[lr]])

        self.circuit.measure(self.syndrome, self.readout)

if __name__ == '__main__':

    QI.set_authentication(get_token_authentication(load_account()), QI_URL)
    qi_backend = QI.get_backend('QX single-node simulator')

    q = SurfaceQubit(7)
    q.stabilize()
    # todo: apply some error(s) between stabilize() calls
    q.stabilize()

    # qi_job = execute(circuit, backend=qi_backend, shots=1)
    # qi_result = qi_job.result()
    # probabilities_histogram = qi_result.get_probabilities(circuit)
