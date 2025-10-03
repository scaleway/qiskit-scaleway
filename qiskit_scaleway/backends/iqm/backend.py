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
from qiskit.providers import Options

from qiskit_scaleway.backends import BaseBackend
from qiskit_scaleway.backends.iqm.move_gate import MoveGate
from qiskit_scaleway.utils import create_target_from_platform

from scaleway_qaas_client.v1alpha1 import QaaSClient, QaaSPlatform


class IqmBackend(BaseBackend):
    def __init__(self, provider, client: QaaSClient, platform: QaaSPlatform):
        super().__init__(
            provider=provider,
            client=client,
            platform=platform,
        )

        self._options = self._default_options()

        self._platform = platform
        self._target = create_target_from_platform(
            self._platform, additional_gates={"move": MoveGate()}
        )

        self._options.max_shots = platform.max_shot_count
        self._options.set_validator("shots", (1, platform.max_shot_count))

    def __repr__(self) -> str:
        return f"<IqmBackend(name={self.name},num_qubits={self.num_qubits},platform_id={self.id})>"

    @property
    def target(self):
        return self._target

    @classmethod
    def _default_options(self):
        return Options(
            session_id="auto",
            session_name="qs-qiskit-iqm",
            session_deduplication_id="qs-qiskit-iqm",
            session_max_duration="59h",
            session_max_idle_duration="59m",
            shots=1000,
        )
