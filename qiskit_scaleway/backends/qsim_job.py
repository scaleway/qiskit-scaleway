import json
import io
import collections

import numpy as np

from enum import Enum
from typing import Union, List
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

from qiskit import qasm2
from qiskit.providers import JobError
from qiskit.result import Result
from qiskit.transpiler.passes import RemoveBarriers
from qiskit.result.models import ExperimentResult, ExperimentResultData
from qiskit.version import VERSION

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


def _tuple_of_big_endian_int(bit_groups: Iterable[Any]) -> Tuple[int, ...]:
    return tuple(_big_endian_bits_to_int(bits) for bits in bit_groups)


def _big_endian_bits_to_int(bits: Iterable[Any]) -> int:
    result = 0

    for e in bits:
        result <<= 1
        if e:
            result |= 1

    return result


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

        # Note 1: Barriers are only visual elements
        # Barriers are not managed by Cirq deserialization
        # Note 2: Qsim can only handle on circuit at a time
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

        def __make_hex_from_result_array(result: Tuple):
            str_value = "".join(map(str, result))
            integer_value = int(str_value, 2)
            return hex(integer_value)

        def __make_expresult_from_cirq_result(
            cirq_result: CirqResult,
        ) -> ExperimentResult:
            hist = dict(
                cirq_result.multi_measurement_histogram(
                    keys=cirq_result.measurements.keys()
                )
            )

            return ExperimentResult(
                shots=cirq_result.repetitions,
                success=True,
                data=ExperimentResultData(
                    counts={
                        __make_hex_from_result_array(key): value
                        for key, value in hist.items()
                    },
                ),
            )

        def __make_result_from_payload(payload: str) -> Result:
            payload_dict = json.loads(payload)
            cirq_result = CirqResult._from_json_dict_(**payload_dict)

            return Result(
                backend_name=self.backend().name,
                backend_version=self.backend().version,
                job_id=self._job_id,
                qobj_id=", ".join(x.name for x in self._circuits),
                success=True,
                results=__make_expresult_from_cirq_result(cirq_result),
                status=None,  # TODO
                header=None,  # TODO
                date=None,  # TODO
                cirq_result=payload,
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
            measurements = {}
            records = {}
        self._params = None
        self._measurements = measurements
        self._records = records

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

    def multi_measurement_histogram(
        self,
        *,  # Forces keyword args.
        keys: Iterable,
        fold_func: Callable = cast(Callable, _tuple_of_big_endian_int),
    ) -> collections.Counter:
        fixed_keys = tuple(key for key in keys)
        samples: Iterable[Any] = zip(
            *(self.measurements[sub_key] for sub_key in fixed_keys)
        )

        if len(fixed_keys) == 0:
            samples = [()] * self.repetitions

        c: collections.Counter = collections.Counter()

        for sample in samples:
            c[fold_func(sample)] += 1
        return c

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

    @property
    def repetitions(self) -> int:
        if not self.records:
            return 0
        # Get the length quickly from one of the keyed results.
        return len(next(iter(self.records.values())))