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

import io
from setuptools import setup, find_packages

description = "A Qiskit package to connect to Scaleway Quantum as a Service"
long_description = io.open("README.md", encoding="utf-8").read()
requirements = open("requirements.txt").readlines()
requirements = [r.strip() for r in requirements]

setup(
    name="qiskit_scaleway",
    version="0.2.8",
    project_urls={
        "Documentation": "https://www.scaleway.com/en/quantum-as-a-service/",
        "Source": "https://github.com/scaleway/qiskit-scaleway",
        "Tracker": "https://github.com/scaleway/qiskit-scaleway/issues",
    },
    author="The Scaleway Developers",
    author_email="vmacheret@scaleway.com",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=(">=3.12.0"),
    license="Apache 2",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
)
