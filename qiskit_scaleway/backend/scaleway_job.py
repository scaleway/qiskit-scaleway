import time
import httpx

from abc import ABC
from qiskit.providers import JobV1 as Job
from qiskit.providers import JobError
from qiskit.providers import JobTimeoutError
from qiskit.providers.jobstatus import JobStatus

from ..utils import QaaSClient


class ScalewayJob(Job, ABC):
    def __init__(
        self,
        name: str,
        backend,
        client: QaaSClient,
    ) -> None:
        super().__init__(backend, None)
        self._name = name
        self._client = client

    def _extract_payload_from_response(self, result_response: dict) -> str:
        result = result_response.get("result", None)

        if result is None or result == "":
            url = result_response.get("url", None)

            if url is not None or result == "":
                http_client = httpx.Client(base_url=url, timeout=10.0, verify=False)

                resp = http_client.get(url)
                resp.raise_for_status()

                return resp.text
        else:
            return result

    def _wait_for_result(self, timeout=None, fetch_interval: int = 5) -> dict | None:
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time

            if timeout and elapsed >= timeout:
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
        result = self._client.get_job(self._job_id)

        if result["status"] == "running":
            status = JobStatus.RUNNING
        elif result["status"] == "waiting":
            status = JobStatus.QUEUED
        elif result["status"] == "completed":
            status = JobStatus.DONE
        else:
            status = JobStatus.ERROR

        return status
