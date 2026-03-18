from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Optional


class PhaseTimer:
    def __init__(self) -> None:
        self._task: Optional[asyncio.Task] = None

    def start(self, seconds: int, callback: Callable[[], Awaitable[None]]) -> None:
        self.cancel()
        self._task = asyncio.create_task(self._run(seconds, callback))

    def cancel(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    async def _run(self, seconds: int, callback: Callable[[], Awaitable[None]]) -> None:
        try:
            await asyncio.sleep(seconds)
            await callback()
        except asyncio.CancelledError:
            return
