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
from qiskit.primitives import BackendSamplerV2


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
