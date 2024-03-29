import time
import json
import httpx

from enum import Enum
from typing import Union, List
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from qiskit.providers import JobV1 as Job
from qiskit.providers import JobError
from qiskit.providers import JobTimeoutError
from qiskit.providers.jobstatus import JobStatus
from qiskit.result import Result
from qiskit import qasm2

from .client import ScalewayClient


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
        backend,
        client: ScalewayClient,
        circuits,
        config,
    ) -> None:
        super().__init__(backend, None)
        self._circuits = circuits
        self._name = name
        self._config = config
        self._client = client

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

    def submit(self, session_id: str) -> None:
        if self._job_id:
            raise RuntimeError(f"Job already submitted (ID: {self._job_id})")

        options = self._config.copy()

        runOpts = _RunPayload(
            shots=options["shots"],
            options={},
            circuit=_CircuitPayload(
                serialization_type=_SerializationType.QASM_V2,
                circuit_serialization=qasm2.dumps(self._circuits[0]),
            ),
        )

        options.pop("shots")

        backendOpts = _BackendPayload(
            name="aer",
            version="1.0",
            options=options,
        )

        job_payload = _JobPayload.schema().dumps(
            _JobPayload(
                backend=backendOpts,
                run=runOpts,
                version="1.0",
            )
        )

        self._job_id = self._client.create_job(
            name=self._name,
            session_id=session_id,
            circuits=job_payload,
        )

    def result(
        self, timeout=None, fetch_interval: int = 3
    ) -> Union[Result, List[Result]]:
        if self._job_id == None:
            raise JobError("Job ID error")

        job_results = self._wait_for_result(timeout, fetch_interval)

        def __extract_payload_from_response(result_response: dict) -> str:
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

        def __make_result_from_payload(payload: str) -> Result:
            payload_dict = json.loads(payload)

            return Result.from_dict(
                {
                    "results": payload_dict["results"],
                    "backend_name": payload_dict["backend_name"],
                    "backend_version": payload_dict["backend_version"],
                    "job_id": self._job_id,
                    "qobj_id": ", ".join(x.name for x in self._circuits),
                    "success": payload_dict["success"],
                }
            )

        qiskit_results = list(map(
            lambda r: __make_result_from_payload(__extract_payload_from_response(r)),
            job_results,
        ))

        if len(qiskit_results) == 1:
            return qiskit_results[0]

        return qiskit_results
