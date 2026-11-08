import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .deduplicator import RecordDeduplicator
from .infrai_client import InfraiClient, InfraiError
from .models import DeduplicationResult, GameRecord

COLLECTION = os.environ.get("INFRAI_COLLECTION", "game-backend-records")
DIMENSION = 1536


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = InfraiClient()
    client.create_collection(COLLECTION, DIMENSION)
    app.state.infrai = client
    app.state.deduplicator = RecordDeduplicator(client, COLLECTION)
    yield
    client.close()


app = FastAPI(title="Game Record Duplicate Guard", lifespan=lifespan)


@app.post("/records/inspect", response_model=DeduplicationResult)
def inspect_record(record: GameRecord) -> DeduplicationResult:
    try:
        return app.state.deduplicator.inspect(record)
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc

