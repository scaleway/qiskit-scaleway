import httpx

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
        self._session = None
        self._project_id = project_id
        self._url = url
        self._secret_key = secret_key

        self._client = ScalewayClient(url=url, token=secret_key, project_id=project_id)

    @property
    def url(self) -> str:
        return self._url

    @property
    def project_id(self) -> str:
        return self._project_id

    @property
    def session(self) -> str | None:
        return self._session

    @property
    def secret_key(self) -> str:
        return self._secret_key

    def backends(self, name=None, session=None, **kwargs) -> list[ScalewayBackend]:
        """Return a list of backends matching the specified filtering.

        Args:
            name (str): name of the backend.

        Returns:
            list[ScalewayBackend]: a list of Backends that match the filtering
                criteria.
        """
        self._session = session

        scaleway_backends = []
        json_resp = self._client.list_platforms(name)

        for platform in json_resp["platforms"]:
            scaleway_backends.append(
                ScalewayBackend(
                    provider=self,
                    platform_id=platform.get("id"),
                    name=platform.get("name"),
                    version=platform.get("version"),
                    num_qubits=platform.get("max_qubit_count"),
                )
            )

        return filter_backends(scaleway_backends, **kwargs)
