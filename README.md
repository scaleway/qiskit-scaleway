# Scaleway provider for Qiskit

**Qiskit Scaleway** is a Python package to run quantum circuits on [Scaleway](https://www.scaleway.com/en/) infrastructure, providing access to [Aer](https://github.com/Qiskit/qiskit-aer) and [Qsim](https://github.com/quantumlib/qsim) simulators on powerful hardware (CPU and GPU).

More info on the [Quantum service web page](https://labs.scaleway.com/en/qaas/).

## Installation

We encourage installing Scaleway provider via the pip tool (a python package manager):

```bash
pip install qiskit-scaleway
```

## Usage
```python
from qiskit import QuantumCircuit
from qiskit_scaleway import ScalewayProvider

provider = ScalewayProvider(
    project_id="<your-scaleway-project-id>",
    secret_key="<your-scaleway-secret-key>",
)

# Retrieve a backend by providing search criteria. The search must have a single match
backend = provider.get_backend("aer_simulation_h100")

# Define a quantum circuit that produces a 4-qubit GHZ state.
qc = QuantumCircuit(4)
qc.h(0)
qc.cx(0, 1)
qc.cx(0, 2)
qc.cx(0, 3)
qc.measure_all()

# Create and send a job to a new QPU's session (or on an existing one)
result = backend.run(qc, shots=1000).result()

if result.success:
    print(result.get_counts())
else:
    print(result.to_dict()["error"])

```

## Contribute
TODO

## Licence
[License Apache 2.0](LICENCE)