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
import numpy as np
import random

from qiskit import QuantumCircuit
from qiskit_scaleway import ScalewayProvider


def _random_qiskit_circuit(size: int) -> QuantumCircuit:
    num_qubits = size
    num_gate = size

    qc = QuantumCircuit(num_qubits)

    for _ in range(num_gate):
        random_gate = np.random.choice(["unitary", "cx", "cy", "cz"])

        if random_gate == "cx" or random_gate == "cy" or random_gate == "cz":
            control_qubit = np.random.randint(0, num_qubits)
            target_qubit = np.random.randint(0, num_qubits)

            while target_qubit == control_qubit:
                target_qubit = np.random.randint(0, num_qubits)

            getattr(qc, random_gate)(control_qubit, target_qubit)
        else:
            for q in range(num_qubits):
                random_gate = np.random.choice(["h", "x", "y", "z"])
                getattr(qc, random_gate)(q)

    qc.measure_all()

    return qc


def test_aqt_multiple_circuits():
    provider = ScalewayProvider(
        project_id=os.environ["QISKIT_SCALEWAY_PROJECT_ID"],
        secret_key=os.environ["QISKIT_SCALEWAY_SECRET_KEY"],
        url=os.environ["QISKIT_SCALEWAY_API_URL"],
    )

    backend = provider.get_backend("aqt_ibex_simulation_pop_c16m128")

    assert backend is not None

    session_id = backend.start_session(
        name="my-aqt-session-autotest",
        deduplication_id=f"my-aqt-session-autotest-{random.randint(1, 1000)}",
        max_duration="15m",
    )

    assert session_id is not None

    try:
        qc1 = _random_qiskit_circuit(10)
        qc2 = _random_qiskit_circuit(12)
        qc3 = _random_qiskit_circuit(9)
        qc4 = _random_qiskit_circuit(10)

        run_result = backend.run(
            [qc1, qc2, qc3, qc4],
            shots=20,
            session_id=session_id,
        ).result()

        results = run_result.results

        assert len(results) == 4

        for result in results:
            assert result.success
    finally:
        backend.delete_session(session_id)
