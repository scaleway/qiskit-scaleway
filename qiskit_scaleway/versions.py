import importlib.metadata
import platform

from typing import Final

QISKIT_VERSION: Final = importlib.metadata.version("qiskit")
QISKIT_SCALEWAY_PROVIDER_VERSION: Final = importlib.metadata.version("qiskit-scaleway")

__version__: Final = QISKIT_SCALEWAY_PROVIDER_VERSION

USER_AGENT: Final = " ".join(
    [
        f"qiskit-scaleway/{QISKIT_SCALEWAY_PROVIDER_VERSION}",
        f"({platform.system()}; {platform.python_implementation()}/{platform.python_version()})",
        f"qiskit/{QISKIT_VERSION}",
    ]
)
