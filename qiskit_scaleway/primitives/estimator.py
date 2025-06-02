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
from qiskit.primitives import BackendEstimatorV2
from qiskit.primitives.backend_estimator import (
    _prepare_counts,
    _run_circuits,
)


class Estimator(BackendEstimatorV2):
    def __init__(
        self,
        backend,
        session_id: str,
        options: dict | None = None,
    ):
        if not session_id:
            raise Exception("session_id must be not None")

        self._session_id = session_id

        super().__init__(
            backend=backend,
            options=options,
        )

    def _run_pubs(self, pubs, shots: int) -> list:
        """Compute results for pubs that all require the same value of ``shots``."""
        preprocessed_data = []
        flat_circuits = []
        for pub in pubs:
            data = self._preprocess_pub(pub)
            preprocessed_data.append(data)
            flat_circuits.extend(data.circuits)

        run_result, metadata = _run_circuits(
            flat_circuits,
            self._backend,
            shots=shots,
            seed_simulator=self._options.seed_simulator,
            session_id=self._session_id,
        )
        counts = _prepare_counts(run_result)

        results = []
        start = 0
        for pub, data in zip(pubs, preprocessed_data):
            end = start + len(data.circuits)
            expval_map = self._calc_expval_map(counts[start:end], metadata[start:end])
            start = end
            results.append(self._postprocess_pub(pub, expval_map, data, shots))

        return results
