import abc

from typing import List
from qiskit.providers import JobV1 as Job
from qiskit.providers.jobstatus import JobStatus

from ..utils import QaaSClient


class ScalewayApplicationJob(Job, abc.ABC):
    def __init__(self, name: str, client: QaaSClient):
        self._client = client
        self._name = name
        self._final_result = None

    def results(self):
        results = self._client.get_process_results(self._job_id)

    def final_result(self):
        if self.status() != JobStatus.DONE:
            return None

        if self._final_result is None:
            results = self._client.get_process_results(self._job_id)
            self._final_result = results[0]

        return self._final_result

    def status(self) -> JobStatus:
        process = self._client.get_process(self._job_id)

        if process["status"] == "running":
            status = JobStatus.RUNNING
        elif process["status"] == "starting":
            status = JobStatus.QUEUED
        elif process["status"] == "completed":
            status = JobStatus.DONE
        else:
            status = JobStatus.ERROR

        return status

    @property
    def name(self):
        return self._name
