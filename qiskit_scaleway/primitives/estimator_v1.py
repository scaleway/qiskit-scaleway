# Copyright 2025 Scaleway
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
from qiskit.primitives import BackendEstimator


class Estimator(BackendEstimator):
    def __init__(
        self,
        backend,
        session_id: str,
        options: dict | None = None,
        abelian_grouping: bool = True,
        skip_transpilation: bool = False,
    ):
        if not session_id:
            raise Exception("session_id must be not None")

        self._session_id = session_id

        super().__init__(
            backend,
            bound_pass_manager=backend.get_pass_manager(),
            options=options,
            abelian_grouping=abelian_grouping,
            skip_transpilation=skip_transpilation,
        )

    def _run(self, circuits, observables, parameter_values, **run_options):
        run_options["session_id"] = self._session_id
        return super()._run(circuits, observables, parameter_values, **run_options)
