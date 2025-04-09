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
from typing import Optional, List, Dict

from qiskit.providers.providerutils import filter_backends

from qiskit_scaleway.api import QaaSClient, QaaSPlatform
from qiskit_scaleway.backends import BaseBackend


class ScalewayProvider:
    """
    :param project_id: optional UUID of the Scaleway Project, if the provided ``project_id`` is None, the value is loaded from the SCALEWAY_PROJECT_ID variables in the dotenv file or the QISKIT_SCALEWAY_PROJECT_ID environment variables

    :param secret_key: optional authentication token required to access the Scaleway API, if the provided ``secret_key`` is None, the value is loaded from the SCALEWAY_API_TOKEN variables in the dotenv file or the QISKIT_SCALEWAY_API_TOKEN environment variables

    :param url: optional value, endpoint URL of the API, if the provided ``url`` is None, the value is loaded from the SCALEWAY_API_URL variables in the dotenv file or the QISKIT_SCALEWAY_API_URL environment variables, if no url is found, then ``_ENDPOINT_URL`` is used.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        url: Optional[str] = None,
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

        api_url = url or env_api_url

        self.__client = QaaSClient(url=api_url, token=token, project_id=project_id)

    def get_backend(self, name=None, **kwargs):
        """Return a single backend matching the specified filtering.

        Args:
            name (str): name of the backend.
            **kwargs: dict used for filtering.

        Returns:
            Backend: a backend matching the filtering.

        Raises:
            Exception: if no backend could be found or
                more than one backend matches the filtering criteria.
        """
        backends = self.backends(name, **kwargs)
        if len(backends) > 1:
            raise Exception("More than one backend matches the criteria")
        if not backends:
            raise Exception("No backend matches the criteria")

        return backends[0]

    def backends(self, name: Optional[str] = None, **kwargs) -> List[BaseBackend]:
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

        platforms = self.__client.list_platforms(name=name)

        for platform in platforms:
            if platform.backend_name == "aer":
                scaleway_backends.append(self._create_aer_backend(platform))
            elif platform.backend_name == "qsim":
                scaleway_backends.append(self._create_qsim_backend(platform))
            elif platform.provider_name == "aqt":
                scaleway_backends.append(self._create_aqt_backend(platform))
        if filters is not None:
            scaleway_backends = self.filters(scaleway_backends, filters)

        return filter_backends(scaleway_backends, **kwargs)

    def filters(self, backends: List[BaseBackend], filters: Dict) -> List[BaseBackend]:
        operational = filters.get("operational")
        min_num_qubits = filters.get("min_num_qubits")

        if operational is not None:
            backends = [
                b for b in backends if b.availability in ["available", "scarce"]
            ]

        if min_num_qubits is not None:
            backends = [b for b in backends if b.num_qubits >= min_num_qubits]

        return backends

    def _create_aqt_backend(self, platform: QaaSPlatform) -> BaseBackend:
        try:
            from qiskit_scaleway.backends.aqt import AqtBackend
        except:
            raise Exception(
                "Could not import aqt backend. You must install `qiskit_scaleway[aqt]` package"
            )

        return AqtBackend(
            provider=self,
            client=self.__client,
            platform=platform,
        )

    def _create_qsim_backend(self, platform: QaaSPlatform) -> BaseBackend:
        from qiskit_scaleway.backends.qsim import QsimBackend

        return QsimBackend(
            provider=self,
            client=self.__client,
            platform=platform,
        )

    def _create_aer_backend(self, platform: QaaSPlatform) -> BaseBackend:
        try:
            from qiskit_scaleway.backends.aer import AerBackend
        except:
            raise Exception(
                "Could not import aqt backend. You must install `qiskit_scaleway[aer]` package"
            )

        return AerBackend(
            provider=self,
            client=self.__client,
            platform=platform,
        )
