import abc

from typing import List
from qiskit_scaleway.backends import ScalewayBackend

from .scaleway_application_job import ScalewayApplicationJob
from ..utils import QaaSClient


class ScalewayApplication(abc.ABC):
    def __init__(
        self, provider, client: QaaSClient, app_id: str, name: str, version: str
    ):
        self._provider = provider
        self._client = client
        self._app_id = app_id
        self._version = version
        self._name = name

    @property
    def id(self):
        return self._app_id

    @property
    def version(self):
        return self._version

    @property
    def name(self):
        return self._name

    def compatible_backends(self) -> List[ScalewayBackend]:
        app_dict = self._client.get_application(self._app_id)

        compatible_platform_ids = app_dict.get("compatible_platform_ids", [])
        compatible_backends = []

        for id in compatible_platform_ids:
            plt_dict = self._client.get_platform(id)
            compatible_backends.append(
                ScalewayBackend(
                    self._provider,
                    self._client,
                    id,
                    plt_dict.get("name"),
                    plt_dict.get("availability"),
                    plt_dict.get("version"),
                    plt_dict.get("max_qubit_count"),
                    plt_dict.get("metadata"),
                )
            )

    def run(self, input, backend) -> ScalewayApplicationJob:
        pass
