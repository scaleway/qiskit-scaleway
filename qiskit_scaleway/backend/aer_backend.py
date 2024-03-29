import randomname
import warnings

from typing import Union, List

from qiskit.transpiler import Target
from qiskit.providers import Options
from qiskit.circuit import Parameter, Measure, QuantumCircuit
from qiskit.circuit.library import PhaseGate, SXGate, UGate, CXGate, IGate

from .aer_job import AerJob
from .scaleway_backend import ScalewayBackend
from ..utils import QaaSClient


class AerBackend(ScalewayBackend):
    def __init__(
        self,
        provider,
        client: QaaSClient,
        backend_id: str,
        name: str,
        version: str,
        num_qubits: int,
    ):
        super().__init__(
            provider=provider,
            client=client,
            backend_id=backend_id,
            name=name,
            version=version,
        )

        self._options = self._default_options()

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
    def num_qubits(self) -> int:
        return self._target.num_qubits

    @property
    def max_circuits(self):
        return 1024

    def run(self, circuits: Union[QuantumCircuit, List[QuantumCircuit]], **kwargs):
        if not isinstance(circuits, list):
            circuits = [circuits]

        job_config = {key: value for key, value in self._options.items()}

        for kwarg in kwargs:
            if not hasattr(self.options, kwarg):
                warnings.warn(
                    f"Option {kwarg} is not used by this backend",
                    UserWarning,
                    stacklevel=2,
                )
            else:
                job_config[kwarg] = kwargs[kwarg]

        job_name = f"qj-aer-{randomname.get_name()}"

        job_config.pop("session_id")
        job_config.pop("session_name")
        job_config.pop("session_deduplication_id")
        job_config.pop("session_max_duration")
        job_config.pop("session_max_idle_duration")

        job = AerJob(
            backend=self,
            client=self._client,
            circuits=circuits,
            config=job_config,
            name=job_name,
        )

        session_id = job_config.get("session_id", None)

        if session_id in ["auto", None]:
            session_id = self.start_session(name=f"auto-{self._options.session_name}")
            assert session_id is not None

        job.submit(session_id)

        return job

    @classmethod
    def _default_options(self):
        # https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html
        return Options(
            session_id="auto",
            session_name="qiskit-scaleway-session",
            session_deduplication_id="qiskit-scaleway-session",
            session_max_duration="1200s",
            session_max_idle_duration="1200s",
            shots=1000,
            memory=False,
            method="automatic",
            precision="double",
            max_shot_size=None,
            enable_truncation=True,
            zero_threshold=1e-10,
            validation_threshold=1e-8,
            max_parallel_threads=0,
            max_parallel_shots=0,
            max_parallel_experiments=1,
            blocking_enable=True,
            blocking_qubits=0,
            batched_shots_gpu=False,
            chunk_swap_buffer_qubits=15,
            batched_shots_gpu_max_qubits=16,
            num_threads_per_device=1,
            shot_branching_enable=False,
            shot_branching_sampling_enable=False,
            accept_distributed_results=None,
            runtime_parameter_bind_enable=False,
            statevector_parallel_threshold=14,
            statevector_sample_measure_opt=10,
            stabilizer_max_snapshot_probabilities=32,
            extended_stabilizer_sampling_method="resampled_metropolis",
            extended_stabilizer_metropolis_mixing_time=5000,
            extended_stabilizer_approximation_error=0.05,
            extended_stabilizer_norm_estimation_samples=100,
            extended_stabilizer_norm_estimation_repetitions=3,
            extended_stabilizer_parallel_threshold=100,
            extended_stabilizer_probabilities_snapshot_samples=3000,
            matrix_product_state_max_bond_dimension=None,
            matrix_product_state_truncation_threshold=1e-16,
            mps_sample_measure_algorithm="mps_apply_measure",
            mps_log_data=False,
            mps_swap_direction="mps_swap_left",
            chop_threshold=1e-8,
            mps_parallel_threshold=14,
            mps_omp_threads=1,
            tensor_network_num_sampling_qubits=10,
            use_cuTensorNet_autotuning=False,
            fusion_enable=True,
            fusion_verbose=False,
            fusion_max_qubit=None,
            fusion_threshold=None,
        )
