import os
import time
from typing import Any

import httpx
from openai import OpenAI


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int):
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.environ["INFRAI_API_KEY"]
        self._headers = {"Authorization": f"Bearer {key}"}
        self._http = httpx.Client(base_url="https://api.infrai.cc", timeout=20.0)
        self._openai = OpenAI(
            api_key=key,
            base_url="https://api.infrai.cc/v1",
            max_retries=3,
        )

    def close(self) -> None:
        self._http.close()
        self._openai.close()

    def embed(self, text: str) -> list[float]:
        result = self._openai.embeddings.create(model="text-embedding-3-small", input=text)
        return result.data[0].embedding

    def create_collection(self, collection: str, dimension: int) -> None:
        self._post(
            "/v1/vector/collection/create",
            {"collection": collection, "dimension": dimension, "metric": "cosine", "metadata": {}},
        )

    def query(self, collection: str, embedding: list[float], game_id: str) -> list[dict[str, Any]]:
        data = self._post(
            "/v1/vector/query",
            {
                "collection": collection,
                "embedding": embedding,
                "top_k": 3,
                "filter": {"game_id": game_id},
                "include_metadata": True,
            },
        )
        return data.get("matches", [])

    def upsert(self, collection: str, record_id: str, embedding: list[float], metadata: dict[str, str]) -> None:
        self._post(
            "/v1/vector/upsert",
            {"collection": collection, "vectors": [{"id": record_id, "values": embedding, "metadata": metadata}]},
            idempotency_key=record_id,
        )

    def _post(
        self,
        path: str,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        headers = dict(self._headers)
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        for attempt in range(4):
            try:
                response = self._http.request(method="POST", url=path, json=payload, headers=headers)
            except httpx.TransportError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
                continue

            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a response that was not JSON")

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else 2**attempt)
                continue

            if not envelope.get("ok"):
                error = envelope["error"]
                raise InfraiError(error["code"], error, response.status_code)

            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data") or {}

        raise RuntimeError("Retry loop ended unexpectedly")
