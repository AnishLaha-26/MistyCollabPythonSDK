import asyncio
import websockets

async def echo(websocket, path):
    async for message in websocket:
        await websocket.send(f"Echo: {message}")

start_server = websockets.serve(echo, "10.106.11.9", 8080)


asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
