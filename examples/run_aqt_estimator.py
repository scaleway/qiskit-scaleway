# Copyright 2025 Scaleway
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from scipy.optimize import minimize

from qiskit import QuantumCircuit
from qiskit.quantum_info.operators.base_operator import BaseOperator
from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import n_local

from qiskit_scaleway import ScalewayProvider
from qiskit_scaleway.primitives import EstimatorV1

provider = ScalewayProvider(
    project_id="<your-scaleway-project-id>",
    secret_key="<your-scaleway-secret-key>",
)

# Scaleway provides Alpine Quantum Technologies (AQT) ion-trapped backend, whichs is compatible with Qiskit SDK
backend = provider.get_backend("aqt_ibex_simulation_l4")

# Start the session
session_id = backend.start_session(name="test-session", deduplication_id="my-workshop")

# Create an estimator (v1) with the backend and the session
estimator = EstimatorV1(backend=backend, session_id=session_id)

# Specify the problem Hamiltonian
hamiltonian = SparsePauliOp.from_list(
    [
        ("II", -1.052373245772859),
        ("IZ", 0.39793742484318045),
        ("ZI", -0.39793742484318045),
        ("ZZ", -0.01128010425623538),
        ("XX", 0.18093119978423156),
    ]
)

# Define the VQE Ansatz, initial point, and cost function
circuit = n_local(num_qubits=2, rotation_blocks="ry", entanglement_blocks="cz")

initial_point = [0] * 8


def cost_function(
    params,
    ansatz: QuantumCircuit,
    hamiltonian: BaseOperator,
    estimator: EstimatorV1,
) -> float:
    """Cost function for the VQE.

    Return the estimated expectation value of the Hamiltonian
    on the state prepared by the Ansatz circuit.
    """
    return float(
        estimator.run(ansatz, hamiltonian, parameter_values=params).result().values[0]
    )


# Run the VQE using the SciPy minimizer routine
result = minimize(
    cost_function,
    initial_point,
    args=(circuit, hamiltonian, estimator),
    method="cobyla",
)

# Print the found minimum eigenvalue
print(f"> {result.fun}")

# Revoke manually the QPU's session if needed
backend.stop_session(session_id)
