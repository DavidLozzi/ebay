from __future__ import annotations

import asyncio
import base64
import random
from pathlib import Path
from typing import Any

import httpx

from core.env import AppConfig
from core.logging import get_logger
from core.models import MCPImageUpload, MCPListingRequest, MCPListingResponse, PriceRecommendation, SoldListing

logger = get_logger(__name__)


class MCPClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        retries: int = 3,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=timeout,
        )
        self._retries = retries

    @classmethod
    def from_config(cls, config: AppConfig) -> "MCPClient":
        if not config.mcp_endpoint or not config.mcp_api_key:
            raise ValueError("MCP credentials are not configured.")
        return cls(str(config.mcp_endpoint), config.mcp_api_key)

    async def __aenter__(self) -> "MCPClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, json: Any | None = None) -> Any:
        for attempt in range(self._retries):
            try:
                response = await self._client.request(method, path, json=json)
                response.raise_for_status()
                return response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                if attempt == self._retries - 1:
                    raise
                backoff = min(2 ** attempt + random.random(), 10)
                logger.warning("MCP request failed (%s), retrying in %.2fs", exc, backoff)
                await asyncio.sleep(backoff)

    async def invoke(self, tool: str, payload: dict[str, Any]) -> Any:
        return await self._request("POST", "/invoke", {"tool": tool, "input": payload})

    async def upload_image(self, sku: str, image_path: Path) -> MCPImageUpload:
        data = image_path.read_bytes()
        encoded = base64.b64encode(data).decode("utf-8")
        payload = {"sku": sku, "filename": image_path.name, "content": encoded}
        response = await self.invoke("upload_image", payload)
        return MCPImageUpload(image_path=image_path, remote_url=response["url"])

    async def create_listing(self, request: MCPListingRequest) -> MCPListingResponse:
        response = await self.invoke("create_listing", request.model_dump())
        return MCPListingResponse(**response)

    async def publish_listing(self, listing_id: str) -> MCPListingResponse:
        response = await self.invoke("publish_listing", {"listing_id": listing_id})
        return MCPListingResponse(**response)

    async def fetch_sold_prices(self, query: str) -> PriceRecommendation:
        response = await self.invoke("search_sold", {"query": query})
        sold_listings = [SoldListing(**item) for item in response.get("results", [])]
        if not sold_listings:
            return PriceRecommendation(recommended_price=0.0, rationale="No comps found.")
        highest = max(sold.price for sold in sold_listings)
        recommended = round(highest * 0.9, 2)
        rationale = f"Recommended price is 10% below highest sold price (${highest:.2f})."
        return PriceRecommendation(
            recommended_price=recommended,
            rationale=rationale,
            sold_listings=sold_listings,
        )