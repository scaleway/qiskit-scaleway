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
import time
import httpx
import json
import randomname

from typing import List, Union, Optional, Dict

from qiskit import qasm3, QuantumCircuit
from qiskit.result import Result
from qiskit.providers import JobV1
from qiskit.providers import JobError, JobTimeoutError, JobStatus

from qiskit_scaleway.versions import USER_AGENT

from scaleway_qaas_client.v1alpha1 import (
    QaaSClient,
    QaaSJobResult,
    QaaSJobData,
    QaaSJobClientData,
    QaaSCircuitData,
    QaaSJobRunData,
    QaaSJobBackendData,
    QaaSCircuitSerializationFormat,
)


class BaseJob(JobV1):
    def __init__(
        self,
        backend,
        client: QaaSClient,
        circuits: Union[List[QuantumCircuit], QuantumCircuit],
        config: Dict,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(backend, None)
        self._name = name if name else f"qj-qiskit-{randomname.get_name()}"
        self._client = client
        self._circuits = circuits
        self._config = config

    @property
    def name(self):
        return self._name

    def status(self) -> JobStatus:
        job = self._client.get_job(self._job_id)

        status_mapping = {
            "running": JobStatus.RUNNING,
            "waiting": JobStatus.QUEUED,
            "completed": JobStatus.DONE,
        }

        return status_mapping.get(job.status, JobStatus.ERROR)

    def submit(self, session_id: str) -> None:
        if self._job_id:
            raise RuntimeError(f"Job already submitted (ID: {self._job_id})")

        options = self._config.copy()

        run_data = QaaSJobRunData(
            options={
                "shots": options.pop("shots"),
                "memory": options.pop("memory", False),
            },
            circuits=list(
                map(
                    lambda c: QaaSCircuitData(
                        serialization_format=QaaSCircuitSerializationFormat.QASM_V3,
                        circuit_serialization=qasm3.dumps(c),
                    ),
                    self._circuits,
                )
            ),
        )

        backend_data = QaaSJobBackendData(
            name=self.backend().name,
            version=self.backend().version,
            options=options,
        )

        client_data = QaaSJobClientData(
            user_agent=USER_AGENT,
        )

        data = QaaSJobData.schema().dumps(
            QaaSJobData(
                backend=backend_data,
                run=run_data,
                client=client_data,
            )
        )

        self._job_id = self._client.create_job(
            name=self._name,
            session_id=session_id,
            payload=data,
        ).id

    def result(
        self, timeout: Optional[int] = None, fetch_interval: int = 3
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

    def _extract_payload_from_response(self, job_result: QaaSJobResult) -> str:
        result = job_result.result

        if result is None or result == "":
            url = job_result.url

            if url is not None:
                resp = httpx.get(url.replace("http://s3", "http://localhost"))
                resp.raise_for_status()

                return resp.text
            else:
                raise Exception("Got result with empty data and url fields")
        else:
            return result

    def _wait_for_result(
        self, timeout: Optional[int], fetch_interval: int
    ) -> List[QaaSJobResult]:
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time

            if timeout is not None and elapsed >= timeout:
                raise JobTimeoutError("Timed out waiting for result")

            status = self.status()

            if status == JobStatus.DONE:
                return self._client.list_job_results(self._job_id)

            if status == JobStatus.ERROR:
                raise JobError("Job error")

            time.sleep(fetch_interval)
