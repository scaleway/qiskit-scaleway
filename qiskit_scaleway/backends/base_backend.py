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
import warnings

from typing import Union, Optional
from abc import ABC

from typing import Union, List

from qiskit.providers import BackendV2
from qiskit.circuit import QuantumCircuit

from scaleway_qaas_client.v1alpha1 import QaaSClient, QaaSPlatform

from .base_job import BaseJob


class BaseBackend(BackendV2, ABC):
    def __init__(
        self,
        provider,
        client: QaaSClient,
        platform: QaaSPlatform,
        **fields,
    ):
        super().__init__(
            provider=provider,
            backend_version=platform.version,
            name=platform.name,
            **fields,
        )

        self._platform = platform
        self._client = client

    @property
    def num_qubits(self) -> int:
        return self._platform.max_qubit_count

    @property
    def max_circuits(self) -> int:
        return self._platform.max_circuit_count

    @property
    def id(self) -> str:
        return self._platform.id

    @property
    def availability(self):
        return self._platform.availability

    def run(
        self, circuits: Union[QuantumCircuit, List[QuantumCircuit]], **run_options
    ) -> BaseJob:
        if not isinstance(circuits, List):
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

        session_id = job_config.get("session_id", None)

        job_config.pop("session_id")
        job_config.pop("session_name")
        job_config.pop("session_deduplication_id")
        job_config.pop("session_max_duration")
        job_config.pop("session_max_idle_duration")

        job = BaseJob(
            backend=self,
            client=self._client,
            circuits=circuits,
            config=job_config,
        )

        if session_id in ["auto", None]:
            session_id = self.start_session(name=f"auto-{self._options.session_name}")
            assert session_id is not None

        job.submit(session_id)

        return job

    def start_session(
        self,
        name: Optional[str] = None,
        deduplication_id: Optional[str] = None,
        max_duration: Union[int, str] = None,
        max_idle_duration: Union[int, str] = None,
    ) -> str:
        if name is None:
            name = self._options.get("session_name")

        if deduplication_id is None:
            deduplication_id = self._options.get("session_deduplication_id")

        if max_duration is None:
            max_duration = self._options.get("session_max_duration", "59m")

        if max_idle_duration is None:
            max_idle_duration = self._options.get("session_max_idle_duration", "25m")

        return self._client.create_session(
            name=name,
            platform_id=self.id,
            deduplication_id=deduplication_id,
            max_duration=max_duration,
            max_idle_duration=max_idle_duration,
        ).id

    def stop_session(self, session_id: str):
        self._client.terminate_session(
            session_id=session_id,
        )

    def delete_session(self, session_id: str):
        self._client.delete_session(
            session_id=session_id,
        )
