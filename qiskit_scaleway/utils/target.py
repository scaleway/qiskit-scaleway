from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import List

from qiskit.transpiler import Target
from qiskit.circuit.library import get_standard_gate_name_mapping

from scaleway_qaas_client.v1alpha1 import QaaSPlatform


@dataclass_json
@dataclass
class _QiskitInstructionData:
    name: str
    params: List[str] = field(default=None)


@dataclass_json
@dataclass
class _QiskitTargetData:
    instructions: List[_QiskitInstructionData]


@dataclass_json
@dataclass
class _QiskitClientData:
    target: _QiskitTargetData


@dataclass_json
@dataclass
class _PlatformMetadata:
    qiskit: _QiskitClientData


def create_target_from_platform(platform: QaaSPlatform) -> Target:
    target = Target(num_qubits=platform.max_qubit_count)

    if not platform.metadata:
        return target

    metadata = _PlatformMetadata.from_json(platform.metadata)

    if not metadata:
        return target

    instructions = metadata.qiskit.target.instructions

    if not instructions:
        return target

    qiskit_gate_mapping = get_standard_gate_name_mapping()

    for instruction in instructions:
        qiskit_instruction = qiskit_gate_mapping.get(instruction.name)

        if not qiskit_instruction:
            raise Exception("could not find instruction:", instruction.name)

        target.add_instruction(qiskit_instruction)

    return target
