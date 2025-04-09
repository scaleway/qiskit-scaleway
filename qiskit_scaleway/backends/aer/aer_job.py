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
import json

from typing import Union, List

from qiskit.providers import JobError
from qiskit.result import Result
from qiskit import qasm3

from qiskit_scaleway.api import QaaSClient
from qiskit_scaleway.versions import USER_AGENT
from qiskit_scaleway.backends import BaseJob
from qiskit_scaleway.backends.aer.aer_models import (
    JobPayload,
    ClientPayload,
    BackendPayload,
    RunPayload,
    SerializationType,
    CircuitPayload,
)


class AerJob(BaseJob):
    def __init__(
        self,
        name: str,
        backend,
        client: QaaSClient,
        circuits,
        config,
    ) -> None:
        super().__init__(name, backend, client)
        self._circuits = circuits
        self._config = config

    def submit(self, session_id: str) -> None:
        if self._job_id:
            raise RuntimeError(f"Job already submitted (ID: {self._job_id})")

        options = self._config.copy()

        run_opts = RunPayload(
            options={
                "shots": options.pop("shots"),
                "memory": options.pop("memory"),
                "seed_simulator": options.pop("seed_simulator"),
            },
            circuits=list(
                map(
                    lambda c: CircuitPayload(
                        serialization_type=SerializationType.QASM_V3,
                        circuit_serialization=qasm3.dumps(c),
                    ),
                    self._circuits,
                )
            ),
        )

        backend_opts = BackendPayload(
            name=self.backend().name,
            version=self.backend().version,
            options=options,
        )

        client_opts = ClientPayload(
            user_agent=USER_AGENT,
        )

        job_payload = JobPayload.schema().dumps(
            JobPayload(
                backend=backend_opts,
                run=run_opts,
                client=client_opts,
            )
        )

        self._job_id = self._client.create_job(
            name=self._name,
            session_id=session_id,
            circuits=job_payload,
        ).id

    def result(
        self, timeout=None, fetch_interval: int = 3
    ) -> Union[Result, List[Result]]:
        if self._job_id == None:
            raise JobError("Job ID error")

        job_results = self._wait_for_result(timeout, fetch_interval)

        def __make_result_from_payload(payload: str) -> Result:
            payload_dict = json.loads(payload)

            return Result.from_dict(
                {
                    "results": payload_dict["results"],
                    "backend_name": self.backend().name,
                    "backend_version": self.backend().version,
                    "job_id": self._job_id,
                    "qobj_id": ", ".join(x.name for x in self._circuits),
                    "success": payload_dict["success"],
                    "header": payload_dict.get("header"),
                    "metadata": payload_dict.get("metadata"),
                }
            )

        qiskit_results = list(
            map(
                lambda r: __make_result_from_payload(
                    self._extract_payload_from_response(r)
                ),
                job_results,
            )
        )

        if len(qiskit_results) == 1:
            return qiskit_results[0]

        return qiskit_results
