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
import os
import random

from scipy.optimize import minimize

from qiskit import QuantumCircuit
from qiskit.quantum_info.operators.base_operator import BaseOperator
from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import TwoLocal

from qiskit_scaleway import ScalewayProvider
from qiskit_scaleway.primitives import Estimator


def test_estimator():
    provider = ScalewayProvider(
        project_id=os.environ["QISKIT_SCALEWAY_PROJECT_ID"],
        secret_key=os.environ["QISKIT_SCALEWAY_SECRET_KEY"],
        url=os.environ["QISKIT_SCALEWAY_API_URL"],
    )

    backend = provider.get_backend("aer_simulation_pop_c16m128")

    assert backend is not None

    session_id = backend.start_session(
        name="my-estimator-session-autotest",
        deduplication_id=f"my-estimator-session-autotest-{random.randint(1, 1000)}",
        max_duration="15m",
    )

    assert session_id is not None

    try:
        # Buildup the estimator for the VQE
        estimator = Estimator(backend=backend, session_id=session_id)

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
        ansatz = TwoLocal(num_qubits=2, rotation_blocks="ry", entanglement_blocks="cz")
        initial_point = [0] * 8

        def cost_function(
            params,
            ansatz: QuantumCircuit,
            hamiltonian: BaseOperator,
            estimator: Estimator,
        ) -> float:
            """Cost function for the VQE.

            Return the estimated expectation value of the Hamiltonian
            on the state prepared by the Ansatz circuit.
            """
            result = estimator.run([(ansatz, hamiltonian, params)]).result()

            loss = float(result[0].data["evs"])

            print(f"> loss {loss}")

            return loss

        # Run the VQE using the SciPy minimizer routine
        result = minimize(
            cost_function,
            initial_point,
            args=(ansatz, hamiltonian, estimator),
            method="cobyla",
        )

        assert result is not None
        assert result.fun is not None

        # Print the found minimum eigenvalue
        print(f"> {result.fun}")
    finally:
        backend.stop_session(session_id)
