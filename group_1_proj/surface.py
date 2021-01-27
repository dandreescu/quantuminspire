import os

import random
from functools import reduce

import numpy as np
from qiskit.quantum_info import Operator
from quantuminspire.credentials import load_account, get_token_authentication

from qiskit.circuit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit import execute, Aer

from quantuminspire.qiskit import QI

QI_EMAIL = os.getenv('QI_EMAIL')
QI_PASSWORD = os.getenv('QI_PASSWORD')
QI_URL = os.getenv('API_URL', 'https://api.quantum-inspire.com/')

QI.set_authentication(get_token_authentication(load_account()), QI_URL)
qi_backend = QI.get_backend('QX single-node simulator')


def generate_random_factors():
    e0 = random.random()
    e1 = random.random()
    e2 = random.random()
    e3 = random.random()

    norm = e0 ** 2 + e1 ** 2 + e2 ** 2 + e3 ** 2
    e0 /= norm
    e1 /= norm
    e2 /= norm
    e3 /= norm

    return e0, e1, e2, e3


def get_random_noise_matrix():
    e0, e1, e2, e3 = generate_random_factors()
    matrix = np.array([[e0 + e2, e1 - e3],
                       [e1 + e3, e0 - e2]])
    q, r = np.linalg.qr(matrix)
    return q.tolist()


def xxxx(circ, s, edges):   # stabilize a (2 or 4 qubit) x-face (https://arxiv.org/pdf/1208.0928.pdf fig 1.c)
    circ.h(s)
    if edges[0]:            # if the upper qubits exist
        circ.cx(s, edges[0])
        circ.cx(s, edges[1])
    if edges[2]:            # if the lower qubits exist
        circ.cx(s, edges[2])
        circ.cx(s, edges[3])
    circ.h(s)


def zzzz(circ, s, edges):   # stabilize a (2 or 4 qubit) z-face (https://arxiv.org/pdf/1208.0928.pdf fig 1.b)
    if edges[0]:            # if the left qubits exist
        circ.cx(edges[0], s)
        circ.cx(edges[2], s)
    if edges[1]:            # if the right qubits exist
        circ.cx(edges[1], s)
        circ.cx(edges[3], s)


def exec(circ):
    qi_probs = execute(circ, Aer.get_backend("qasm_simulator")
                       , shots=1).result().get_counts()
    return [int(token, 2) for token in list(qi_probs.keys())[0].split(' ')]


class SurfaceQubit:

    def __init__(self, d):
        assert d % 2 == 1
        self.round = 0
        self.d = d
        self.data = QuantumRegister(d ** 2, "data")
        self.syndrome = QuantumRegister(d ** 2 - 1, "syndrome")
        self.ancilla = QuantumRegister(1, "ancilla")
        self.measurement = ClassicalRegister(1, "measurement")
        self.circuit = QuantumCircuit(self.data, self.syndrome, self.ancilla, self.measurement)

    def stabilize(self):                # traverse all x and z faces and measure stabilizers
        readout = ClassicalRegister(self.d ** 2 - 1, f"readout{self.round}")
        self.round += 1
        self.circuit.add_register(readout)

        it = iter(self.syndrome)
        for i in range(self.d - 1):     # the (d-1)*(d-1) grid of square faces
            for j in range(self.d - 1):
                s = next(it)            # syndrome qubit
                ul = i * self.d + j     # upper-left data qubit index
                ur = ul + 1             # upper-right data qubit index
                ll = ul + self.d        # lower-left data qubit index
                lr = ll + 1             # upper-right data qubit index
                qubits = [self.data[k] for k in [ul, ur, ll, lr]]
                if (i + j) % 2 == 0:    # chessboard pattern
                    zzzz(self.circuit, s, qubits)
                else:
                    xxxx(self.circuit, s, qubits)

        for i in range(self.d // 2):    # the 4 edges * d/2 two-qubit stabilizers
            s = next(it)                # upper edge
            ll = 2 * i
            lr = ll + 1
            xxxx(self.circuit, s, [None, None, self.data[ll], self.data[lr]])

            s = next(it)                # right edge
            ul = 2 * i * self.d + self.d - 1
            ll = ul + self.d
            zzzz(self.circuit, s, [self.data[ul], None, self.data[ll], None])

            s = next(it)                # lower edge
            ur = self.d ** 2 - 1 - i
            ul = ur - 1
            xxxx(self.circuit, s, [self.data[ul], self.data[ur], None, None])

            s = next(it)                # left edge
            ur = 2 * i * self.d + self.d
            lr = ur + self.d
            zzzz(self.circuit, s, [None, self.data[ur], None, self.data[lr]])

        self.circuit.measure(self.syndrome, readout)
        self.circuit.reset(self.syndrome)
        self.circuit.barrier()

    def logical_z(self):
        for i in range(self.d):
            self.circuit.z(self.data[i])
        self.circuit.barrier()

    def logical_x(self):
        for i in range(self.d):
            self.circuit.x(self.data[i * self.d])
        self.circuit.barrier()

    def get_flips(self, syndrome):
        indices = [*range(0, self.d - 1, 2)]
        indices_lr = [(i + self.d) for i in indices]
        indices_ll = [(i + self.d - 2) if i else (self.d - 1) ** 2 + 3 for i in indices]

        parity_up = [syndrome & (1 << i) for i in indices]
        parity_lr = [syndrome & (1 << i) for i in indices_lr]
        parity_ll = [syndrome & (1 << i) for i in indices_ll]

        flips = sum(map(lambda u, lr, ll: u and not (ll or lr), parity_up, parity_lr, parity_ll))
        if syndrome & (1 << ((self.d - 1) ** 2 + 1)) and not syndrome & (1 << (2 * self.d - 3)):
            flips += 1
        return flips

    def measure_z(self):
        for i in range(self.d):
            self.circuit.cx(self.data[i], self.ancilla)
        self.circuit.measure(self.ancilla, self.measurement)
        self.circuit.reset(self.ancilla)
        self.circuit.barrier()

        result = exec(self.circuit)
        syndromes = [result[i] ^ result[i+1] for i in range(self.round - 1)]
        syndrome = reduce(lambda x, y: x ^ y, syndromes, 0)
        flips = self.get_flips(syndrome) + result[-1]

        return flips % 2

    def single_bitflip(self, i=-1):                       # only for data qubits (for now)
        q = self.data[i] if i > -1 else random.choice(self.data)
        self.circuit.x(q)

    def single_phaseflip(self, i=-1):                       # only for data qubits (for now)
        q = self.data[i] if i > -1 else random.choice(self.data)
        self.circuit.z(q)

    def single_err(self, i=-1):
        matrix = get_random_noise_matrix()
        err_op = Operator(matrix)
        q = self.data[i] if i > -1 else random.choice(self.data)
        self.circuit.unitary(err_op, q, label='error')


if __name__ == '__main__':

    d = 5
    for i in range(d ** 2):
        q = SurfaceQubit(d)
        q.stabilize()
        q.single_bitflip(i)
        q.stabilize()
        print(q.measure_z())


