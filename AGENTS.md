# eBay Inventory & Listing Automation Tool — Agent Context

This file gives LLM-based agents the minimum context needed to navigate and extend the project safely.

## Mission

Automate the pipeline from raw photo dumps to live eBay listings:

1. **Organize mode (`--organize`)**: GPT-vision batches (≤50 images) identify handwritten SKU labels, group images, and rename the label shot to `SKU.<ext>`.
2. **Inventory mode (default argument path)**: For each organized folder, GPT summarizes metadata while the MCP server provides sold-price comps; results are written to `listings_YYYYMMDD_HHMMSS.csv`.
3. **Publish mode (`--upload`)**: Reads a CSV, uploads images via MCP, creates listings (draft or live), publishes when requested, and persists the returned `mcp_listing_id` back into the CSV.

## Architecture Cheat Sheet

| Module | Purpose |
| --- | --- |
| `app.py` | Typer CLI entrypoint. Determines mode, sets up logging/config, and runs async workflows. |
| `core/env.py` | Loads `.env`, validates mode-specific requirements (`OPENAI_API_KEY`, `MCP_ENDPOINT`, etc.), exposes `AppConfig`. |
| `core/models.py` | Pydantic models for folders, image assignments, CSV rows (see `CSV_HEADERS`), MCP payloads, and pricing responses. |
| `core/csv_io.py` | Timestamped CSV writer, CSV reader, and overwrite helper for publish mode. |
| `gpt/organize.py` | Handles batching, image base64 encoding, prompt construction, and JSON parsing for folder assignments. |
| `gpt/analyze.py` | Builds listing metadata via GPT, appends description suffix `\n\nItem: <sku>`, and combines MCP sold-price data. |
| `mcp/client.py` | Async `httpx` client with retry/backoff wrapping MCP tools (`upload_image`, `create_listing`, `publish_listing`, `search_sold`). |
| `mcp/listings.py` | Orchestrates CSV-driven listing creation/publishing, resolves local image paths, enforces concurrency limits, and rewrites CSV rows. |
| `utils/files.py` | Filesystem helpers to detect images, ensure folders, move/rename files after organize mode, and collect SKU folders. |
| `utils/concurrency.py` | Semaphore-bound gather helpers that preserve ordering for deterministic CSV updates. |

## External Services

- **OpenAI Responses API** (`gpt-5`): used for both organization (vision) and inventory analysis (vision + text). Always request JSON, respect batch limits, and send base64 images.
- **eBay MCP server** (`MCP_ENDPOINT`, `MCP_API_KEY`): provides search/comps, image upload, listing creation, and publishing. All eBay actions go through MCP tool invocations—never call eBay REST APIs directly.

## Environment & Configuration

- Copy `.env.example` → `.env`. Variables per mode:
  - Organize: `OPENAI_API_KEY`
  - Inventory: `OPENAI_API_KEY`, `MCP_ENDPOINT`, `MCP_API_KEY`
  - Publish: `MCP_ENDPOINT`, `MCP_API_KEY`
- Optional: `OPENAI_API_BASE`, `LOG_LEVEL`, `CONCURRENCY_LIMIT` (defaults to 5; controls folder/image parallelism).
- Config access pattern: `config = get_config_for_mode("<mode>")`, then pass through to downstream modules.

## Operational Notes

- **Concurrency:** Use helpers in `utils.concurrency`; don’t spawn unbounded tasks. Inventory folders and MCP uploads must respect `config.concurrency_limit`.
- **HTTP layer:** Always use `httpx.AsyncClient` with retries (already implemented in `mcp/client.py`). No `requests`.
- **Filesystem:** `utils.files.move_assignments` renames the label image to match folder name and skips missing files gracefully.
- **CSV schema:** `core/models.CSV_HEADERS` defines 24 columns. Descriptions must end with `Item: <folder>`. `mcp_listing_id` starts blank and is set during publish flow.
- **Logging:** `core/logging.setup_logging` provides a uniform format. Use `get_logger(__name__)`.
- **Error handling:** Missing env vars raise `ConfigError`. CLI catches and prints messages via Typer before exiting with status 1.

## How to Extend Safely

- Keep functions small/pure where possible; inject side effects (clients, paths, configs) for easier testing.
- When adding new MCP interactions, update `mcp/client.py` so retries/backoff stay consistent.
- Any new GPT flow should mirror existing JSON-only prompting style to keep parsing predictable.
- Update both `README.md` (user-facing) and this file (agent-facing) when workflows change.

## Learnings

Record notable clarifications or user-specific expectations below.

- _None yet_