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
import httpx

from typing import List, Optional

from qiskit_scaleway.api.qaas_models import (
    QaaSPlatform,
    QaaSSession,
    QaaSJob,
    QaaSJobResult,
)

_DEFAULT_URL = "https://api.scaleway.com/qaas/v1alpha1"

_ENDPOINT_PLATFORM = "/platforms"
_ENDPOINT_SESSION = "/sessions"
_ENDPOINT_JOB = "/jobs"


class QaaSClient:
    def __init__(self, project_id: str, token: str, url: str):
        self.__token = token
        self.__url = url if url else _DEFAULT_URL
        self.__project_id = project_id

        self.__client = httpx.Client(
            headers={"X-Auth-Token": self.__token},
            base_url=self.__url,
            timeout=10.0,
            verify="https" in url,
        )

    def _build_endpoint(self, endpoint: str) -> str:
        return f"{self.__url}{endpoint}"

    @property
    def url(self):
        return self.__url

    def list_platforms(self, name: Optional[str]) -> List[QaaSPlatform]:
        filter_by_name = ""
        if name:
            filter_by_name = f"?name={name}"

        endpoint = f"{self._build_endpoint(_ENDPOINT_PLATFORM)}{filter_by_name}"

        resp = self.__client.get(endpoint)
        resp.raise_for_status()

        platforms = []
        platforms_json = resp.json().get("platforms", None)

        if not platforms_json:
            return platforms

        for platform_json in platforms_json:
            platform = QaaSPlatform.from_dict(platform_json)

            if not platform:
                raise Exception(
                    "Failure during platform json deserialization:", platform_json
                )

            platforms.append(platform)

        return platforms

    def create_session(
        self,
        name: str,
        platform_id: str,
        deduplication_id: str,
        max_duration: str,
        max_idle_duration: str,
    ) -> QaaSSession:
        payload = {
            "name": name,
            "project_id": self.__project_id,
            "platform_id": platform_id,
            "deduplication_id": deduplication_id,
            "max_duration": max_duration,
            "max_idle_duration": max_idle_duration,
        }

        response = self.__client.post(
            self._build_endpoint(_ENDPOINT_SESSION), json=payload
        )

        response.raise_for_status()
        session_json = response.json()
        session = QaaSSession.from_dict(session_json)

        if not session:
            raise Exception(
                "Failure during session json deserialization:", session_json
            )

        return session

    def update_session(
        self, session_id: str, name: str, max_duration: str, max_idle_duration: str
    ) -> QaaSSession:
        payload = {
            "name": name,
            "max_duration": max_duration,
            "max_idle_duration": max_idle_duration,
        }

        response = self.__client.patch(
            self._build_endpoint(f"{_ENDPOINT_SESSION}/{session_id}"), json=payload
        )

        response.raise_for_status()
        session_json = response.json()
        session = QaaSSession.from_dict(session_json)

        if not session:
            raise Exception(
                "Failure during session json deserialization:", session_json
            )

        return session

    def terminate_session(self, session_id: str) -> QaaSSession:
        response = self.__client.post(
            self._build_endpoint(f"{_ENDPOINT_SESSION}/{session_id}/terminate")
        )

        response.raise_for_status()
        session_json = response.json()
        session = QaaSSession.from_dict(session_json)

        if not session:
            raise Exception(
                "Failure during session json deserialization:", session_json
            )

        return session

    def delete_session(self, session_id: str):
        self.__client.delete(self._build_endpoint(f"{_ENDPOINT_SESSION}/{session_id}"))

    def create_job(self, name: str, session_id: str, circuits: dict) -> QaaSJob:
        payload = {
            "name": name,
            "session_id": session_id,
            "circuit": {"qiskit_circuit": f"{circuits}"},
        }

        response = self.__client.post(self._build_endpoint(_ENDPOINT_JOB), json=payload)
        response.raise_for_status()

        job_json = response.json()
        job = QaaSJob.from_dict(job_json)

        if not job:
            raise Exception("Failure during job json deserialization:", job_json)

        return job

    def get_job(self, job_id: str) -> QaaSJob:
        endpoint = f"{self._build_endpoint(_ENDPOINT_JOB)}/{job_id}"

        response = self.__client.get(endpoint)
        response.raise_for_status()
        job_json = response.json()

        job = QaaSJob.from_dict(job_json)

        if not job:
            raise Exception("Failure during job json deserialization:", job_json)

        return job

    def get_job_results(self, job_id: str) -> List[QaaSJobResult]:
        endpoint = f"{self._build_endpoint(_ENDPOINT_JOB)}/{job_id}/results"

        resp = self.__client.get(endpoint)
        resp.raise_for_status()

        job_results = []
        job_results_json = resp.json().get("job_results", None)

        if not job_results_json:
            return job_results

        for job_result_json in job_results_json:
            job_result = QaaSJobResult.from_dict(job_result_json)

            if not job_result:
                raise Exception(
                    "Failure during job_result json deserialization:", job_result_json
                )

            job_results.append(job_result)

        return job_results
