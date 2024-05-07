import json

from enum import Enum
from typing import Union, List
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from qiskit.providers import JobError
from qiskit.result import Result
from qiskit import qasm3
from qiskit.version import VERSION

from ..utils import QaaSClient
from .scaleway_job import ScalewayJob


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
    circuits: List[_CircuitPayload]
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


class AerJob(ScalewayJob):
    def __init__(
        self,
        name: str,
        backend,
        client: QaaSClient,
        circuits,
        config,
    ) -> None:
        super().__init__(name, backend, client)
        self._circuits = circuits
        self._config = config

    def submit(self, session_id: str) -> None:
        if self._job_id:
            raise RuntimeError(f"Job already submitted (ID: {self._job_id})")

        options = self._config.copy()
        shots = options.pop("shots")

        runOpts = _RunPayload(
            shots=shots,
            options={},
            circuits=list(
                map(
                    lambda c: _CircuitPayload(
                        serialization_type=_SerializationType.QASM_V3,
                        circuit_serialization=qasm3.dumps(c),
                    ),
                    self._circuits,
                )
            ),
        )

        backendOpts = _BackendPayload(
            name=self.backend().name,
            version=self.backend().version,
            options=options,
        )

        job_payload = _JobPayload.schema().dumps(
            _JobPayload(
                backend=backendOpts,
                run=runOpts,
                version=VERSION,
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
