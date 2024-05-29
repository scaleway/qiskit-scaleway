import os
import numpy as np
import random

from qiskit import transpile
from qiskit.circuit.library import IQP
from qiskit.quantum_info import random_hermitian

from qiskit_scaleway import ScalewayProvider
from qiskit_scaleway.primitives import Sampler as BackendSamplerV2


def test_sampler():
    provider = ScalewayProvider(
        project_id=os.environ["QISKIT_SCALEWAY_PROJECT_ID"],
        secret_key=os.environ["QISKIT_SCALEWAY_API_TOKEN"],
        url=os.environ["QISKIT_SCALEWAY_API_URL"],
    )

    backend = provider.get_backend("aer_simulation_pop_c16m128")

    assert backend is not None

    session_id = backend.start_session(
        name="my-sampler-session-autotest",
        deduplication_id=f"my-sampler-session-autotest-{random.randint(1, 1000)}",
        max_duration="5m",
    )

    assert session_id is not None

    try:
        sampler = BackendSamplerV2(backend=backend)

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
