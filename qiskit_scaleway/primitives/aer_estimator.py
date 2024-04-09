from qiskit_aer.primitives import Estimator as AerEstimator
from ..backends import AerBackend


class Estimator(AerEstimator):
    def __init__(
        self,
        backend: AerBackend,
        *,
        transpile_options: dict | None = None,
        run_options: dict | None = None,
        approximation: bool = False,
        skip_transpilation: bool = False,
        abelian_grouping: bool = True,
    ):
        super().__init__(
            backend_options=None,
            transpile_options=transpile_options,
            run_options=run_options,
            approximation=approximation,
            skip_transpilation=skip_transpilation,
            abelian_grouping=abelian_grouping,
        )

        self._backend = backend
