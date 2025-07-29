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

from qiskit import transpile
from qiskit.circuit.library import IQP
from qiskit.quantum_info import random_hermitian

from qiskit_scaleway import ScalewayProvider
from qiskit_scaleway.primitives import Sampler


def test_sampler():
    provider = ScalewayProvider(
        project_id=os.environ["QISKIT_SCALEWAY_PROJECT_ID"],
        secret_key=os.environ["QISKIT_SCALEWAY_SECRET_KEY"],
        url=os.environ["QISKIT_SCALEWAY_API_URL"],
    )

    backend = provider.get_backend("aer_simulation_pop_c16m128")

    assert backend is not None

    session_id = backend.start_session(
        name="my-sampler-session-autotest",
        deduplication_id=f"my-sampler-session-autotest-{random.randint(1, 1000)}",
        max_duration="15m",
    )

    assert session_id is not None

    try:
        sampler = Sampler(backend=backend, session_id=session_id)

        n_qubits = 10
        mat = np.real(random_hermitian(n_qubits, seed=1234))
        circuit = IQP(mat)
        circuit.measure_all()

        isa_circuit = transpile(circuit, backend=backend, optimization_level=1)
        job = sampler.run([isa_circuit], shots=100)
        result = job.result()

        assert result is not None
    finally:
        backend.stop_session(session_id)
