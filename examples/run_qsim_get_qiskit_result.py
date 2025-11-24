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
from qiskit.visualization import plot_histogram

from qiskit import QuantumCircuit
from qiskit_scaleway import ScalewayProvider

provider = ScalewayProvider(
    project_id="<your-scaleway-project-id>",
    secret_key="<your-scaleway-secret-key>",
)

# Scaleway provides Qsim backend, whichs is compatible with Cirq SDK
backend = provider.get_backend("EMU-QSIM-L40S")

# Define a quantum circuit that produces a 4-qubit GHZ state.
qc = QuantumCircuit(4)
qc.h(0)
qc.cx(0, 1)
qc.cx(0, 2)
qc.cx(0, 3)
qc.measure_all()

# Create a QPU's session with Qsim installed for a limited duration
session_id = backend.start_session(
    deduplication_id="my-qsim-session-workshop", max_duration="2h"
)

# Create and send a job to the target session
qsim_job = backend.run(qc, shots=1000, session_id=session_id)

# Wait and get the Qiskit result
qiskit_result = qsim_job.result()

# Display the result
plot_histogram(qiskit_result.get_counts())

# Revoke manually the QPU's session if needed
# If not done, will be revoked automatically after `max_duration`
backend.stop_session(session_id)
