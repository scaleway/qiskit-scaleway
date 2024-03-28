import qiskit

from qiskit import QuantumCircuit
from qiskit_scaleway import ScalewayProvider

provider = ScalewayProvider(project_id="<project_id>", secret_key="<secret_key>", url="https://agw.stg.fr-par-2.internal.scaleway.com/qaas/v1alpha1")

# The backends() method lists all available computing backends. Printing it
# renders it as a table that shows each backend's containing workspace.
print(provider.backends())

# Retrieve a backend by providing search criteria. The search must have a single match
# Create or fetch an existing Scaleway session, the session argument use the deduplication_id
backend = provider.get_backend("aer_simulation_h100", session="test-qiskit-12")

# Define a quantum circuit that produces a 4-qubit GHZ state.
qc = QuantumCircuit(4)
qc.h(0)
qc.cx(0, 1)
qc.cx(0, 2)
qc.cx(0, 3)
qc.measure_all()

# # Transpile for the target backend
# # useless for now, could return the same circuit ( later could be useful for Perceval to Qiskit)
qc = qiskit.transpile(qc, backend)

# Execute on the target backend
# Send job in QASM format
# Every params from backend + job are send to the session
result = backend.run(qc, shots=1).result()

# TODO
# if result.success:
#     print(result.get_counts())
# else:
#     print(result.to_dict()["error"])


