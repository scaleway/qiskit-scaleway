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
from typing import Union

from abc import ABC
from qiskit.providers import BackendV2 as Backend
from pytimeparse.timeparse import timeparse

from ..utils import QaaSClient


class ScalewayBackend(Backend, ABC):
    def __init__(
        self,
        provider,
        client: QaaSClient,
        backend_id: str,
        name: str,
        availability: str,
        version: str,
    ):
        super().__init__(provider=provider, backend_version=version, name=name)

        self._backend_id = backend_id
        self._availability = availability
        self._client = client

    @property
    def id(self):
        return self._backend_id

    @property
    def availability(self):
        return self._availability

    def start_session(
        self,
        name: str = None,
        deduplication_id: str = None,
        max_duration: Union[int, str] = None,
        max_idle_duration: Union[int, str] = None,
    ) -> str:
        if name is None:
            name = self._options.session_name

        if deduplication_id is None:
            deduplication_id = self._options.session_deduplication_id

        if max_duration is None:
            max_duration = self._options.session_max_duration

        if max_idle_duration is None:
            max_idle_duration = self._options.session_max_idle_duration

        if isinstance(max_duration, str):
            max_duration = f"{timeparse(max_duration)}s"

        if isinstance(max_idle_duration, str):
            max_idle_duration = f"{timeparse(max_idle_duration)}s"

        return self._client.create_session(
            name,
            platform_id=self.id,
            deduplication_id=deduplication_id,
            max_duration=max_duration,
            max_idle_duration=max_idle_duration,
        )

    def stop_session(self, session_id: str):
        self._client.terminate_session(
            session_id=session_id,
        )

    def delete_session(self, session_id: str):
        self._client.delete_session(
            session_id=session_id,
        )
