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

from typing import Union, List

from qiskit.providers import Options
from qiskit.circuit import QuantumCircuit

from qiskit_scaleway.backends.iqm.iqm_job import IqmJob
from qiskit_scaleway.backends import BaseBackend
from qiskit_scaleway.api import QaaSClient, QaaSPlatform


class IqmBackend(BaseBackend):
    def __init__(self, provider, client: QaaSClient, platform: QaaSPlatform):
        super().__init__(
            provider=provider,
            client=client,
            platform=platform,
        )

        self._options = self._default_options()
        self._platform = platform

    def __repr__(self) -> str:
        return f"<IqmBackend(name={self.name},num_qubits={self.num_qubits},platform_id={self.id})>"

    @property
    def num_qubits(self) -> int:
        return self._platform.max_qubit_count

    @property
    def max_circuits(self):
        return self._platform.max_circuit_count

    def run(
        self, circuits: Union[QuantumCircuit, List[QuantumCircuit]], **run_options
    ) -> IqmJob:
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

        job_name = f"qj-iqm-{randomname.get_name()}"

        session_id = job_config.get("session_id", None)

        job_config.pop("session_id")
        job_config.pop("session_name")
        job_config.pop("session_deduplication_id")
        job_config.pop("session_max_duration")
        job_config.pop("session_max_idle_duration")

        job = IqmJob(
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
            session_name="iqm-session-from-qiskit",
            session_deduplication_id="iqm-session-from-qiskit",
            session_max_duration="59h",
            session_max_idle_duration="20m",
            shots=1000,
        )
