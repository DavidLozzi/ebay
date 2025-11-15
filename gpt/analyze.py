from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from core.env import AppConfig
from core.logging import get_logger
from core.models import FolderImages, InventoryRow, blank_inventory_row
from mcp.client import MCPClient
from utils.concurrency import run_with_concurrency
from utils.files import gather_folders

logger = get_logger(__name__)


class InventoryAnalyzer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.openai_api_key,
            base_url=str(config.openai_api_base) if config.openai_api_base else None,
        )

    async def analyze_folder(
        self,
        folder: FolderImages,
        mcp_client: MCPClient,
    ) -> InventoryRow:
        llm_data = await self._describe_folder(folder)
        row = blank_inventory_row(folder)
        row.title = llm_data.get("title", "")
        row.description = f"{llm_data.get('description', '')}\n\nItem: {folder.sku}"
        row.condition = llm_data.get("condition", "USED")
        row.condition_note = llm_data.get("condition_note", "")
        row.suggested_category_id = llm_data.get("suggested_category_id", "")
        row.suggested_category_path = llm_data.get("suggested_category_path", "")
        row.ebay_search_query = llm_data.get("ebay_search_query", row.title)
        row.listing_format = llm_data.get("listing_format", "BIN")
        row.marketplace_id = llm_data.get("marketplace_id", "")
        row.category_id = llm_data.get("category_id", "")
        row.notes_path = str(folder.folder / "notes.txt") if (folder.folder / "notes.txt").exists() else ""
        row.image_urls = [image.name for image in folder.non_label_images]
        row.price_source = "mcp-sold"

        quantity_value = llm_data.get("quantity")
        if quantity_value:
            try:
                row.quantity = int(quantity_value)
            except (TypeError, ValueError):
                logger.debug("Unable to parse quantity '%s' for %s", quantity_value, folder.sku)

        price = await mcp_client.fetch_sold_prices(row.ebay_search_query or row.title)
        row.recommended_price = price.recommended_price
        row.price_rationale = price.rationale
        row.last_sold_prices = price.last_sold_prices
        row.highest_sold_price = price.highest_price

        return row

    async def _describe_folder(self, folder: FolderImages) -> dict[str, Any]:
        images = folder.non_label_images[:10]
        if not images and folder.label_image:
            images = [folder.label_image]
        content = [
            {
                "type": "input_text",
                "text": (
                    "Provide listing metadata JSON with keys: title, description, condition, condition_note, "
                    "suggested_category_id, suggested_category_path, ebay_search_query, listing_format, marketplace_id, category_id."
                ),
            }
        ]
        for path in images:
            encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
            mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
            content.append(
                {
                    "type": "input_image",
                    "image_base64": encoded,
                    "mime_type": mime,
                }
            )
        response = await self.client.responses.create(
            model="gpt-5",
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": "You write structured JSON only."}],
                },
                {"role": "user", "content": content},
            ],
        )
        text = self._extract_text(response)
        return json.loads(text)

    @staticmethod
    def _extract_text(response) -> str:
        for item in response.output:
            for output in item.content:
                if output.type == "output_text":
                    return output.text
        raise ValueError("No text output found.")


async def analyze_inventory(root: Path, config: AppConfig) -> list[InventoryRow]:
    folders = gather_folders(root)
    analyzer = InventoryAnalyzer(config)
    async with MCPClient.from_config(config) as mcp_client:

        async def worker(folder: FolderImages) -> InventoryRow:
            return await analyzer.analyze_folder(folder, mcp_client)

        rows = await run_with_concurrency(
            folders,
            limit=config.concurrency_limit,
            worker=worker,
        )

    return rows
