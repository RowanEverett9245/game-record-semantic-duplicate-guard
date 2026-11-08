import json
import os

from game_record_guard.deduplicator import RecordDeduplicator
from game_record_guard.infrai_client import InfraiClient
from game_record_guard.models import GameRecord, RecordKind


def main() -> None:
    client = InfraiClient()
    try:
        guard = RecordDeduplicator(
            client, os.environ.get("INFRAI_VECTOR_COLLECTION", "game-backend-records")
        )
        result = guard.inspect(
            GameRecord(
                kind=RecordKind.PLAYER_ASSET,
                title="Neon harbor banner",
                body="A player-made banner with a violet skyline, cyan docks, and the guild initials CRW.",
                creator_id="player-1842",
                game_id="skyline-raiders",
            ),
            persist=False,
        )
        print(json.dumps(result.model_dump(), indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()

