import time
import json
import randomname

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
        backend: ScalewayBackend,
        client: ScalewayClient,
        job_id: str,
        circuits,
        config,
    ) -> None:
        super().__init__(backend, job_id)
        # self.__backend = backend
        # self.__circuits = circuits
        self.__job_id = job_id
        self.__config = config
        self.__client = client
        self.__name = None

    def _wait_for_result(self, timeout=None) -> dict | None:
        start_time = time.time()
        result = None

        while True:
            elapsed = time.time() - start_time
            if timeout and elapsed >= timeout:
                raise JobTimeoutError("Timed out waiting for result")
            status = self.status()
            if status == JobStatus.DONE:
                result = self.__client.get_job_result(self._job_id)
                break
            if status == JobStatus.ERROR:
                raise JobError("Job error")

            time.sleep(5)

        return result

    @property
    def name(self):
        return self.__name

    @property
    def id(self):
        return self.__job_id

    def status(self) -> JobStatus:
        result = self.__client.get_job(self._job_id)
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
        # deduplication_id = self._provider.session
        qiskit_payload = _JobPayload.schema().dumps(
            _JobPayload(
                backend=_BackendPayload(
                    name="aer",
                    version="1.0",
                    options={
                        "method": "statevector",
                    },
                ),
                run=_RunPayload(
                    shots=self.__config["shots"],
                    options=self.__config,
                    circuit=_CircuitPayload(
                        serialization_type=_SerializationType.QASM_V2,
                        circuit_serialization=qasm2.dumps(self.circuits[0]),
                    ),
                ),
                version="1.0",
            )
        )

        # session_id = self.__client.create_session(
        #     name= "",deduplication_id=deduplication_id, platform_id=self.__backend.id
        # )

        if self.__job_id:
            raise RuntimeError(f"Job already submitted (ID: {self.__job_id})")

        self.__job_id = self.__client.create_job(
            name=f"qj-aer-{randomname.get_name()}-{session_id}",
            session_id=session_id,
            circuits=qiskit_payload,
        )

    def result(self, timeout=None, wait=5):
        if self.__job_id == None:
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
