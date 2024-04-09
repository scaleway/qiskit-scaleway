from qiskit_aer.primitives import Sampler as AerSampler
from ..backends import AerBackend


class Sampler(AerSampler):
    def __init__(
        self,
        backend: AerBackend,
        *,
        transpile_options: dict | None = None,
        run_options: dict | None = None,
        skip_transpilation: bool = False,
    ):
        super().__init__(
            backend_options=None,
            transpile_options=transpile_options,
            run_options=run_options,
            skip_transpilation=skip_transpilation,
        )

        self._backend = backend
