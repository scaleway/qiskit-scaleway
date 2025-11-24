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

from qiskit import QuantumCircuit
from qiskit_scaleway import ScalewayProvider

from qio.utils.circuit import random_square_qiskit_circuit


def test_aer_multiple_circuits():
    provider = ScalewayProvider(
        project_id=os.environ["QISKIT_SCALEWAY_PROJECT_ID"],
        secret_key=os.environ["QISKIT_SCALEWAY_SECRET_KEY"],
        url=os.getenv("QISKIT_SCALEWAY_API_URL"),
    )

    backend = provider.get_backend(
        os.getenv("QISKIT_SCALEWAY_BACKEND_NAME", "EMU-AER-16C-128M")
    )

    assert backend is not None

    session_id = backend.start_session(
        name="my-aer-session-autotest",
        deduplication_id=f"my-aer-session-autotest-{random.randint(1, 1000)}",
        max_duration="15m",
    )

    assert session_id is not None

    try:
        qc1 = random_square_qiskit_circuit(20)
        qc2 = random_square_qiskit_circuit(15)
        qc3 = random_square_qiskit_circuit(21)
        qc4 = random_square_qiskit_circuit(17)

        run_result = backend.run(
            [qc1, qc2, qc3, qc4],
            shots=1000,
            max_parallel_experiments=0,
            session_id=session_id,
        ).result()

        results = run_result.results

        assert len(results) == 4

        for result in results:
            assert result.success
    finally:
        backend.delete_session(session_id)


def _get_noise_model():
    import qiskit_aer.noise as noise

    # Error probabilities (exaggerated to get a noticeable effect for demonstration)
    prob_1 = 0.01  # 1-qubit gate
    prob_2 = 0.1  # 2-qubit gate

    # Depolarizing quantum errors
    error_1 = noise.depolarizing_error(prob_1, 1)
    error_2 = noise.depolarizing_error(prob_2, 2)

    # Add errors to noise model
    noise_model = noise.NoiseModel()
    noise_model.add_all_qubit_quantum_error(error_1, ["rz", "sx", "x"])
    noise_model.add_all_qubit_quantum_error(error_2, ["cx"])

    return noise_model


def _bell_state_circuit():
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return qc


def _simple_one_state_circuit():
    qc = QuantumCircuit(1, 1)
    qc.x(0)
    qc.measure_all()
    return qc


def test_aer_with_noise_model():
    provider = ScalewayProvider(
        project_id=os.environ["QISKIT_SCALEWAY_PROJECT_ID"],
        secret_key=os.environ["QISKIT_SCALEWAY_SECRET_KEY"],
        url=os.getenv("QISKIT_SCALEWAY_API_URL"),
    )

    backend = provider.get_backend(
        os.getenv("QISKIT_SCALEWAY_BACKEND_NAME", "EMU-AER-16C-128M")
    )

    assert backend is not None

    session_id = backend.start_session(
        name="my-aer-session-autotest",
        deduplication_id=f"my-aer-session-autotest-{random.randint(1, 1000)}",
        max_duration="15m",
    )

    assert session_id is not None

    try:
        qc1 = _bell_state_circuit()
        qc2 = _simple_one_state_circuit()

        run_ideal_result = backend.run(
            [qc1, qc2],
            shots=1000,
            max_parallel_experiments=0,
            session_id=session_id,
        ).result()

        run_noisy_result = backend.run(
            [qc1, qc2],
            shots=1000,
            max_parallel_experiments=0,
            session_id=session_id,
            noise_model=_get_noise_model(),
        ).result()

        ideal_results = run_ideal_result.results
        noisy_results = run_noisy_result.results

        assert len(ideal_results) == len(noisy_results) == 2

        for i, ideal_result in enumerate(ideal_results):
            assert len(ideal_result.data.counts) < len(noisy_results[i].data.counts)
    finally:
        backend.delete_session(session_id)
