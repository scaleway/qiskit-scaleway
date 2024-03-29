import randomname
import warnings

from typing import Union, List

from qiskit.providers import BackendV2 as Backend
from qiskit.transpiler import Target
from qiskit.providers import Options
from qiskit.circuit import Parameter, Measure, QuantumCircuit
from qiskit.circuit.library import PhaseGate, SXGate, UGate, CXGate, IGate

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

        self._platform_id = platform_id
        self._options = self._default_options()
        self._client = client

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
    def id(self):
        return self._platform_id

    @property
    def num_qubits(self) -> int:
        return self._target.num_qubits

    @property
    def max_circuits(self):
        return 1024

    def start_session(
        self,
        name: str = None,
        deduplication_id: str = None,
        max_duration: Union[int, str] = None,
        max_idle_duration: Union[int, str] = None,
    ) -> str:
        if name is None:
            name = self._options.session_name

        if deduplication_id is None:
            deduplication_id = self._options.session_deduplication_id

        if max_duration is None:
            max_duration = self._options.session_max_duration

        if max_idle_duration is None:
            max_idle_duration = self._options.session_max_idle_duration

        return self._client.create_session(
            name,
            platform_id=self.id,
            deduplication_id=deduplication_id,
            max_duration=max_duration,
            max_idle_duration=max_idle_duration,
        )

    def stop_session(self, id: str):
        self._client.terminate_session(
            session_id=id,
        )

    def delete_session(self, id: str):
        self._client.delete_session(
            session_id=id,
        )

    def run(self, circuits: Union[QuantumCircuit, List[QuantumCircuit]], **kwargs):
        if not isinstance(circuits, list):
            circuits = [circuits]

        valid_options = {
            key: value for key, value in kwargs.items() if key in self._options
        }
        unknown_options = set(kwargs) - set(valid_options)

        if unknown_options:
            for unknown_option in unknown_options:
                warnings.warn(
                    f"Option {unknown_option} is not used by this backend",
                    UserWarning,
                    stacklevel=2,
                )

        job_config = {}
        for kwarg in kwargs:
            if not hasattr(self.options, kwarg):
                warnings.warn(
                    f"Option {kwarg} is not used by this backend",
                    UserWarning,
                    stacklevel=2,
                )
            else:
                job_config[kwarg] = kwargs[kwarg]

        if "shots" not in job_config:
            job_config["shots"] = self._options.shots

        job_name = f"qj-aer-{randomname.get_name()}"

        job = ScalewayJob(
            backend=self,
            client=self._client,
            circuits=circuits,
            config=job_config,
            name=job_name,
        )

        session_id = job_config.get("session_id", None)

        if session_id in ["auto", None]:
            session_id = self.start_session(name=f"auto-{self._options.session_name}")

        job.submit(session_id)

        return job

    @classmethod
    def _default_options(self):
        return Options(
            session_id="auto",
            session_name="qiskit-scaleway-session",
            session_deduplication_id="qiskit-scaleway-session",
            session_max_duration="1200s",
            session_max_idle_duration="1200s",
            shots=1000,
            memory=False,
            method="automatic",
        )
