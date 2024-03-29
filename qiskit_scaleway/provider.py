# import httpx

from qiskit.providers import ProviderV1 as Provider
from qiskit.providers.providerutils import filter_backends

from .backend import ScalewayBackend
from .client import ScalewayClient


_ENDPOINT_URL = "https://api.scaleway.com/qaas/v1alpha1"


class ScalewayProvider(Provider):
    """
    :param project_id: UUID of the Scaleway Project

    :param secret_key: authentication token required to access the Scaleway API

    :param url: optional value, endpoint URL of the API
    """

    def __init__(
        self, project_id: str, secret_key: str, url: str = _ENDPOINT_URL
    ) -> None:
        # self.__session = None
        self.__project_id = project_id
        self.__url = url
        # self.__secret_key = secret_key

        self.__client = ScalewayClient(url=url, token=secret_key, project_id=project_id)

    @property
    def url(self) -> str:
        return self.__url

    @property
    def project_id(self) -> str:
        return self.__project_id

    # @property
    # def session(self) -> str | None:
    #     return self.__session

    # @property
    # def secret_key(self) -> str:
    #     return self.__secret_key

    def backends(self, name: str = None, **kwargs) -> list[ScalewayBackend]:
        """Return a list of backends matching the specified filtering.

        Args:
            name (str): name of the backend.

        Returns:
            list[ScalewayBackend]: a list of Backends that match the filtering
                criteria.
        """
        # self._session = session

        scaleway_backends = []
        json_resp = self.__client.list_platforms(name)

        for platform in json_resp["platforms"]:
            scaleway_backends.append(
                ScalewayBackend(
                    provider=self,
                    client=self.__client,
                    platform_id=platform.get("id"),
                    name=platform.get("name"),
                    version=platform.get("version"),
                    num_qubits=platform.get("max_qubit_count"),
                )
            )

        return filter_backends(scaleway_backends, **kwargs)
