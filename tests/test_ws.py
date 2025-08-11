import asyncio
import json
import os
import pytest
import websockets

HOST = os.environ.get("TEST_HOST", "localhost")
PATH = "/ws/chat/"


@pytest.mark.asyncio
async def test_smoke():
    uri = f"ws://{HOST}{PATH}"
    async with websockets.connect(uri) as ws:
        await ws.send("hello")
        msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
        data = json.loads(msg)
        assert data.get("count") == 1
