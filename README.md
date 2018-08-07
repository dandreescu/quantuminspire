# Quantum Inspire SDK

The software development kit for the Quantum Inspire platform. The SDK consists of

* An API for the Quantum Inspire online platform `QuantumInspireAPI`
* Backends for various other SDKs. These are the IMB Q backend, ...

For more information see https://www.quantum-inspire.com/

For example usage see the Jupyter notebooks in the [docs](docs/) directory.

``` python
from getpass import getpass
from requests.auth import HTTPBasicAuth
from quantuminspire import QuantumInspireAPI

if 'password' not in vars().keys():
    print('Enter username')
    username = input()
    print('Enter password')
    password = getpass()

auth = HTTPBasicAuth(username, password)
qi = QuantumInspireAPI(server=r'https://api.quantum-inspire.com/', auth=auth)  
backend_types=qi.list_backend_types()

qasm='''version 1.0

qubits 2

H q[0] 
CNOT q[0], q[1] 
display 
measure q[0]
'''

r=qi.execute_qasm(qasm, backend_types[0], nshots=128)
```
