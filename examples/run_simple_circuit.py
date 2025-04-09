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
from qiskit import QuantumCircuit
from qiskit_scaleway import ScalewayProvider

provider = ScalewayProvider(
    project_id="<your-scaleway-project-id>",
    secret_key="<your-scaleway-secret-key>",
)

# Retrieve a backend by providing search criteria. The search must have a single match
backend = provider.get_backend("aer_simulation_2l4")

# Define a quantum circuit that produces a 4-qubit GHZ state.
qc = QuantumCircuit(4)
qc.h(0)
qc.cx(0, 1)
qc.cx(0, 2)
qc.cx(0, 3)
qc.measure_all()

# Create a QPU's session for a limited duration, a max_idle_duration can also be specified
session_id = backend.start_session(
    deduplication_id="my-aer-session-workshop", max_duration="2h"
)

# Create and send a job to the target session
result = backend.run(qc, shots=1000, session_id=session_id).result()

if result.success:
    print(result.get_counts())
else:
    print(result.to_dict()["error"])

# Revoke manually the QPU's session if needed
# If not done, will be revoked automatically after `max_duration`
backend.stop_session(session_id)
