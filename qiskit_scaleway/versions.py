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
import importlib.metadata
import platform

from typing import Final

QISKIT_VERSION: Final = importlib.metadata.version("qiskit")
QISKIT_SCALEWAY_PROVIDER_VERSION: Final = importlib.metadata.version("qiskit-scaleway")

__version__: Final = QISKIT_SCALEWAY_PROVIDER_VERSION

USER_AGENT: Final = " ".join(
    [
        f"qiskit-scaleway/{QISKIT_SCALEWAY_PROVIDER_VERSION}",
        f"({platform.system()}; {platform.python_implementation()}/{platform.python_version()})",
        f"qiskit/{QISKIT_VERSION}",
    ]
)
