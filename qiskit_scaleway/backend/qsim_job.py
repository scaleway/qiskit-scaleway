import json

from enum import Enum
from typing import Union, List
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from qiskit.providers import JobError
from qiskit.result import Result
from qiskit import qasm2

from ..utils import QaaSClient
from .scaleway_job import ScalewayJob


class _SerializationType(Enum):
    UNKOWN = 0
    QASM_V1 = 1
    QASM_V2 = 2


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


# @dataclass_json
# @dataclass
# class _QSimOptions:
#     max_fused_gate_size: int
#     ev_noisy_repetitions: int
#     denormals_are_zeros: bool


class QsimJob(ScalewayJob):
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
            options=options,
            circuit=_CircuitPayload(
                serialization_type=_SerializationType.QASM_V2,
                circuit_serialization=qasm2.dumps(self._circuits[0]),
            ),
        )

        options.pop("circuit_memoization_size")

        backendOpts = _BackendPayload(
            name="qsim",
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

        def __make_result_from_payload(payload: str) -> Result:
            print(payload)
            return Result()

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
