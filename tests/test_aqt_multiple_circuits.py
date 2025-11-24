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

from qiskit_scaleway import ScalewayProvider

from qio.utils.circuit import random_square_qiskit_circuit


def test_aqt_multiple_circuits():
    provider = ScalewayProvider(
        project_id=os.environ["QISKIT_SCALEWAY_PROJECT_ID"],
        secret_key=os.environ["QISKIT_SCALEWAY_SECRET_KEY"],
        url=os.getenv("QISKIT_SCALEWAY_API_URL"),
    )

    backend = provider.get_backend("EMU-IBEX-12PQ-16C-128M")

    assert backend is not None

    session_id = backend.start_session(
        name="my-aqt-session-autotest",
        deduplication_id=f"my-aqt-session-autotest-{random.randint(1, 1000)}",
        max_duration="15m",
    )

    assert session_id is not None

    try:
        qc1 = random_square_qiskit_circuit(10)
        qc2 = random_square_qiskit_circuit(12)
        qc3 = random_square_qiskit_circuit(9)
        qc4 = random_square_qiskit_circuit(10)

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
