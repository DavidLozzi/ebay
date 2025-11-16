from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Iterable

from openai import AsyncOpenAI

from core.env import AppConfig
from core.logging import get_logger
from core.models import ImageAssignment
from utils.files import iter_image_files

logger = get_logger(__name__)

BATCH_SIZE = 50
SYSTEM_PROMPT = (
    "You are an assistant that groups raw product photos into folders based on SKU labels. "
    "Return JSON with entries: filename, folder, is_label."
)


def _encode_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _image_payload(path: Path) -> dict[str, str]:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return {"type": "input_image", "image_base64": _encode_image(path), "mime_type": mime}


def _chunked(iterable: list[Path], size: int) -> Iterable[list[Path]]:
    for idx in range(0, len(iterable), size):
        yield iterable[idx : idx + size]


def _build_user_content(chunk: list[Path]) -> list[dict[str, str]]:
    content: list[dict[str, str]] = [
        {
            "type": "input_text",
            "text": (
                "Group these images. Use existing alphanumeric labels written in the photo when present, "
                "otherwise create a new folder label when the subject changes. Respond with JSON array "
                "like [{\"filename\": \"IMG_1234.jpg\", \"folder\": \"A12\", \"is_label\": true}]."
            ),
        }
    ]
    for path in chunk:
        content.append(_image_payload(path))
    return content


def _extract_text(response) -> str:
    for item in response.output:
        for output in item.content:
            if output.type == "output_text":
                return output.text
    raise ValueError("No text output found in response.")


def _parse_assignments(text: str, root: Path) -> list[ImageAssignment]:
    data = json.loads(text)
    assignments: list[ImageAssignment] = []
    for entry in data:
        filename = entry["filename"]
        folder = entry["folder"]
        is_label = entry.get("is_label", False)
        source_path = root / filename
        assignments.append(
            ImageAssignment(
                source_path=source_path,
                destination_folder=folder,
                is_label_image=is_label,
            )
        )
    return assignments


async def organize_images(root: Path, config: AppConfig) -> list[ImageAssignment]:
    client = AsyncOpenAI(
        api_key=config.openai_api_key,
        base_url=str(config.openai_api_base) if config.openai_api_base else None,
    )
    images = list(iter_image_files(root))
    assignments: list[ImageAssignment] = []

    for chunk in _chunked(images, BATCH_SIZE):
        response = await client.responses.create(
            model="gpt-5",
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
                {"role": "user", "content": _build_user_content(chunk)},
            ],
        )
        text = _extract_text(response)
        assignments.extend(_parse_assignments(text, root))

    return assignments
