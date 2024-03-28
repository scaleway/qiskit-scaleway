import qiskit

from qiskit import QuantumCircuit
from qiskit_scaleway_provider import ScalewayProvider
from qiskit_ibm_provider import IBMProvider

provider = ScalewayProvider(project_id="my-project", secret_key="my-secret")

print(provider.backends())
