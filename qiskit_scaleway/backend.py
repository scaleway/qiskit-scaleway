from qiskit.providers import BackendV2 as Backend
from qiskit.transpiler import Target
from qiskit.providers import Options
from qiskit.circuit import Parameter, Measure
from qiskit.circuit.library import PhaseGate, SXGate, UGate, CXGate, IGate
from qiskit.providers.models import BackendConfiguration
from qiskit.converters import circuit_to_dag


from .job import ScalewayJob


class ScalewayBackend(Backend):

    def __init__(
        self, provider, platform_id: str, name: str, version: str, num_qubits: int
    ):
        super().__init__(provider=provider, backend_version=version, name=name)

        self._platform_id = platform_id
        self._options = self._default_options()
        self._name = name
        self._version = version

        # Create Target
        self._target = Target("Target for Scaleway Backend")
        self._target.num_qubits = num_qubits

        # Instead of None for this and below instructions you can define
        # a qiskit.transpiler.InstructionProperties object to define properties
        # for an instruction.
        # TODO: fix https://docs.quantum.ibm.com/api/qiskit/dev/providers
        lam = Parameter("λ")
        p_props = {(qubit,): None for qubit in range(5)}
        self._target.add_instruction(PhaseGate(lam), p_props)

        sx_props = {(qubit,): None for qubit in range(5)}
        self._target.add_instruction(SXGate(), sx_props)

        phi = Parameter("φ")
        theta = Parameter("ϴ")
        u_props = {(qubit,): None for qubit in range(5)}
        self._target.add_instruction(UGate(theta, phi, lam), u_props)

        cx_props = {edge: None for edge in [(0, 1), (1, 2), (2, 3), (3, 4)]}
        self._target.add_instruction(CXGate(), cx_props)

        meas_props = {(qubit,): None for qubit in range(5)}
        self._target.add_instruction(Measure(), meas_props)

        id_props = {(qubit,): None for qubit in range(5)}
        self._target.add_instruction(IGate(), id_props)

        # Set option validators
        self.options.set_validator("shots", (1, 4096))
        self.options.set_validator("memory", bool)

    @property
    def target(self):
        return self._target

    @property
    def platform_id(self):
        return self._platform_id

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits the backend has."""
        return self.target.num_qubits

    @property
    def max_circuits(self):
        return 1024

    @classmethod
    def _default_options(self):
        return Options(shots=1024, memory=False)

    def run(self, circuits, **kwargs):

        if not isinstance(circuits, list):
            circuits = [circuits]

        valid_options = {
            key: value for key, value in kwargs.items() if key in self.options
        }
        unknown_options = set(kwargs) - set(valid_options)

        if unknown_options:
            for unknown_option in unknown_options:
                warnings.warn(
                    f"Option {unknown_option} is not used by this backend",
                    UnknownOptionWarning,
                    stacklevel=2,
                )

        job_config = {}
        for kwarg in kwargs:
            if not hasattr(self.options, kwarg):
                warnings.warn(
                    "Option %s is not used by this backend" % kwarg,
                    UserWarning,
                    stacklevel=2,
                )
            else:
                job_config[kwarg] = kwargs[kwarg]
        if "shots" not in job_config:
            job_config["shots"] = self.options.shots

        job = ScalewayJob(
            backend=self, job_id=None, circuits=circuits, config=job_config
        )
        job.submit()
        return job
