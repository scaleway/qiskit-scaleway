import abc

from typing import List
from qiskit_scaleway.backends import ScalewayBackend

from .scaleway_application_job import ScalewayApplicationJob
from ..utils import QaaSClient


class ScalewayApplication(abc.ABC):
    def __init__(self, client: QaaSClient):
        self._client = client

    def compatible_backends(self) -> List[ScalewayBackend]:
        pass

    def run(self, input, backend) -> ScalewayApplicationJob:
        pass
