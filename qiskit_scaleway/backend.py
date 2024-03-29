from typing import Union

from qiskit.providers import BackendV2 as Backend
from qiskit.transpiler import Target
from qiskit.providers import Options
from qiskit.circuit import Parameter, Measure
from qiskit.circuit.library import PhaseGate, SXGate, UGate, CXGate, IGate
from qiskit.providers.models import BackendConfiguration
from qiskit.converters import circuit_to_dag

from .job import ScalewayJob
from .client import ScalewayClient


class ScalewayBackend(Backend):
    def __init__(
        self,
        provider,
        client: ScalewayClient,
        platform_id: str,
        name: str,
        version: str,
        num_qubits: int,
    ):
        super().__init__(provider=provider, backend_version=version, name=name)

        self.__platform_id = platform_id
        self.__options = self._default_options()
        self.__name = name
        self.__version = version
        self.__client = client

        # Create Target
        self.__target = Target("Target for Scaleway Backend")
        self.__target.num_qubits = num_qubits

        # Instead of None for this and below instructions you can define
        # a qiskit.transpiler.InstructionProperties object to define properties
        # for an instruction.
        # TODO: fix https://docs.quantum.ibm.com/api/qiskit/dev/providers
        lam = Parameter("λ")
        p_props = {(qubit,): None for qubit in range(5)}
        self.__target.add_instruction(PhaseGate(lam), p_props)

        sx_props = {(qubit,): None for qubit in range(5)}
        self.__target.add_instruction(SXGate(), sx_props)

        phi = Parameter("φ")
        theta = Parameter("ϴ")
        u_props = {(qubit,): None for qubit in range(5)}
        self.__target.add_instruction(UGate(theta, phi, lam), u_props)

        cx_props = {edge: None for edge in [(0, 1), (1, 2), (2, 3), (3, 4)]}
        self.__target.add_instruction(CXGate(), cx_props)

        meas_props = {(qubit,): None for qubit in range(5)}
        self.__target.add_instruction(Measure(), meas_props)

        id_props = {(qubit,): None for qubit in range(5)}
        self.__target.add_instruction(IGate(), id_props)

        # Set option validators
        self.options.set_validator("shots", (1, 4096))
        self.options.set_validator("memory", bool)

    @property
    def name(self):
        return self.__name

    @property
    def version(self):
        return self.__version

    @property
    def target(self):
        return self.__target

    @property
    def id(self):
        return self.__platform_id

    @property
    def num_qubits(self) -> int:
        return self.__target.num_qubits

    @property
    def max_circuits(self):
        return 1024

    @classmethod
    def _default_options(self):
        return Options(session_id=None, shots=1024, memory=False)

    def start_session(
        self,
        name: str = None,
        deduplication_id: str = None,
        max_duration: Union[int, str] = "1200s",
        max_idle_duration: Union[int, str] = "1200s",
    ) -> str:
        if name is None:
            name = ""

        if deduplication_id is None:
            deduplication_id = name

        self.__client.create_session(
            name,
            platform_id=self.id,
            deduplication_id=deduplication_id,
            max_duration=max_duration,
            max_idle_duration=max_idle_duration,
        )

    def stop_session(self, id):
        pass

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
            job_config["shots"] = self.__options.shots

        job = ScalewayJob(
            backend=self,
            client=self.__client,
            job_id=None,
            circuits=circuits,
            config=job_config,
        )

        job.submit()

        return job
