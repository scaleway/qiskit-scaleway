# Copyright 2024 Scaleway
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import randomname
import warnings

from typing import Union, List

from qiskit.providers import Options
from qiskit.circuit import QuantumCircuit
from qiskit.providers import convert_to_target

from qiskit_aer.backends.aer_simulator import BASIS_GATES, AerBackendConfiguration
from qiskit_aer.backends.aerbackend import NAME_MAPPING

from qiskit_scaleway.backends.aer.aer_job import AerJob
from qiskit_scaleway.backends import BaseBackend
from qiskit_scaleway.api import QaaSClient, QaaSPlatform


class AerBackend(BaseBackend):
    def __init__(self, provider, client: QaaSClient, platform: QaaSPlatform):
        super().__init__(
            provider=provider,
            client=client,
            platform=platform,
        )

        self._options = self._default_options()

        self._configuration = AerBackendConfiguration.from_dict(
            {
                "open_pulse": False,
                "backend_name": platform.name,
                "backend_version": platform.version,
                "n_qubits": platform.max_qubit_count,
                "url": "https://github.com/Qiskit/qiskit-aer",
                "simulator": True,
                "local": False,
                "conditional": True,
                "memory": True,
                "max_shots": platform.max_shot_count,
                "description": "A C++ Qasm simulator with noise",
                "coupling_map": None,
                "basis_gates": BASIS_GATES["automatic"],
                "gates": [],
            }
        )
        self._properties = None
        self._target = convert_to_target(
            self._configuration, self._properties, None, NAME_MAPPING
        )

    def __repr__(self) -> str:
        return f"<AerBackend(name={self.name},num_qubits={self.num_qubits},platform_id={self.id})>"

    @property
    def target(self):
        return self._target

    @property
    def num_qubits(self) -> int:
        return self._target.num_qubits

    @property
    def max_circuits(self):
        return 1024

    def run(
        self, circuits: Union[QuantumCircuit, List[QuantumCircuit]], **run_options
    ) -> AerJob:
        if not isinstance(circuits, list):
            circuits = [circuits]

        job_config = dict(self._options.items())

        for kwarg in run_options:
            if not hasattr(self.options, kwarg):
                warnings.warn(
                    f"Option {kwarg} is not used by this backend",
                    UserWarning,
                    stacklevel=2,
                )
            else:
                job_config[kwarg] = run_options[kwarg]

        job_name = f"qj-aer-{randomname.get_name()}"

        session_id = job_config.get("session_id", None)

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
            session_name="aer-session-from-qiskit",
            session_deduplication_id="aer-session-from-qiskit",
            session_max_duration="1h",
            session_max_idle_duration="20m",
            shots=1000,
            memory=False,
            seed_simulator=None,
            method="automatic",
            precision="double",
            max_shot_size=None,
            enable_truncation=True,
            max_parallel_experiments=1,
            zero_threshold=1e-10,
            validation_threshold=1e-8,
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
