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
import time
import httpx
import randomname

from typing import List, Union, Optional, Dict

from qiskit import QuantumCircuit
from qiskit.result import Result
from qiskit.providers import JobV1
from qiskit.providers import JobError, JobTimeoutError, JobStatus

from qiskit_scaleway.versions import USER_AGENT

from qio.core import (
    QuantumProgram,
    QuantumProgramResult,
    QuantumComputationModel,
    QuantumComputationParameters,
    QuantumNoiseModel,
    BackendData,
    ClientData,
)

from scaleway_qaas_client.v1alpha1 import (
    QaaSClient,
    QaaSJobResult,
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
        self._name = name or f"qj-qiskit-{randomname.get_name()}"
        self._client = client
        self._circuits = circuits
        self._config = config
        self._last_progress_message = ""

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

        if job.progress_message is not None:
            self._last_progress_message = job.progress_message

        return status_mapping.get(job.status, JobStatus.ERROR)

    def submit(self, session_id: str) -> None:
        if self._job_id:
            raise RuntimeError(f"Job already submitted (ID: {self._job_id})")

        options = self._config.copy()
        shots = options.pop("shots")
        memory = options.pop("memory", False)

        programs = map(lambda c: QuantumProgram.from_qiskit_circuit(c), self._circuits)

        noise_model = options.pop("noise_model", None)
        if noise_model:
            noise_model = QuantumNoiseModel.from_qiskit_aer_noise_model(noise_model)

        backend_data = BackendData(
            name=self.backend().name,
            version=self.backend().version,
            options=options,
        )

        client_data = ClientData(
            user_agent=USER_AGENT,
        )

        computation_model_json = QuantumComputationModel(
            programs=programs,
            backend=backend_data,
            client=client_data,
            noise_model=noise_model,
        ).to_json_str()

        computation_parameters_json = QuantumComputationParameters(
            shots=shots,
            options={
                "memory": memory,
            },
        ).to_json_str()

        model = self._client.create_model(
            payload=computation_model_json,
        )

        if not model:
            raise RuntimeError("Failed to push circuit data")

        self._last_progress_message = ""
        self._job_id = self._client.create_job(
            name=self._name,
            session_id=session_id,
            model_id=model.id,
            parameters=computation_parameters_json,
        ).id

    def result(
        self, timeout: Optional[int] = None, fetch_interval: int = 3
    ) -> Union[Result, List[Result]]:
        if self._job_id == None:
            raise JobError("Job ID error")

        job_results = self._wait_for_result(timeout, fetch_interval)

        program_results = list(
            map(
                lambda r: self._extract_payload_from_response(r).to_qiskit_result(
                    backend_name=self.backend().name,
                    backend_version=self.backend().version,
                    job_id=self._job_id,
                    qobj_id=", ".join(x.name for x in self._circuits),
                ),
                job_results,
            )
        )

        if len(program_results) == 1:
            return program_results[0]

        return program_results

    def _extract_payload_from_response(
        self, job_result: QaaSJobResult
    ) -> QuantumProgramResult:
        result = job_result.result

        if result is None or result == "":
            url = job_result.url

            if url is not None:
                resp = httpx.get(url)
                resp.raise_for_status()
                result = resp.text
            else:
                raise RuntimeError("Got result with empty data and url fields")

        return QuantumProgramResult.from_json_str(result)

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
                raise JobError(f"Job failed: {self._last_progress_message}")

            time.sleep(fetch_interval)
