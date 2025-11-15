# Inventory & Listing Automation Tool

AI-assisted workflow for organizing raw photo drops, generating inventory CSVs, and creating/publishing eBay listings through the MCP server.

## Prerequisites

- Python 3.11+
- Access to the eBay MCP server (`MCP_ENDPOINT`, `MCP_API_KEY`)
- OpenAI API key with GPT-5 access

## Setup

```bash
git clone <repo>
cd <repo>
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env  # fill in secrets
```

## CLI Overview

```
python app.py --organize /path/to/raw_images
python app.py /path/to/organized_items
python app.py --upload /path/to/listings.csv [--draft|--publish]
```

- `--organize`: groups loose photos into SKU folders (max 50 images per GPT batch) and renames label shots to `SKU.jpg`.
- `inventory` (default): scans organized folders, calls GPT for metadata, queries MCP for sold comps, and writes `listings_YYYYMMDD_HHMMSS.csv` in the provided root. Prints absolute CSV path on success.
- `--upload`: reads a CSV, uploads images via MCP, and creates/publishes listings.
  - Omit flags to create + publish in one pass.
  - `--draft`: create drafts only.
  - `--publish`: publish previously-created drafts (`mcp_listing_id` required per row).

## Environment Variables

See `.env.example`. Required per mode:

| Mode      | Variables                               |
|-----------|------------------------------------------|
| Organize  | `OPENAI_API_KEY`                         |
| Inventory | `OPENAI_API_KEY`, `MCP_ENDPOINT`, `MCP_API_KEY` |
| Publish   | `MCP_ENDPOINT`, `MCP_API_KEY`            |

Optional: `OPENAI_API_BASE`, `LOG_LEVEL`, `CONCURRENCY_LIMIT`.

## Architecture Highlights

- Async `httpx` client with retry/backoff for MCP interactions.
- Pydantic models for CSV rows, price data, and listing payloads.
- Structured concurrency helpers for bounded parallelism.
- GPT-driven vision prompts for organization and metadata extraction (OpenAI Responses API).