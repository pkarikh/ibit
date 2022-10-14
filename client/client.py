import asyncio
import signal
import logging
import websockets
import json

logging.basicConfig()
logger = logging.getLogger("client")
logger.setLevel(logging.DEBUG)


async def subscribe():
    async with websockets.connect('ws://127.0.0.1:8080/') as websocket:
        get_assets_msg = {"action": "assets", "message": {}}
        subscr_msg = {"action": "subscribe", "message": {"assetId": 1}}
        await websocket.send(json.dumps(get_assets_msg))

        logger.info(f"> {get_assets_msg}")

        assets_resp = await websocket.recv()
        logger.info(f"< {assets_resp}")

        await websocket.send(json.dumps(subscr_msg))
        logger.info(f"> {subscr_msg}")

        async for msg in websocket:
            data = json.loads(msg)
            logger.info(f"< {data}")


async def shutdown(signal, loop):
    logger.info(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not
             asyncio.current_task()]

    [task.cancel() for task in tasks]

    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)

    for sign in signals:
        loop.add_signal_handler(
            sign, lambda s=sign: asyncio.create_task(shutdown(sign, loop)))

    try:
        loop.create_task(subscribe())
        loop.run_forever()
    finally:
        logger.info("Successful shutdown")
        loop.close()
