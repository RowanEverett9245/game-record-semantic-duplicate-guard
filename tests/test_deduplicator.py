from game_record_guard.deduplicator import RecordDeduplicator
from game_record_guard.models import GameRecord, RecordKind


class FakeIndex:
    def __init__(self, matches: list[dict]) -> None:
        self.matches = matches
        self.writes: list[dict] = []

    def embed(self, text: str) -> list[float]:
        assert "Neon harbor banner" in text
        return [0.2, 0.8]

    def query(self, collection: str, embedding: list[float], game_id: str) -> list[dict]:
        assert (collection, embedding, game_id) == ("records", [0.2, 0.8], "skyline-raiders")
        return self.matches

    def upsert(self, collection: str, record_id: str, embedding: list[float], metadata: dict[str, str]) -> None:
        self.writes.append({"collection": collection, "id": record_id, "metadata": metadata})


def record() -> GameRecord:
    return GameRecord(
        kind=RecordKind.PLAYER_ASSET,
        title="Neon harbor banner",
        body="Violet skyline with cyan docks and the CRW guild initials.",
        creator_id="player-1842",
        game_id="skyline-raiders",
    )


def test_flags_semantic_duplicate_without_writing() -> None:
    index = FakeIndex(
        [{"id": "asset-77", "score": 0.94, "metadata": {"title": "Cyber port flag", "kind": "player_asset"}}]
    )

    result = RecordDeduplicator(index, "records", threshold=0.90).inspect(record())

    assert result.decision == "duplicate"
    assert result.match is not None
    assert result.match.record_id == "asset-77"
    assert index.writes == []


def test_accepts_and_indexes_distinct_record() -> None:
    index = FakeIndex([{"id": "asset-12", "score": 0.61, "metadata": {}}])

    result = RecordDeduplicator(index, "records", threshold=0.90).inspect(record())

    assert result.decision == "accepted"
    assert len(result.record_id) == 24
    assert index.writes[0]["metadata"]["game_id"] == "skyline-raiders"



def test_read_only_inspection_does_not_index_distinct_record() -> None:
    index = FakeIndex([])

    result = RecordDeduplicator(index, "records").inspect(record(), persist=False)

    assert result.decision == "accepted"
    assert len(result.record_id) == 24
    assert index.writes == []
