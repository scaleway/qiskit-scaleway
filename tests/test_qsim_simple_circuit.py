import os

from qiskit import QuantumCircuit
from qiskit_scaleway import ScalewayProvider


def test_qsim_simple_circuit():
    provider = ScalewayProvider(
        project_id=os.environ["QISKIT_SCALEWAY_PROJECT_ID"],
        secret_key=os.environ["QISKIT_SCALEWAY_API_TOKEN"],
        url=os.environ["QISKIT_SCALEWAY_API_URL"],
    )

    backend = provider.get_backend("qsim_simulation_pop_c16m128")

    assert backend is not None

    session_id = backend.start_session(
        name="my-qsim-session-autotest",
        deduplication_id="my-qsim-session-autotest",
        max_duration="2m",
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
