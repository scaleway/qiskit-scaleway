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
import os

from dotenv import dotenv_values

from qiskit.providers import ProviderV1 as Provider
from qiskit.providers.providerutils import filter_backends

from .backends import ScalewayBackend, AerBackend, QsimBackend
from .utils import QaaSClient


_ENDPOINT_URL = "https://api.scaleway.com/qaas/v1alpha1"


class ScalewayProvider(Provider):
    """
    :param project_id: optional UUID of the Scaleway Project, if the provided ``project_id`` is None, the value is loaded from the SCALEWAY_PROJECT_ID variables in the dotenv file or the QISKIT_SCALEWAY_PROJECT_ID environment variables

    :param secret_key: optional authentication token required to access the Scaleway API, if the provided ``secret_key`` is None, the value is loaded from the SCALEWAY_API_TOKEN variables in the dotenv file or the QISKIT_SCALEWAY_API_TOKEN environment variables

    :param url: optional value, endpoint URL of the API, if the provided ``url`` is None, the value is loaded from the SCALEWAY_API_URL variables in the dotenv file or the QISKIT_SCALEWAY_API_URL environment variables, if no url is found, then ``_ENDPOINT_URL`` is used.
    """

    def __init__(
        self, project_id: str = None, secret_key: str = None, url: str = None
    ) -> None:
        env_token = dotenv_values().get("QISKIT_SCALEWAY_API_TOKEN") or os.getenv(
            "QISKIT_SCALEWAY_API_TOKEN"
        )
        env_project_id = dotenv_values().get("QISKIT_SCALEWAY_PROJECT_ID") or os.getenv(
            "QISKIT_SCALEWAY_PROJECT_ID"
        )
        env_api_url = dotenv_values().get("QISKIT_SCALEWAY_API_URL") or os.getenv(
            "QISKIT_SCALEWAY_API_URL"
        )

        token = secret_key or env_token
        if token is None:
            raise Exception("secret_key is missing")

        project_id = project_id or env_project_id
        if project_id is None:
            raise Exception("project_id is missing")

        api_url = url or env_api_url or _ENDPOINT_URL

        self.__client = QaaSClient(url=api_url, token=token, project_id=project_id)

    def backends(self, name: str = None, **kwargs) -> list[ScalewayBackend]:
        """Return a list of backends matching the specified filtering.

        Args:
            name (str): name of the backend.

        Returns:
            list[ScalewayBackend]: a list of Backends that match the filtering
                criteria.
        """

        scaleway_backends = []
        filters = {}

        if kwargs.get("operational") is not None:
            filters["operational"] = kwargs.pop("operational", None)

        if kwargs.get("min_num_qubits") is not None:
            filters["min_num_qubits"] = kwargs.pop("min_num_qubits", None)

        json_resp = self.__client.list_platforms(name)

        for platform_dict in json_resp["platforms"]:
            name = platform_dict.get("name")

            if name.startswith("aer"):
                scaleway_backends.append(AerBackend(
                    provider=self,
                    client=self.__client,
                    backend_id=platform_dict.get("id"),
                    name=name,
                    availability=platform_dict.get("availability"),
                    version=platform_dict.get("version"),
                    num_qubits=platform_dict.get("max_qubit_count"),
                    metadata=platform_dict.get("metadata"),
                ))
            elif name.startswith("qsim"):
                scaleway_backends.append(QsimBackend(
                    provider=self,
                    client=self.__client,
                    backend_id=platform_dict.get("id"),
                    name=name,
                    availability=platform_dict.get("availability"),
                    version=platform_dict.get("version"),
                    num_qubits=platform_dict.get("max_qubit_count"),
                    metadata=platform_dict.get("metadata"),
                ))

        if filters is not None:
            scaleway_backends = self.filters(scaleway_backends, filters)

        return filter_backends(scaleway_backends, **kwargs)

    def filters(
        self, backends: list[ScalewayBackend], filters: dict
    ) -> list[ScalewayBackend]:
        operational = filters.get("operational")
        min_num_qubits = filters.get("min_num_qubits")

        if operational is not None:
            backends = [
                b for b in backends if b.availability in ["available", "scarce"]
            ]

        if min_num_qubits is not None:
            backends = [b for b in backends if b.num_qubits >= min_num_qubits]

        return backends
