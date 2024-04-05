import json
import io

import numpy as np
import pandas as pd

from enum import Enum
from typing import Union, List
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import (
    Mapping,
    Optional,
    Sequence,
    Union,
    cast,
)

from qiskit import qasm2
from qiskit.providers import JobError
from qiskit.result import Result
from qiskit.transpiler.passes import RemoveBarriers
from qiskit.result.models import ExperimentResult, ExperimentResultData

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

        # Barriers are only visual elements
        # Barriers are not handle by Cirq deserialization
        circuit = RemoveBarriers()(self._circuits[0])

        runOpts = _RunPayload(
            shots=shots,
            options=options,
            circuit=_CircuitPayload(
                serialization_type=_SerializationType.QASM_V2,
                circuit_serialization=qasm2.dumps(circuit),
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

        def __make_expresult_from_meas(k, v) -> ExperimentResult:
            print(k)
            print(v)
            return ExperimentResult(
                shots=None, success=True, data=ExperimentResultData()
            )

        def __make_result_from_payload(payload: str) -> Result:
            payload_dict = json.loads(payload)
            cirq_result = CirqResult._from_json_dict_(**payload_dict)

            return Result(
                backend_name="QsimSimulator",
                backend_version="0.21.0",
                job_id=self._job_id,
                qobj_id=", ".join(x.name for x in self._circuits),
                success=True,
                results=[
                    __make_expresult_from_meas(k, m)
                    for k, m in enumerate(cirq_result.records)
                ],
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


class CirqResult(Result):
    def __init__(
        self,
        *,  # Forces keyword args.
        measurements: Optional[Mapping[str, np.ndarray]] = None,
        records: Optional[Mapping[str, np.ndarray]] = None,
    ) -> None:
        if measurements is None and records is None:
            # For backwards compatibility, allow constructing with None.
            measurements = {}
            records = {}
        self._params = None
        self._measurements = measurements
        self._records = records
        self._data: Optional[pd.DataFrame] = None

    @property
    def measurements(self) -> Mapping[str, np.ndarray]:
        if self._measurements is None:
            assert self._records is not None
            self._measurements = {}
            for key, data in self._records.items():
                reps, instances, qubits = data.shape
                if instances != 1:
                    raise ValueError("Cannot extract 2D measurements for repeated keys")
                self._measurements[key] = data.reshape((reps, qubits))
        return self._measurements

    @property
    def records(self) -> Mapping[str, np.ndarray]:
        if self._records is None:
            assert self._measurements is not None
            self._records = {
                key: data[:, np.newaxis, :] for key, data in self._measurements.items()
            }
        return self._records

    @property
    def repetitions(self) -> int:
        if self._records is not None:
            if not self._records:
                return 0
            # Get the length quickly from one of the keyed results.
            return len(next(iter(self._records.values())))
        else:
            if not self._measurements:
                return 0
            # Get the length quickly from one of the keyed results.
            return len(next(iter(self._measurements.values())))

    @property
    def data(self) -> pd.DataFrame:
        if self._data is None:
            self._data = self.dataframe_from_measurements(self.measurements)
        return self._data

    @classmethod
    def _from_packed_records(cls, records, **kwargs):
        return cls(
            records={key: _unpack_digits(**val) for key, val in records.items()},
            **kwargs,
        )

    @classmethod
    def _from_json_dict_(cls, **kwargs):
        if "measurements" in kwargs:
            measurements = kwargs["measurements"]
            return cls(
                params=None,
                measurements={
                    key: _unpack_digits(**val) for key, val in measurements.items()
                },
            )
        return cls._from_packed_records(records=kwargs["records"])

    @staticmethod
    def dataframe_from_measurements(
        measurements: Mapping[str, np.ndarray]
    ) -> pd.DataFrame:
        # Convert to a DataFrame with columns as measurement keys, rows as
        # repetitions and a big endian integer for individual measurements.
        converted_dict = {}
        for key, bitstrings in measurements.items():
            _, n = bitstrings.shape
            dtype = object if n > 63 else np.int64
            basis = 2 ** np.arange(n, dtype=dtype)[::-1]
            converted_dict[key] = np.sum(basis * bitstrings, axis=1)

        # Use objects to accommodate more than 64 qubits if needed.
        dtype = (
            object
            if any(bs.shape[1] > 63 for _, bs in measurements.items())
            else np.int64
        )
        return pd.DataFrame(converted_dict, dtype=dtype)

    @property
    def repetitions(self) -> int:
        if not self.records:
            return 0
        # Get the length quickly from one of the keyed results.
        return len(next(iter(self.records.values())))


def _unpack_digits(
    packed_digits: str,
    binary: bool,
    dtype: Union[None, str],
    shape: Union[None, Sequence[int]],
) -> np.ndarray:
    if binary:
        dtype = cast(str, dtype)
        shape = cast(Sequence[int], shape)
        return _unpack_bits(packed_digits, dtype, shape)

    buffer = io.BytesIO()
    buffer.write(bytes.fromhex(packed_digits))
    buffer.seek(0)
    digits = np.load(buffer, allow_pickle=False)
    buffer.close()
    return digits


def _unpack_bits(packed_bits: str, dtype: str, shape: Sequence[int]) -> np.ndarray:
    bits_bytes = bytes.fromhex(packed_bits)
    bits = np.unpackbits(np.frombuffer(bits_bytes, dtype=np.uint8))
    return bits[: np.prod(shape).item()].reshape(shape).astype(dtype)
