from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from core.env import AppConfig
from core.logging import get_logger
from core.models import InventoryRow, MCPListingRequest
from core.csv_io import overwrite_inventory_csv, read_inventory_csv
from mcp.client import MCPClient
from utils.concurrency import run_with_concurrency
from utils.files import is_image

logger = get_logger(__name__)


def _resolve_image_paths(row: InventoryRow) -> list[Path]:
    folder = Path(row.folder)
    if not folder.exists():
        raise FileNotFoundError(f"Folder {folder} does not exist for row {row.sku}")

    paths: list[Path] = []
    if row.image_urls:
        for image_ref in row.image_urls:
            if image_ref.startswith("http"):
                continue
            image_path = Path(image_ref)
            if not image_path.is_absolute():
                image_path = folder / image_ref
            paths.append(image_path)
    else:
        paths = [path for path in folder.iterdir() if path.is_file() and is_image(path)]
    return paths


def _is_remote(url: str) -> bool:
    try:
        return urlparse(url).scheme in {"http", "https"}
    except ValueError:
        return False


async def _create_listing_for_row(
    client: MCPClient,
    row: InventoryRow,
    publish_after_create: bool,
    upload_limit: int,
) -> InventoryRow:
    image_paths = _resolve_image_paths(row)
    uploads = await run_with_concurrency(
        image_paths,
        limit=max(1, min(upload_limit, len(image_paths) or 1)),
        worker=lambda path: client.upload_image(row.sku, path),
    )
    remote_urls = [upload.remote_url for upload in uploads]
    row.image_urls = remote_urls

    request = MCPListingRequest(
        sku=row.sku,
        title=row.title,
        description=row.description,
        price=row.recommended_price,
        listing_format=row.listing_format,
        image_urls=remote_urls,
    )
    listing = await client.create_listing(request)
    row.mcp_listing_id = listing.listing_id
    if publish_after_create:
        await client.publish_listing(listing.listing_id)
    return row


async def _publish_existing_listing(client: MCPClient, row: InventoryRow) -> InventoryRow:
    if not row.mcp_listing_id:
        logger.warning("Row %s has no listing id; skipping publish.", row.sku)
        return row
    await client.publish_listing(row.mcp_listing_id)
    return row


async def process_uploads(
    csv_path: Path,
    draft_only: bool,
    publish_only: bool,
    config: AppConfig,
) -> list[InventoryRow]:
    rows = read_inventory_csv(csv_path)
    async with MCPClient.from_config(config) as client:

        async def worker(row: InventoryRow) -> InventoryRow:
            if publish_only:
                return await _publish_existing_listing(client, row)
            publish_after_create = not draft_only
            return await _create_listing_for_row(
                client,
                row,
                publish_after_create,
                upload_limit=config.concurrency_limit,
            )

        updated_rows = await run_with_concurrency(
            rows,
            limit=config.concurrency_limit,
            worker=worker,
        )

    overwrite_inventory_csv(csv_path, updated_rows)
    return updated_rows
