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
from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class QaaSPlatform:
    id: str
    name: str
    metadata: str
    version: str
    max_qubit_count: int
    max_shot_count: int
    max_circuit_count: int
    availability: str
    type: str
    technology: str
    backend_name: str
    provider_name: str


@dataclass_json
@dataclass
class QaaSSession:
    id: str
    name: str
    status: str
    max_duration: str
    max_idle_duration: str


@dataclass_json
@dataclass
class QaaSJob:
    id: str
    name: str
    status: str


@dataclass_json
@dataclass
class QaaSJobResult:
    result: str
    url: str
