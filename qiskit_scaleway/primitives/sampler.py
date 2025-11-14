# Copyright 2024 Scaleway
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import numpy as np
import re

from numpy.typing import NDArray

from qiskit.primitives.backend_sampler_v2 import (
    BackendSamplerV2,
    _MeasureInfo,
    _samples_to_packed_array,
    QiskitError,
    ResultMemory,
)

from qiskit.primitives.containers import (
    BitArray,
    DataBin,
    SamplerPubResult,
)

_NON_BINARY_CHARS = re.compile(r"[^01]")


class Sampler(BackendSamplerV2):
    def __init__(
        self,
        backend,
        session_id: str,
        options: dict | None = None,
    ):
        if not session_id:
            raise Exception("session_id must be not None")

        if not options:
            options = {}

        if not options.get("run_options"):
            options["run_options"] = {}

        if not options["run_options"].get("session_id"):
            options["run_options"]["session_id"] = session_id

        super().__init__(
            backend=backend,
            options=options,
        )

    def _postprocess_pub(
        self,
        result_memory: list[ResultMemory],
        shots: int,
        shape: tuple[int, ...],
        meas_info: list[_MeasureInfo],
        max_num_bytes: int,
        circuit_metadata: dict,
        meas_level: int | None,
    ) -> SamplerPubResult:
        """Converts the memory data into a sampler pub result

        For level 2 data, the memory data are stored in an array of bit arrays
        with the shape of the pub. For level 1 data, the data are stored in a
        complex numpy array.
        """
        if meas_level == 2 or meas_level is None:
            arrays = {
                item.creg_name: np.zeros(
                    shape + (shots, item.num_bytes), dtype=np.uint8
                )
                for item in meas_info
            }
            memory_array = _memory_array(result_memory, max_num_bytes)

            for samples, index in zip(memory_array, np.ndindex(*shape)):
                for item in meas_info:
                    ary = _samples_to_packed_array(samples, item.num_bits, item.start)
                    arrays[item.creg_name][index] = ary

            meas = {
                item.creg_name: BitArray(arrays[item.creg_name], item.num_bits)
                for item in meas_info
            }
        elif meas_level == 1:
            raw = np.array(result_memory)
            cplx = raw[..., 0] + 1j * raw[..., 1]
            cplx = np.reshape(cplx, (*shape, *cplx.shape[1:]))
            meas = {item.creg_name: cplx for item in meas_info}
        else:
            raise QiskitError(f"Unsupported meas_level: {meas_level}")
        return SamplerPubResult(
            DataBin(**meas, shape=shape),
            metadata={"shots": shots, "circuit_metadata": circuit_metadata},
        )


def _memory_array(results: list[list[str]], num_bytes: int) -> NDArray[np.uint8]:
    """Converts the memory data into an array in an unpacked way."""
    lst = []
    # Heuristic: check only the first result format
    if len(results) > 0 and len(results[0]) > 0:
        base = 16 if _NON_BINARY_CHARS.search(results[0][0]) else 2

    for memory in results:
        if num_bytes > 0:
            data = b"".join(int(i, base).to_bytes(num_bytes, "big") for i in memory)
            data = np.frombuffer(data, dtype=np.uint8).reshape(-1, num_bytes)
        else:
            # no measure in a circuit
            data = np.zeros((len(memory), num_bytes), dtype=np.uint8)
        lst.append(data)
    ary = np.asarray(lst)
    return np.unpackbits(ary, axis=-1, bitorder="big")
