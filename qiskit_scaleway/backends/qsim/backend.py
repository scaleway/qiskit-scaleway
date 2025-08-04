# Copyright 2024 Scaleway
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

from typing import Union, List

from qiskit.providers import Options
from qiskit.circuit import QuantumCircuit
from qiskit.transpiler import Target

from qiskit_scaleway.backends.qsim.job import QsimJob
from qiskit_scaleway.backends import BaseBackend

from scaleway_qaas_client.v1alpha1 import QaaSClient, QaaSPlatform


class QsimBackend(BaseBackend):
    def __init__(self, provider, client: QaaSClient, platform: QaaSPlatform):
        super().__init__(
            provider=provider,
            client=client,
            platform=platform,
        )

        self._options = self._default_options()
        self.options.set_validator("shots", (1, platform.max_shot_count))

        self._target = Target(num_qubits=platform.max_qubit_count)

    def __repr__(self) -> str:
        return f"<QsimBackend(name={self.name},num_qubits={self.num_qubits},platform_id={self.id})>"

    @property
    def target(self):
        return self._target

    @property
    def job_cls(self):
        return QsimJob

    def run(
        self, circuits: Union[QuantumCircuit, List[QuantumCircuit]], **kwargs
    ) -> QsimJob:
        if not isinstance(circuits, List):
            circuits = [circuits]

        job_config = dict(self._options.items())

        for kwarg in kwargs:
            if not hasattr(self.options, kwarg):
                warnings.warn(
                    f"Option {kwarg} is not used by this backend",
                    UserWarning,
                    stacklevel=2,
                )
            else:
                job_config[kwarg] = kwargs[kwarg]

        job_name = f"qj-qsim-{randomname.get_name()}"

        session_id = job_config.get("session_id", None)

        job_config.pop("session_id")
        job_config.pop("session_name")
        job_config.pop("session_deduplication_id")
        job_config.pop("session_max_duration")
        job_config.pop("session_max_idle_duration")

        job = QsimJob(
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
        return Options(
            session_id="auto",
            session_name="qsim-session-from-qiskit",
            session_deduplication_id="qsim-session-from-qiskit",
            session_max_duration="59m",
            session_max_idle_duration="20m",
            shots=1000,
            circuit_memoization_size=0,
            max_fused_gate_size=2,
            ev_noisy_repetitions=1,
            denormals_are_zeros=False,
        )
