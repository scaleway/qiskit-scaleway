from qiskit.primitives import BackendSamplerV2
from ..backends import AerBackend


class Sampler(BackendSamplerV2):
    def __init__(
        self,
        backend: AerBackend,
        options: dict | None = None,
    ):
        if not isinstance(backend, AerBackend):
            raise Exception("backend must be instance of qiskit_scaleway.AerBackend")

        super().__init__(
            backend=backend,
            options=options,
        )
