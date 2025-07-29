# Copyright 2025 Scaleway
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
from qiskit import transpile
from qiskit.quantum_info import random_hermitian
from qiskit.circuit.library import IQP

from qiskit_scaleway import ScalewayProvider
from qiskit_scaleway.primitives import Sampler

import numpy as np

provider = ScalewayProvider(
    project_id="<your-scaleway-project-id>",
    secret_key="<your-scaleway-secret-key>",
)

# Create a Aer compatible backend
backend = provider.get_backend("aer_simulation_2l4")

# Start a session to run further jobs
session_id = backend.start_session(deduplication_id="my-sampler", max_duration="20m")

# Buildup the sampler
sampler = Sampler(backend=backend, session_id=session_id)

n_qubits = 5
circuit = IQP(np.real(random_hermitian(n_qubits, seed=1234)))
circuit.measure_all()

job = sampler.run([circuit], shots=100)
result = job.result()

print(f"> bitstrings: {result[0].data.meas.get_bitstrings()}")
print(f"> counts: {result[0].data.meas.get_counts()}")

backend.stop_session(session_id)
