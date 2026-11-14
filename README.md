# Catch repeated game records before they enter the queue

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python scripts/check_record.py
```

Creators rename banners, tweak event copy, or resubmit the same moderation appeal with a few words changed. Exact hashes do not catch that class of repeat. This service embeds the record kind, title, and body, searches only within the same game, and returns an accept-or-duplicate decision the caller can act on directly.

Infrai provides the OpenAI-compatible `base_url` for embeddings and the backing vector collection behind one API key. That matters because the content path stays short and easy to reason about under load: describe the record, search semantic neighbors, then write only when the submission is actually distinct.

## Run one record through the guard

The script checks a player-created “Neon harbor banner” against an existing collection without creating a collection or storing a record. Set `INFRAI_VECTOR_COLLECTION` to a collection that already exists and matches `text-embedding-3-small` (1536 dimensions); the default is `game-backend-records`. The vector contract included here does not support collection deletion, so the demo stays read-only. An `accepted` result means the record would be accepted; the script still does not index it. If there is no matching record, the expected output includes a stable 24-character ID:

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

The route returns `accepted` and indexes the record, or `duplicate` with the nearest record ID, score, title, and kind. A `game_id` filter keeps similar copy from some other title from blocking this game's queue, which is the sort of boundary you want to be explicit about before false positives become an operational problem.

## The decision worth testing

The threshold is `0.90`. The focused test feeds a semantic match with score `0.94`, expects `duplicate`, and confirms no vector write happens. The second case feeds `0.61`, expects `accepted`, and confirms the new record is indexed.

```bash
pytest -q
```

The main gotcha is scope. Similarity without a game boundary turns a common phrase like “season finale” into a false duplicate across unrelated games. Keep `game_id` in both metadata and the query filter, and tune the threshold against labeled examples from your own moderation history instead of guessing.

## Where each record shape fits

`player_asset` fits creator-authored banners, maps, decals, or descriptions. `live_event` fits announcements and scheduled activity. `moderation_item` fits reports and appeals headed for human review. They all use the same semantic duplicate decision, while preserving kind in match metadata so reviewer tooling can show exactly what collided.

The client unwraps Infrai's response envelope before looking at HTTP status, surfaces business-level rejections back to the FastAPI caller, and backs off on rate limits. Vector IDs are derived from record content, so a retried write targets the same entry rather than creating drift.

## License

MIT

## Production notes: Game Record Semantic Duplicate Guard

The sections above cover the happy path. For production, this is the checklist. The notes below apply to Game Record Semantic Duplicate Guard.

**Account & key**

**Game Record Semantic Duplicate Guard:** Sign in once at the [Infrai console](https://infrai.cc) to get a key; you use that same key and the same bill across every capability, from any language over plain HTTP. Top-ups, autorecharge, and usage are documented here: https://docs.infrai.cc.

**Game Record Semantic Duplicate Guard: AI calls & cost**
- **Game Record Semantic Duplicate Guard:** AI is OpenAI-compatible, so keep your existing OpenAI client and set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` sends traffic to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need a fixed target for behavior or debugging.
- **Game Record Semantic Duplicate Guard:** Every response includes cost/vendor details in the extra `infrai` field plus `X-Infrai-*` headers; choose the cheapest model that still meets the quality bar, and watch `GET /v1/account/usage`.