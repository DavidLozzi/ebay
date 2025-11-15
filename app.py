from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer

from core.csv_io import write_inventory_csv
from core.env import ConfigError, get_config_for_mode
from core.logging import setup_logging
from gpt.analyze import analyze_inventory
from gpt.organize import organize_images
from mcp.listings import process_uploads
from utils.files import move_assignments

app = typer.Typer(add_completion=False, help="Inventory and listing automation tool.")


def _run_async(coro):
    return asyncio.run(coro)


@app.command()
def main(
    items_path: Optional[Path] = typer.Argument(
        None,
        help="Path to organized item folders (inventory mode).",
    ),
    organize: Optional[Path] = typer.Option(
        None,
        "--organize",
        exists=True,
        dir_okay=True,
        file_okay=False,
        help="Path to raw images root.",
    ),
    upload: Optional[Path] = typer.Option(
        None,
        "--upload",
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to inventory CSV for publish mode.",
    ),
    draft: bool = typer.Option(False, "--draft", help="Create draft listings only."),
    publish: bool = typer.Option(False, "--publish", help="Publish existing drafts."),
) -> None:
    try:
        if organize:
            _run_organize_mode(organize)
        elif upload:
            _run_publish_mode(upload, draft, publish)
        elif items_path:
            _run_inventory_mode(items_path)
        else:
            raise typer.BadParameter("Provide --organize, --upload, or an items path.")
    except ConfigError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


def _run_organize_mode(path: Path) -> None:
    if not path.exists():
        raise typer.BadParameter(f"{path} not found.")
    config = get_config_for_mode("organize")
    setup_logging(config.log_level)
    assignments = _run_async(organize_images(path, config))
    move_assignments(assignments, path)
    typer.echo(f"Organized {len(assignments)} images under {path}")


def _run_inventory_mode(path: Path) -> None:
    if not path.exists():
        raise typer.BadParameter(f"{path} not found.")
    config = get_config_for_mode("inventory")
    setup_logging(config.log_level)
    rows = _run_async(analyze_inventory(path, config))
    csv_path = write_inventory_csv(rows, path)
    typer.echo(f"Created CSV at {csv_path.resolve()}")


def _run_publish_mode(csv_path: Path, draft: bool, publish: bool) -> None:
    if draft and publish:
        raise typer.BadParameter("Use either --draft or --publish, not both.")
    config = get_config_for_mode("publish")
    setup_logging(config.log_level)
    updated_rows = _run_async(process_uploads(csv_path, draft_only=draft, publish_only=publish, config=config))
    typer.echo(f"Updated {csv_path} for {len(updated_rows)} rows")


def main_cli() -> None:
    app()


if __name__ == "__main__":
    main_cli()
