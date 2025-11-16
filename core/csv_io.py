from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Sequence

from core.models import CSV_HEADERS, InventoryRow


def _parse_float_list(value: str) -> list[float]:
    if not value:
        return []
    return [float(part) for part in value.split(";") if part]


def _parse_str_list(value: str) -> list[str]:
    if not value:
        return []
    return [part for part in value.split(";") if part]


def read_inventory_csv(csv_path: Path) -> list[InventoryRow]:
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows: list[InventoryRow] = []
        for row in reader:
            rows.append(
                InventoryRow(
                    item_number=row.get("item_number", ""),
                    sku=row.get("sku", ""),
                    folder=row.get("folder", ""),
                    title=row.get("title", ""),
                    description=row.get("description", ""),
                    condition=row.get("condition", "USED"),
                    condition_note=row.get("condition_note", "") or "",
                    recommended_price=float(row.get("recommended_price") or 0),
                    price_rationale=row.get("price_rationale", "") or "",
                    suggested_category_id=row.get("suggested_category_id", "") or "",
                    suggested_category_path=row.get("suggested_category_path", "") or "",
                    ebay_search_query=row.get("ebay_search_query", "") or "",
                    last_sold_prices=_parse_float_list(row.get("last_sold_prices", "")),
                    price_source=row.get("price_source", "") or "",
                    highest_sold_price=(
                        float(row["highest_sold_price"])
                        if row.get("highest_sold_price")
                        else None
                    ),
                    image_urls=_parse_str_list(row.get("image_urls", "")),
                    notes_path=row.get("notes_path", "") or "",
                    listing_format=row.get("listing_format", "") or "",
                    marketplace_id=row.get("marketplace_id", "") or "",
                    category_id=row.get("category_id", "") or "",
                    quantity=int(row.get("quantity") or 1),
                    listing_duration=row.get("listing_duration", "") or "",
                    best_offer_enabled=(
                        row.get("best_offer_enabled", "true").lower() == "true"
                    ),
                    mcp_listing_id=row.get("mcp_listing_id", "") or "",
                )
            )
    return rows


def _timestamped_filename(root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return root / f"listings_{timestamp}.csv"


def write_inventory_csv(rows: Sequence[InventoryRow], root_path: Path) -> Path:
    csv_path = _timestamped_filename(root_path)
    root_path.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.csv_row())

    return csv_path


def overwrite_inventory_csv(csv_path: Path, rows: Sequence[InventoryRow]) -> None:
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.csv_row())