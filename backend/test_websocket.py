import asyncio
import json

import websockets


async def test_chat():

    uri = "ws://127.0.0.1:8000/api/v1/chat/ws"

    async with websockets.connect(
        uri,
        ping_interval=20,
        ping_timeout=120,
        close_timeout=10,
    ) as websocket:

        await websocket.send(
            json.dumps(
                {
                    "question": (
                        "What is Storage Fabric "
                        "(DataSync Layer)?"
                    )
                }
            )
        )

        while True:

            message = await websocket.recv()

            data = json.loads(message)

            print(data)

            if data.get("type") == "complete":
                break


if __name__ == "__main__":
    asyncio.run(test_chat())