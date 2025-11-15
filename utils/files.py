from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

from core.models import FolderImages, ImageAssignment

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".webp"}


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def iter_image_files(root: Path) -> Iterable[Path]:
    for entry in sorted(root.iterdir()):
        if entry.is_file() and is_image(entry):
            yield entry


def ensure_folder(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def move_assignments(assignments: Iterable[ImageAssignment], root: Path) -> None:
    for assignment in assignments:
        if not assignment.source_path.exists():
            continue
        target_dir = ensure_folder(root / assignment.destination_folder)
        destination = target_dir / assignment.source_path.name
        shutil.move(str(assignment.source_path), destination)
        if assignment.is_label_image:
            label_name = f"{assignment.destination_folder}{assignment.source_path.suffix}"
            destination.rename(target_dir / label_name)


def gather_folders(root: Path) -> list[FolderImages]:
    folders: list[FolderImages] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        images = [img for img in entry.iterdir() if img.is_file() and is_image(img)]
        label_image = next(
            (img for img in images if img.stem.lower() == entry.name.lower()), None
        )
        folders.append(
            FolderImages(folder=entry, sku=entry.name, label_image=label_image, images=images)
        )
    return folders