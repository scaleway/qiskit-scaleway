import time

from qiskit.providers import JobV1 as Job
from qiskit.providers import JobError
from qiskit.providers import JobTimeoutError
from qiskit.providers.jobstatus import JobStatus
from qiskit.result import Result
from .client import ScalewayClient
from qiskit_qir import to_qir_module
from qiskit import qasm2


class ScalewayJob(Job):
    def __init__(self, backend, job_id, circuits, config):
        super().__init__(backend, job_id)
        self._backend = backend
        self.circuits = circuits
        self._provider = backend.provider
        self._config = config
        self._client = ScalewayClient(
            url=self._provider.url,
            token=self._provider.secret_key,
            project_id=self._provider.project_id,
        )

    def _wait_for_result(self, timeout=None, wait=5):
        start_time = time.time()
        result = None
        while True:
            elapsed = time.time() - start_time
            if timeout and elapsed >= timeout:
                raise JobTimeoutError("Timed out waiting for result")
            status = self.status()
            if status == JobStatus.DONE:
                result = self._client.get_job_result(self._job_id)
                break
            if status == JobStatus.ERROR:
                raise JobError("Job error")
            time.sleep(wait)
        return result

    def result(self, timeout=None, wait=5):
        if self._job_id == None:
            raise JobError("Job ID error")
        result = self._wait_for_result(timeout, wait)
        print(result)
        # results = [{'success': True, 'shots': len(result['counts']),
        #             'data': result['counts']}]
        # return Result.from_dict({
        #     'results': results,
        #     'backend_name': self._backend.configuration().backend_name,
        #     'backend_version': self._backend.configuration().backend_version,
        #     'job_id': self._job_id,
        #     'qobj_id': ', '.join(x.name for x in self.circuits),
        #     'success': True,
        # })

    def status(self):
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

    def submit(self) -> None:
        # backend_name = self.backend().name
        deduplication_id = self._provider.session
        platform_id = self.backend().platform_id

        qiskit_payload = {
            "backend": {
                "name": "aer",
                "version": "1.0",
                "options": {
                    "method": "statevector",
                },
            },
            "run": {
                "shots": self._config["shots"],
                "options": {},
                "circuit": {
                    "serialization_type": 2,
                    "circuit_serialization": qasm2.dumps(self.circuits[0]),
                },
            },
            "version": "1.0",
        }

        session_id = self._client.create_session(
            deduplication_id=deduplication_id, platform_id=platform_id
        )

        if self._job_id:
            raise RuntimeError(f"Job already submitted (ID: {self._job_id})")

        self._job_id = self._client.create_job(
            session_id=session_id, circuits=qiskit_payload
        )
