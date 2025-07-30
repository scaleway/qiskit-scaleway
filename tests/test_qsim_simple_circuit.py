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


def test_qsim_simple_circuit():
    provider = ScalewayProvider(
        project_id=os.environ["QISKIT_SCALEWAY_PROJECT_ID"],
        secret_key=os.environ["QISKIT_SCALEWAY_SECRET_KEY"],
        url=os.environ["QISKIT_SCALEWAY_API_URL"],
    )

    backend = provider.get_backend("qsim_simulation_pop_c16m128")

    assert backend is not None

    session_id = backend.start_session(
        name="my-qsim-session-autotest",
        deduplication_id=f"my-qsim-session-autotest-{random.randint(1, 1000)}",
        max_duration="15m",
    )

    assert session_id is not None

    try:
        qc = QuantumCircuit(4)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(0, 2)
        qc.cx(0, 3)
        qc.measure_all()

        shots_count = 1000
        job = backend.run(qc, shots=shots_count, session_id=session_id)

        # cirq_result = job.result(format="cirq")

        # assert cirq_result is not None
        # assert cirq_result.repetitions == shots_count

        qiskit_result = job.result(format="qiskit")

        assert qiskit_result is not None
        assert qiskit_result.success
        assert qiskit_result.results[0].shots == shots_count

    finally:
        backend.delete_session(session_id)
