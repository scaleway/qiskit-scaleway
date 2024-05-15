from typing import Union, List

from qiskit.providers import Options
from qiskit.circuit import QuantumCircuit

from .scaleway_backend import ScalewayBackend
from ..utils import QaaSClient


class QuandelaBackend(ScalewayBackend):
    def __init__(
        self,
        provider,
        client: QaaSClient,
        backend_id: str,
        name: str,
        availability: str,
        version: str,
        num_qubits: int,
        metadata: str,
    ):
        super().__init__(
            provider=provider,
            client=client,
            backend_id=backend_id,
            name=name,
            availability=availability,
            version=version,
        )

        self._num_qubits = num_qubits
        self._options = self._default_options()

    def __repr__(self) -> str:
        return f"<QuandelaBackend(name={self.name},num_qubits={self.num_qubits},platform_id={self.id})>"

    @property
    def target(self):
        return None

    @property
    def num_qubits(self) -> int:
        return self._num_qubits

    @property
    def max_circuits(self):
        return 1

    def run(
        self, circuits: Union[QuantumCircuit, List[QuantumCircuit]], **run_options
    ) -> None:
        pass

    @classmethod
    def _default_options(self):
        return Options(
            session_id="auto",
            session_name="quandela-session-from-qiskit",
            session_deduplication_id="quandela-session-from-qiskit",
            session_max_duration="20m",
            session_max_idle_duration="20m",
        )
