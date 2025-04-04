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
import randomname
import warnings

from typing import Union, List, TypeVar

from qiskit.circuit import QuantumCircuit
from qiskit.circuit.parameter import Parameter
from qiskit.circuit.library import RXGate, RXXGate, RZGate
from qiskit.circuit.measure import Measure
from qiskit.providers import convert_to_target
from qiskit.providers import Options
from qiskit.providers.models import BackendConfiguration
from qiskit.transpiler import Target

from .aqt_job import AqtJob
from ..scaleway_backend import ScalewayBackend
from ...utils import QaaSClient

TargetT = TypeVar("TargetT", bound=Target)


def make_transpiler_target(target_cls: type[TargetT], num_qubits: int) -> TargetT:
    """Factory for transpilation targets of AQT resources.

    Args:
        target_cls: base class to use for the returned instance.
        num_qubits: maximum number of qubits supported by the resource.

    Returns:
        A Qiskit transpilation target for an AQT resource.
    """
    target: TargetT = target_cls(num_qubits=num_qubits)

    theta = Parameter("θ")
    lam = Parameter("λ")

    # configure the transpiler to use RX/RZ/RXX
    # the custom scheduling pass rewrites RX to R to comply to the Arnica API format.
    target.add_instruction(RZGate(lam))
    target.add_instruction(RXGate(theta))
    target.add_instruction(RXXGate(theta))
    target.add_instruction(Measure())

    return target


class AqtBackend(ScalewayBackend):
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

        self._options = self._default_options()

        # Create Target
        self._configuration = BackendConfiguration.from_dict(
            {
                "backend_name": name,
                "backend_version": 2,
                "url": str(provider._portal_client.portal_url),
                "simulator": True,
                "local": False,
                "coupling_map": None,
                "description": "AQT trapped-ion device simulator",
                "basis_gates": ["r", "rz", "rxx"],  # the actual basis gates
                "memory": True,
                "n_qubits": num_qubits,
                "conditional": False,
                "max_shots": self._options.max_shots(),
                "max_experiments": 1,
                "open_pulse": False,
                "gates": [
                    {"name": "rz", "parameters": ["theta"], "qasm_def": "TODO"},
                    {"name": "r", "parameters": ["theta", "phi"], "qasm_def": "TODO"},
                    {"name": "rxx", "parameters": ["theta"], "qasm_def": "TODO"},
                ],
            }
        )
        self._target.num_qubits = num_qubits
        self._target = make_transpiler_target(Target, num_qubits)

        # Set option validators
        self.options.set_validator("shots", (1, 2000))
        self.options.set_validator("memory", bool)

    def __repr__(self) -> str:
        return f"<AqtBackend(name={self.name},num_qubits={self.num_qubits},platform_id={self.id})>"

    def configuration(self) -> BackendConfiguration:
        return self._configuration

    @property
    def target(self):
        return self._target

    @property
    def num_qubits(self) -> int:
        return self._target.num_qubits

    @property
    def max_circuits(self):
        return 50

    def run(
        self, circuits: Union[QuantumCircuit, List[QuantumCircuit]], **run_options
    ) -> AqtJob:
        if not isinstance(circuits, list):
            circuits = [circuits]

        job_config = dict(self._options.items())

        for kwarg in run_options:
            if not hasattr(self.options, kwarg):
                warnings.warn(
                    f"Option {kwarg} is not used by this backend",
                    UserWarning,
                    stacklevel=2,
                )
            else:
                job_config[kwarg] = run_options[kwarg]

        job_name = f"qj-aqt-{randomname.get_name()}"

        session_id = job_config.get("session_id", None)

        job_config.pop("session_id")
        job_config.pop("session_name")
        job_config.pop("session_deduplication_id")
        job_config.pop("session_max_duration")
        job_config.pop("session_max_idle_duration")

        job = AqtJob(
            backend=self,
            client=self._client,
            circuits=circuits,
            config=job_config,
            name=job_name,
        )

        if session_id in ["auto", None]:
            session_id = self.start_session(name=f"auto-{self._options.session_name}")
            assert session_id is not None

        job.submit(session_id)

        return job

    @classmethod
    def _default_options(self):
        # https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html
        return Options(
            session_id="auto",
            session_name="aqt-session-from-qiskit",
            session_deduplication_id="aqt-session-from-qiskit",
            session_max_duration="1h",
            session_max_idle_duration="20m",
            shots=2000,
            memory=False,
        )
