from qiskit.providers import ProviderV1 as Provider
from qiskit.providers.providerutils import filter_backends


class ScalewayProvider(Provider):

    """
    :param project_id: UUID of the Scaleway Project

    :param secret_key: authentication token required to access the Scaleway API

    """

    def __init__(
        self,
        project_id: str,
        secret_key: str,
    ) -> None:
        self.project_id = project_id
        self.secret_key = secret_key

    def backends(self, name=None, **kwargs):
        pass
