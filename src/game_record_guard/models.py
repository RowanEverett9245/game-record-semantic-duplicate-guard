from enum import Enum

try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ModuleNotFoundError:
    from dataclasses import dataclass

    HAS_PYDANTIC = False

    class BaseModel:
        """Minimal model fallback for dependency-free core usage."""


class RecordKind(str, Enum):
    PLAYER_ASSET = "player_asset"
    LIVE_EVENT = "live_event"
    MODERATION_ITEM = "moderation_item"


if HAS_PYDANTIC:
    class GameRecord(BaseModel):
        kind: RecordKind
        title: str = Field(min_length=1, max_length=160)
        body: str = Field(min_length=1, max_length=4000)
        creator_id: str = Field(min_length=1, max_length=120)
        game_id: str = Field(min_length=1, max_length=120)

        def search_text(self) -> str:
            return f"{self.kind.value}\nTitle: {self.title.strip()}\nContent: {self.body.strip()}"


    class DuplicateMatch(BaseModel):
        record_id: str
        score: float
        title: str
        kind: RecordKind


    class DeduplicationResult(BaseModel):
        decision: str
        record_id: str
        match: DuplicateMatch | None = None
else:
    @dataclass
    class GameRecord(BaseModel):
        kind: RecordKind
        title: str
        body: str
        creator_id: str
        game_id: str

        def search_text(self) -> str:
            return f"{self.kind.value}\nTitle: {self.title.strip()}\nContent: {self.body.strip()}"


    @dataclass
    class DuplicateMatch(BaseModel):
        record_id: str
        score: float
        title: str
        kind: RecordKind


    @dataclass
    class DeduplicationResult(BaseModel):
        decision: str
        record_id: str
        match: DuplicateMatch | None = None
