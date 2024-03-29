from typing import Union

import httpx


_ENDPOINT_PLATFORM = "/platforms"
_ENDPOINT_SESSION = "/sessions"
_ENDPOINT_JOB = "/jobs"
_PROVIDER_NAME = "scaleway"


class ScalewayClient:
    def __init__(self, url: str, token: str, project_id: str) -> None:
        self.__token = token
        self.__url = url
        self.__project_id = project_id

    def _http_client(self) -> httpx.Client:
        # TODO: remove verify false
        return httpx.Client(
            headers=self._api_headers(), base_url=self.__url, timeout=10.0, verify=False
        )

    def _api_headers(self) -> dict:
        return {"X-Auth-Token": self.__token}

    def _build_endpoint(self, endpoint: str) -> str:
        return f"{self._url}{endpoint}"

    def list_platforms(self, name: str = "") -> dict:
        http_client = self._http_client()
        endpoint = (
            f"{self._build_endpoint(_ENDPOINT_PLATFORM)}?providerName={_PROVIDER_NAME}"
        )

        if name:
            endpoint += f"&name={name}"

        resp = http_client.get(endpoint)
        resp.raise_for_status()

        return resp.json()

    def create_session(
        self,
        name: str,
        platform_id: str,
        deduplication_id: str,
        max_duration: str,
        max_idle_duration: str,
    ) -> str:
        http_client = self._http_client()

        payload = {
            "name": name,
            "project_id": self.__project_id,
            "platform_id": platform_id,
            "deduplication_id": deduplication_id,
            "max_duration": max_duration,
            "max_idle_duration": max_idle_duration,
        }

        request = http_client.post(
            self._build_endpoint(_ENDPOINT_SESSION), json=payload
        )

        request.raise_for_status()
        request_dict = request.json()
        session_id = request_dict["id"]

        return session_id

    def terminate_session(self, session_id: str) -> str:
        http_client = self._http_client()

        payload = {
            "session_id": session_id,
        }

        request = http_client.post(
            self._build_endpoint(_ENDPOINT_SESSION), json=payload
        )

        request.raise_for_status()
        request_dict = request.json()
        session_id = request_dict["id"]

        return session_id

    def create_job(self, name: str, session_id: str, circuits: dict) -> str:
        http_client = self._http_client()

        payload = {
            "name": name,
            "session_id": session_id,
            "circuit": {"qiskit_circuit": f"{circuits}"},
        }

        request = http_client.post(self._build_endpoint(_ENDPOINT_JOB), json=payload)

        request.raise_for_status()
        request_dict = request.json()

        return request_dict["id"]

    def get_job(self, job_id: str) -> dict:
        http_client = self._http_client()
        endpoint = f"{self._build_endpoint(_ENDPOINT_JOB)}/{job_id}"

        resp = http_client.get(endpoint)
        resp.raise_for_status()

        return resp.json()

    def get_job_results(self, job_id: str) -> list:
        http_client = self._http_client()
        endpoint = f"{self._build_endpoint(_ENDPOINT_JOB)}/{job_id}/results"

        resp = http_client.get(endpoint)
        resp.raise_for_status()

        results_dict = resp.json()

        return results_dict["job_results"]
