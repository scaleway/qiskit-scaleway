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


def test_aer_multiple_circuits():
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
        qc1 = _random_qiskit_circuit(20)
        qc2 = _random_qiskit_circuit(15)
        qc3 = _random_qiskit_circuit(21)
        qc4 = _random_qiskit_circuit(17)

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
        backend.stop_session(session_id)
