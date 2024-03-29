import time
import json

from qiskit.providers import JobV1 as Job
from qiskit.providers import JobError
from qiskit.providers import JobTimeoutError
from qiskit.providers.jobstatus import JobStatus
from qiskit.result import Result
from qiskit import qasm2

from enum import Enum
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from .client import ScalewayClient
from .backend import ScalewayBackend


class _SerializationType(Enum):
    UNKOWN = 0
    QASM_V1 = 1
    QASM_V2 = 2
    QASM_V3 = 3


@dataclass_json
@dataclass
class _CircuitPayload:
    serialization_type: _SerializationType
    circuit_serialization: str


@dataclass_json
@dataclass
class _RunPayload:
    shots: int
    circuit: _CircuitPayload
    options: dict


@dataclass_json
@dataclass
class _BackendPayload:
    name: str
    version: str
    options: dict


@dataclass_json
@dataclass
class _JobPayload:
    version: str
    backend: _BackendPayload
    run: _RunPayload


class ScalewayJob(Job):
    def __init__(
        self,
        name: str,
        backend: ScalewayBackend,
        client: ScalewayClient,
        circuits,
        config,
    ) -> None:
        super().__init__(backend, None)
        self._circuits = circuits
        self._name = name
        self._config = config
        self._client = client

    def _wait_for_result(self, timeout=None) -> dict | None:
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

            time.sleep(3)

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

    def submit(self, session_id: str, **kwargs) -> None:
        if self._job_id:
            raise RuntimeError(f"Job already submitted (ID: {self._job_id})")

        qiskit_payload = _JobPayload.schema().dumps(
            _JobPayload(
                backend=_BackendPayload(
                    name="aer",
                    version="1.0",
                    options=self._config,
                ),
                run=_RunPayload(
                    shots=self._config["shots"],
                    # options=self._config,
                    circuit=_CircuitPayload(
                        serialization_type=_SerializationType.QASM_V2,
                        circuit_serialization=qasm2.dumps(self._circuits[0]),
                    ),
                ),
                version="1.0",
            )
        )

        self._job_id = self._client.create_job(
            name=self._name,
            session_id=session_id,
            circuits=qiskit_payload,
        )

    def result(self, timeout=None, wait=5):
        if self._job_id == None:
            raise JobError("Job ID error")

        job_results = self._wait_for_result(timeout, wait)

        # TODO
        job_result = job_results[0]
        result_load = json.loads(job_result["result"])

        # results = [{'success': True, 'shots': 1, 'data': 1}]
        return Result.from_dict(
            {
                "results": result_load,
                "backend_name": self.backend().name,
                "backend_version": self.backend().version,
                "job_id": self._job_id,
                "qobj_id": ", ".join(x.name for x in self.circuits),
                "success": True,
            }
        )
