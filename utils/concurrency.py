from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from typing import TypeVar, cast

T = TypeVar("T")
R = TypeVar("R")


async def bounded_gather(
    tasks: Iterable[Callable[[], Awaitable[R]]],
    limit: int,
) -> list[R]:
    semaphore = asyncio.Semaphore(limit)
    factories = list(tasks)
    results: list[R | None] = [None] * len(factories)

    async def runner(index: int, task_factory: Callable[[], Awaitable[R]]) -> None:
        async with semaphore:
            results[index] = await task_factory()

    await asyncio.gather(*(runner(idx, factory) for idx, factory in enumerate(factories)))
    return [cast(R, result) for result in results]


async def run_with_concurrency(
    items: Iterable[T],
    limit: int,
    worker: Callable[[T], Awaitable[R]],
) -> list[R]:
    semaphore = asyncio.Semaphore(limit)
    item_list = list(items)
    results: list[R | None] = [None] * len(item_list)

    async def bound_work(index: int, item: T) -> None:
        async with semaphore:
            results[index] = await worker(item)

    await asyncio.gather(*(bound_work(idx, item) for idx, item in enumerate(item_list)))
    return [cast(R, result) for result in results]
