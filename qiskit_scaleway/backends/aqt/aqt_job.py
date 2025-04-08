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
import json

from typing import Union, List

from qiskit.providers import JobError, JobStatus
from qiskit.result import Result
from qiskit.circuit import QuantumCircuit

from qiskit_aqt_provider.circuit_to_aqt import circuits_to_aqt_job
from qiskit_aqt_provider.aqt_job import _partial_qiskit_result_dict

from qiskit_scaleway.api import QaaSClient
from qiskit_scaleway.backends import BaseJob


class AqtJob(BaseJob):
    def __init__(
        self,
        name: str,
        backend,
        client: QaaSClient,
        circuits: List[QuantumCircuit],
        config,
    ) -> None:
        super().__init__(name, backend, client)
        self._circuits = circuits
        self._config = config

    def submit(self, session_id: str):
        if self._job_id:
            raise RuntimeError(f"Job already submitted (ID: {self._job_id})")

        aqt_job = circuits_to_aqt_job(self._circuits, self._config["shots"])

        self._job_id = self._client.create_job(
            name=self._name,
            session_id=session_id,
            circuits=aqt_job.payload.model_dump_json(),
        ).id

    def result(
        self, timeout=None, fetch_interval: int = 3
    ) -> Union[Result, List[Result]]:
        if self._job_id == None:
            raise JobError("Job ID error")

        job_results = self._wait_for_result(timeout, fetch_interval)

        def __make_result_from_payload(payload: str) -> Result:
            payload_dict = json.loads(payload)
            results = []

            for circuit_idx_str, samples in payload_dict.items():
                circuit_idx = int(circuit_idx_str)
                circuit = self._circuits[circuit_idx]

                results.append(
                    _partial_qiskit_result_dict(
                        samples,
                        circuit,
                        shots=self._config["shots"],
                        memory=self._config["memory"],
                    )
                )

            return Result.from_dict(
                {
                    "results": results,
                    "backend_name": self.backend().name,
                    "backend_version": self.backend().version,
                    "job_id": self._job_id,
                    "qobj_id": id(self._circuits),
                    "success": self.status() == JobStatus.DONE,
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
