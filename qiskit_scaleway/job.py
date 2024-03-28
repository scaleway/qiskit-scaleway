import time
import json

from qiskit.providers import JobV1 as Job
from qiskit.providers import JobError
from qiskit.providers import JobTimeoutError
from qiskit.providers.jobstatus import JobStatus
from qiskit.result import Result
from .client import ScalewayClient
from qiskit import qasm2
from enum import Enum
from dataclasses import dataclass
from dataclasses_json import dataclass_json

class SerializationType(Enum):
    UNKOWN = 0
    QASM_V1 = 1
    QASM_V2 = 2
    QASM_V3 = 3

@dataclass_json
@dataclass
class CircuitPayload:
    serialization_type: SerializationType # How the circuit was serialized
    circuit_serialization: str # The encoded circuit into string via the serialization type

@dataclass_json
@dataclass
class RunPayload:
    shots: int # corresponds to the number set in 'backend.run(circuit, shots=2000)'
    circuit: CircuitPayload # everything related to the given circuit
    options: dict # Any option that must be blindly forward to the 'backend.run()', except circuit and shots

@dataclass_json
@dataclass
class BackendPayload:
    name: str # Name of the requested platform, ex: aer_simulation_h100
    version: str # Version of the backend
    options: dict # Any option that must be blindly forward to the AerSimulator

@dataclass_json
@dataclass
class QiskitPayload:
    version: str # the qiskit version
    backend: BackendPayload # everything related to the requested platform
    run: RunPayload # everything related to the requested run

class ScalewayJob(Job):
    def __init__(self, backend, job_id: str, circuits, config) -> None:
        super().__init__(backend, job_id)
        self._backend = backend
        self.circuits = circuits
        self._job_id = job_id
        self._provider = backend.provider
        self._config = config
        self._client = ScalewayClient(
            url=self._provider.url,
            token=self._provider.secret_key,
            project_id=self._provider.project_id,
        )

    def _wait_for_result(self, timeout=None, wait=5) -> dict | None:
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
        job_results = self._wait_for_result(timeout, wait)

        # TODO
        # job_result = job_results[0]
        # result_load = json.loads(job_result["result"])

        # results = [{'success': True, 'shots': 1, 'data': 1}]
        # return Result.from_dict({
        #     'results': results,
        #     'backend_name': self.backend().name,
        #     'backend_version': self.backend().version,
        #     'job_id': self._job_id,
        #     'qobj_id': ', '.join(x.name for x in self.circuits),
        #     'success': True,
        # })

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

    def submit(self) -> None:
        # backend_name = self.backend().name
        deduplication_id = self._provider.session
        platform_id = self.backend().platform_id

        qiskit_payload = QiskitPayload.schema().dumps(
            QiskitPayload(
                backend=BackendPayload(
                    name="aer",
                    version="1.0",
                    options={
                        "method": "statevector",
                    },
                ),
                run=RunPayload(
                    shots=100000,
                    options={},
                    circuit=CircuitPayload(
                        serialization_type=SerializationType.QASM_V2,
                        circuit_serialization=qasm2.dumps(
                            self.circuits[0]
                        ),
                    ),
                ),
                version="1.0",
            )
        )

        session_id = self._client.create_session(
            deduplication_id=deduplication_id, platform_id=platform_id
        )

        if self._job_id:
            raise RuntimeError(f"Job already submitted (ID: {self._job_id})")

        self._job_id = self._client.create_job(
            session_id=session_id, circuits=qiskit_payload
        )
