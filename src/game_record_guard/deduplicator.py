import hashlib
from typing import Any

from .models import DeduplicationResult, DuplicateMatch, GameRecord, RecordKind


class RecordDeduplicator:
    def __init__(self, index: Any, collection: str, threshold: float = 0.90) -> None:
        self.index = index
        self.collection = collection
        self.threshold = threshold

    def inspect(self, record: GameRecord, *, persist: bool = True) -> DeduplicationResult:
        text = record.search_text()
        record_id = hashlib.sha256(
            f"{record.game_id}\0{record.creator_id}\0{text}".encode("utf-8")
        ).hexdigest()[:24]
        embedding = self.index.embed(text)
        matches = self.index.query(self.collection, embedding, record.game_id)
        best = max(matches, key=lambda item: float(item.get("score", 0.0)), default=None)

        if best and float(best.get("score", 0.0)) >= self.threshold:
            metadata = best.get("metadata") or {}
            return DeduplicationResult(
                decision="duplicate",
                record_id=record_id,
                match=DuplicateMatch(
                    record_id=str(best["id"]),
                    score=float(best["score"]),
                    title=str(metadata.get("title", "Untitled record")),
                    kind=RecordKind(metadata["kind"]),
                ),
            )

        if persist:
            self.index.upsert(
                self.collection,
                record_id,
                embedding,
                {
                    "game_id": record.game_id,
                    "creator_id": record.creator_id,
                    "title": record.title,
                    "kind": record.kind.value,
                },
            )
        return DeduplicationResult(decision="accepted", record_id=record_id)
