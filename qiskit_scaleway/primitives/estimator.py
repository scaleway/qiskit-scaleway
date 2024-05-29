from qiskit.primitives import BackendEstimatorV2
from ..backends import AerBackend


class Estimator(BackendEstimatorV2):
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
