import qiskit

from qiskit import QuantumCircuit
from qiskit_scaleway import ScalewayProvider

provider = ScalewayProvider(project_id="ae84de1f-c006-4383-8f92-8cc7f76bc07d", secret_key="6af5f1ab-cb28-4bc3-b297-9a95d4ac7c65", url="https://agw.stg.fr-par-2.internal.scaleway.com/qaas/v1alpha1")

# The backends() method lists all available computing backends. Printing it
# renders it as a table that shows each backend's containing workspace.
print(provider.backends())

# Retrieve a backend by providing search criteria. The search must have a single match
# Create or fetch an existing Scaleway session, the session argument use the deduplication_id
backend = provider.get_backend("aer_simulation_h100", session="test-qiskit-8")

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

# if result.success:
#     print(result.get_counts())
# else:
#     print(result.to_dict()["error"])




# import qiskit

# from qiskit import QuantumCircuit
# from qiskit_scaleway import ScalewayProvider
# from qiskit_ibm_provider import IBMProvider

# provider = ScalewayProvider(project_id="my-project", secret_key="61b3f347-06a5-4d18-a0f3-184a7d7f65a3", url="https://agw.stg.fr-par-2.internal.scaleway.com/qaas/v1alpha1")

# # IBMProvider.save_account(token="435635a8d28e76c8f039982c39ad3812d9fae930c0fbf20619a7d1758b5adbc90dc5ef6973256530bd9a59e990c16d45c70b2b6553249e609ca27f9f397a979b")
# # provider = IBMProvider()
# # provider_name scaleway
# backends = provider.backends()

# # print(backends)

# for b in backends:
#   print(b.name)

# # backends = provider.backends(name=)

# # print(backends)

# # print(provider.get_backend("simulator_mps"))
# # print(provider.get_backend("simulator_mps"))
