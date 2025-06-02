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

from abc import ABC
from typing import List

from qiskit.providers import JobV1
from qiskit.providers import JobError, JobTimeoutError, JobStatus

from qiskit_scaleway.api import QaaSClient, QaaSJobResult


class BaseJob(JobV1, ABC):
    def __init__(
        self,
        name: str,
        backend,
        client: QaaSClient,
    ) -> None:
        super().__init__(backend, None)
        self._name = name
        self._client = client

    def _extract_payload_from_response(self, job_result: QaaSJobResult) -> str:
        result = job_result.result

        if result is None or result == "":
            url = job_result.url

            if url is not None:
                url = url.replace("http//s3:", "http//localhost")

                resp = httpx.get(url)
                resp.raise_for_status()

                return resp.text
            else:
                raise Exception("Got result with empty data and url fields")
        else:
            return result

    def _wait_for_result(
        self, timeout=None, fetch_interval: int = 5
    ) -> List[QaaSJobResult]:
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time

            if timeout is not None and elapsed >= timeout:
                raise JobTimeoutError("Timed out waiting for result")

            status = self.status()

            if status == JobStatus.DONE:
                return self._client.get_job_results(self._job_id)

            if status == JobStatus.ERROR:
                raise JobError("Job error")

            time.sleep(fetch_interval)

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
