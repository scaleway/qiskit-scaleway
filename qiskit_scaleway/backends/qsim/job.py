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
from typing import (
    List,
    Union,
    Dict,
)

from qiskit import QuantumCircuit
from qiskit.providers import JobError, JobStatus
from qiskit.result import Result
from qiskit.transpiler.passes import RemoveBarriers

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


class QsimJob(BaseJob):
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

        # Note 1: Barriers are only visual elements
        # Barriers are not managed by Cirq deserialization
        # Note 2: Qsim can only handle one circuit at a time
        circuit = RemoveBarriers()(self._circuits[0])

        programs = [
            QuantumProgram.from_qiskit_circuit(
                circuit, QuantumProgramSerializationFormat.QASM_V2
            )
        ]

        options.pop("circuit_memoization_size")
        shots = options.pop("shots")

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

    def __to_cirq_result(self, program_result: QuantumProgramResult) -> "cirq.Result":
        try:
            import cirq
        except:
            raise Exception("Cannot get Cirq result: Cirq not installed")

        return program_result.to_cirq_result()

    def __to_qiskit_result(self, program_result: QuantumProgramResult) -> Result:
        return program_result.to_qiskit_result(
            backend_name=self.backend().name,
            backend_version=self.backend().version,
            job_id=self._job_id,
            qobj_id=", ".join(x.name for x in self._circuits),
            success=self.status() == JobStatus.DONE,
        )

    def result(
        self,
        timeout=None,
        fetch_interval: int = 3,
        format: str = "qiskit",
    ) -> Union[Result, List[Result], "cirq.Result"]:
        if self._job_id == None:
            raise JobError("Job ID error")

        match = {
            "qiskit": self.__to_qiskit_result,
            "cirq": self.__to_cirq_result,
        }

        job_results = self._wait_for_result(timeout, fetch_interval)

        conv_method = match.get(format, self.__to_qiskit_result)

        program_results = list(
            map(
                lambda r: conv_method(self._extract_payload_from_response(r)),
                job_results,
            )
        )

        if len(program_results) == 1:
            return program_results[0]

        return program_results
