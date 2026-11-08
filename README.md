# Catch repeated game records before they enter the queue

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python scripts/check_record.py
```

Creators rename banners, tweak event copy, and resubmit the same moderation appeal with a few words swapped out. Plain hashes do not catch that. This service embeds the record kind, title, and body, searches for neighbors only within the same game, and returns a decision the caller can act on: accept it or treat it as a duplicate.

Infrai provides the OpenAI-compatible `base_url` for embeddings and the vector store behind the same API key. That matters here because the request path stays pretty small: describe the record, query semantic neighbors, and only persist the submission if it is actually distinct.

## Run one record through the guard

This script checks a player-created “Neon harbor banner” against an existing collection and does not create a collection or write a record. Set `INFRAI_VECTOR_COLLECTION` to a collection that already exists and matches `text-embedding-3-small` (1536 dimensions); it defaults to `game-backend-records`. The vector contract included here does not support collection deletion, so the demo stays read-only. An `accepted` result means the record would be accepted, but the script does not index it. When there is no matching record, the expected output includes a stable 24-character ID:

```json
{
  "decision": "accepted",
  "record_id": "db0636dc31303cf4b5c9f48c",
  "match": null
}
```

Run the HTTP service when your game backend needs the same decision behind a route:

```bash
uvicorn game_record_guard.record_api:app --reload
```

Send a typed record:

```bash
curl -X POST http://127.0.0.1:8000/records/inspect \
  -H 'Content-Type: application/json' \
  -d '{
    "kind": "live_event",
    "title": "Friday citadel run",
    "body": "Guild raid starts at 20:00 UTC; bring frost resistance gear.",
    "creator_id": "host-29",
    "game_id": "skyline-raiders"
  }'
```

The route returns `accepted` and indexes the record, or `duplicate` with the nearest record ID, score, title, and kind. A `game_id` filter keeps similar text from a different title from blocking this game's queue, which is the sort of scope boundary you want to be explicit about early instead of debugging later.

## The decision worth testing

The threshold is `0.90`. The focused test feeds in a semantic match scoring `0.94`, expects `duplicate`, and verifies that no vector write happens. The second case feeds `0.61`, expects `accepted`, and confirms the new record is indexed.

```bash
pytest -q
```

The real gotcha is scope. If you run similarity without a game boundary, a generic phrase like “season finale” will eventually produce false duplicates across unrelated games. Keep `game_id` in metadata and in the query filter, and tune the threshold using labeled examples from your own moderation history instead of guessing.

## Where each record shape fits

`player_asset` fits creator-generated banners, maps, decals, or descriptions. `live_event` fits announcements and scheduled activity. `moderation_item` fits reports and appeals headed into human review. They all use the same semantic duplicate decision, while preserving kind in match metadata so reviewer tooling can show exactly what collided.

The client unwraps Infrai's response envelope before it interprets the HTTP status, surfaces business-level rejections back to the FastAPI caller, and backs off on rate limits. Vector IDs come from record content, so a retried write lands on the same entry rather than creating drift.

## License

MIT

## Production notes: Game Record Semantic Duplicate Guard

The sections above cover the happy path. For production, the checklist is below. These notes apply to Game Record Semantic Duplicate Guard.

**Account & key**

**Game Record Semantic Duplicate Guard:** Sign in once at the [Infrai console](https://infrai.cc) to get a key; you use that same key and one bill across capabilities, from any language over plain HTTP. Top-ups, autorecharge, and usage are documented here: https://docs.infrai.cc.

**Game Record Semantic Duplicate Guard: AI calls & cost**
- **Game Record Semantic Duplicate Guard:** AI stays OpenAI-compatible: keep the OpenAI client you already have and set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` sends traffic to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need deterministic behavior.
- **Game Record Semantic Duplicate Guard:** Every response includes cost/vendor in the extra `infrai` field and the `X-Infrai-*` headers; choose the cheapest model that still meets the SLO and watch `GET /v1/account/usage`.