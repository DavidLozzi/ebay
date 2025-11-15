# eBay Inventory & Listing Automation Tool

A tool to automate the process of adding inventory to eBay and creating listings for it.

## details

- Organize raw photo drops into SKU-specific folders, rename label shots to `SKU.jpg`, and cap GPT batches at 50 images.
- Generate inventory CSVs by extracting metadata with GPT, pulling sold comps from MCP, and writing timestamped CSV files.
- Upload listing CSVs via MCP, supporting draft-only, publish-only, or combined create-and-publish workflows.

## coding requirements

### Python

- always use `httpx` over `requests`
- if performing multiple API calls, consider if it can be done in parallel and use `asyncio` to run multiple calls in parallel

## requirements

- CLI workflow spans three modes: `--organize` for raw photo sorting, default inventory run for CSV generation, and `--upload` for MCP listing creation or publishing.
- Python 3.11+ in a virtual environment (`python -m venv .venv`, `pip install -e .`).
- Access to the eBay MCP server (`MCP_ENDPOINT`, `MCP_API_KEY`) for inventory generation and publishing.
- OpenAI API key with GPT-5 access (optionally configure `OPENAI_API_BASE`, `LOG_LEVEL`, `CONCURRENCY_LIMIT`).
- Mode-specific environment variables: `OPENAI_API_KEY` required for organize/inventory flows; MCP credentials required for inventory/publish steps.

## learnings

As you interact with the user and if you find anything that is out of the norm or an area where you and the user went back-and-forth, or the user had to correct you, save your learnings below.

### learnings
Let your learnings in bullets below