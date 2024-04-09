import warnings

from qiskit.providers import ProviderV1 as Provider
from qiskit.providers.providerutils import filter_backends

from .backends import ScalewayBackend, AerBackend, QsimBackend
from .utils import QaaSClient


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
        self.__client = QaaSClient(url=url, token=secret_key, project_id=project_id)

    def backends(self, name: str = None, **kwargs) -> list[ScalewayBackend]:
        """Return a list of backends matching the specified filtering.

        Args:
            name (str): name of the backend.

        Returns:
            list[ScalewayBackend]: a list of Backends that match the filtering
                criteria.
        """

        scaleway_backends = []
        json_resp = self.__client.list_platforms(name)

        for platform_dict in json_resp["platforms"]:
            name = platform_dict.get("name")
            backend = None

            if name.startswith("aer"):
                backend = AerBackend(
                    provider=self,
                    client=self.__client,
                    backend_id=platform_dict.get("id"),
                    name=name,
                    version=platform_dict.get("version"),
                    num_qubits=platform_dict.get("max_qubit_count"),
                    metadata=platform_dict.get("metadata", None),
                )
            elif name.startswith("qsim"):
                backend = QsimBackend(
                    provider=self,
                    client=self.__client,
                    backend_id=platform_dict.get("id"),
                    name=name,
                    version=platform_dict.get("version"),
                    num_qubits=platform_dict.get("max_qubit_count"),
                    metadata=platform_dict.get("metadata", None),
                )

            if backend is None:
                warnings.warn(
                    f"Backend {name} was not created successfully",
                    UserWarning,
                    stacklevel=2,
                )

                continue

            scaleway_backends.append(backend)

        return filter_backends(scaleway_backends, **kwargs)
