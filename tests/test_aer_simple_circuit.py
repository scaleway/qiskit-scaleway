import os
import random

from qiskit import QuantumCircuit
from qiskit_scaleway import ScalewayProvider


def test_aer_simple_circuit():
    provider = ScalewayProvider(
        project_id=os.environ["QISKIT_SCALEWAY_PROJECT_ID"],
        secret_key=os.environ["QISKIT_SCALEWAY_API_TOKEN"],
        url=os.environ["QISKIT_SCALEWAY_API_URL"],
    )

    backend = provider.get_backend("aer_simulation_pop_c16m128")

    assert backend is not None

    session_id = backend.start_session(
        name="my-aer-session-autotest",
        deduplication_id=f"my-aer-session-autotest-{random.randint(1, 1000)}",
        max_duration="5m",
    )

    assert session_id is not None

    try:
        qc = QuantumCircuit(4)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(0, 2)
        qc.cx(0, 3)
        qc.measure_all()

        # Create and send a job to the target session
        result = backend.run(qc, shots=1000, session_id=session_id).result()

        assert result is not None
        assert result.success
    finally:
        backend.stop_session(session_id)
