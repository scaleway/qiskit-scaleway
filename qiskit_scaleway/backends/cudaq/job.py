# Copyright 2026 Scaleway
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
from typing import (
    List,
    Union,
    Dict,
)

from qiskit import QuantumCircuit

from qiskit_scaleway.versions import USER_AGENT
from qiskit_scaleway.backends import BaseJob

from qio.core import (
    QuantumProgram,
    QuantumProgramSerializationFormat,
    QuantumProgramResult,
    QuantumComputationModel,
    QuantumComputationParameters,
    BackendData,
    ClientData,
)

from scaleway_qaas_client.v1alpha1 import QaaSClient


class CudaqJob(BaseJob):
    def __init__(
        self,
        name: str,
        backend,
        client: QaaSClient,
        circuits: Union[List[QuantumCircuit], QuantumCircuit],
        config: Dict,
    ) -> None:
        super().__init__(
            name=name, backend=backend, client=client, config=config, circuits=circuits
        )

    def submit(self, session_id: str) -> None:
        if self._job_id:
            raise RuntimeError(f"Job already submitted (ID: {self._job_id})")

        options = self._config.copy()

        programs = [
            QuantumProgram.from_qiskit_circuit(
                self._circuits[0], QuantumProgramSerializationFormat.QASM_V2
            )
        ]

        # Retrieve run options
        shots = options.pop("shots")
        cudaq_options = {"cudaq_target_options": options.pop("options", "")}

        backend_data = BackendData(
            name=self.backend().name,
            version=self.backend().version,
            options=options,
        )

        client_data = ClientData(
            user_agent=USER_AGENT,
        )

        computation_model_json = QuantumComputationModel(
            programs=programs,
            backend=backend_data,
            client=client_data,
        ).to_json_str()

        computation_parameters_json = QuantumComputationParameters(
            shots=shots,
            options=cudaq_options,
        ).to_json_str()

        model = self._client.create_model(
            payload=computation_model_json,
        )

        if not model:
            raise RuntimeError("Failed to push circuit data")

        self._job_id = self._client.create_job(
            name=self._name,
            session_id=session_id,
            model_id=model.id,
            parameters=computation_parameters_json,
        ).id
