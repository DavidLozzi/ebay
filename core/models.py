 from __future__ import annotations

from datetime import datetime
from pathlib import Path

 from pydantic import BaseModel, Field


 class ImageAssignment(BaseModel):
     source_path: Path
     destination_folder: str
     is_label_image: bool = False


 class FolderImages(BaseModel):
     folder: Path
     sku: str
     label_image: Path | None = None
     images: list[Path] = Field(default_factory=list)

     @property
     def non_label_images(self) -> list[Path]:
         if not self.label_image:
             return self.images
         return [img for img in self.images if img != self.label_image]


 CSV_HEADERS: list[str] = [
     "item_number",
     "sku",
     "folder",
     "title",
     "description",
     "condition",
     "condition_note",
     "recommended_price",
     "price_rationale",
     "suggested_category_id",
     "suggested_category_path",
     "ebay_search_query",
     "last_sold_prices",
     "price_source",
     "highest_sold_price",
     "image_urls",
     "notes_path",
     "listing_format",
     "marketplace_id",
     "category_id",
     "quantity",
     "listing_duration",
     "best_offer_enabled",
     "mcp_listing_id",
 ]


 class InventoryRow(BaseModel):
     item_number: str
     sku: str
     folder: str
     title: str
     description: str
     condition: str = "USED"
     condition_note: str = ""
     recommended_price: float = 0.0
     price_rationale: str = ""
     suggested_category_id: str = ""
     suggested_category_path: str = ""
     ebay_search_query: str = ""
     last_sold_prices: list[float] = Field(default_factory=list)
     price_source: str = "ebay-sold"
     highest_sold_price: float | None = None
     image_urls: list[str] = Field(default_factory=list)
     notes_path: str = ""
     listing_format: str = "BIN"
     marketplace_id: str = ""
     category_id: str = ""
     quantity: int = 1
     listing_duration: str = "GTC"
     best_offer_enabled: bool = True
     mcp_listing_id: str = ""

     def csv_row(self) -> dict[str, str]:
         return {
             "item_number": self.item_number,
             "sku": self.sku,
             "folder": self.folder,
             "title": self.title,
             "description": self.description,
             "condition": self.condition,
             "condition_note": self.condition_note,
             "recommended_price": f"{self.recommended_price:.2f}",
             "price_rationale": self.price_rationale,
             "suggested_category_id": self.suggested_category_id,
             "suggested_category_path": self.suggested_category_path,
             "ebay_search_query": self.ebay_search_query,
             "last_sold_prices": ";".join(f"{price:.2f}" for price in self.last_sold_prices),
             "price_source": self.price_source,
             "highest_sold_price": (
                 f"{self.highest_sold_price:.2f}" if self.highest_sold_price else ""
             ),
             "image_urls": ";".join(self.image_urls),
             "notes_path": self.notes_path,
             "listing_format": self.listing_format,
             "marketplace_id": self.marketplace_id,
             "category_id": self.category_id,
             "quantity": str(self.quantity),
             "listing_duration": self.listing_duration,
             "best_offer_enabled": "true" if self.best_offer_enabled else "false",
             "mcp_listing_id": self.mcp_listing_id,
         }


 class SoldListing(BaseModel):
     title: str
     price: float
     url: str | None = None
     sold_date: datetime | None = None


 class PriceRecommendation(BaseModel):
     recommended_price: float
     rationale: str
     sold_listings: list[SoldListing] = Field(default_factory=list)

     @property
     def last_sold_prices(self) -> list[float]:
         return [listing.price for listing in self.sold_listings]

     @property
     def highest_price(self) -> float | None:
         prices = self.last_sold_prices
         return max(prices) if prices else None


 class MCPImageUpload(BaseModel):
     image_path: Path
     remote_url: str


 class MCPListingRequest(BaseModel):
     sku: str
     title: str
     description: str
     price: float
     listing_format: str
     image_urls: list[str]


 class MCPListingResponse(BaseModel):
     listing_id: str
     status: str


 def blank_inventory_row(folder: FolderImages) -> InventoryRow:
     return InventoryRow(
         item_number=folder.sku,
         sku=folder.sku,
         folder=str(folder.folder),
         title="",
         description=f"\n\nItem: {folder.sku}",
     )