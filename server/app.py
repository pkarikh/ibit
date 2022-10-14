from aiohttp import web, WSMsgType
import asyncio
import os
import logging

import json
from contextlib import suppress
from db import connection
from server.asset_points import ASSETS_MAPPING_BY_ID, ASSETS


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("app")

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8080))
POINTS_SLEEP_INTERVAL_SEC = 1


async def get_history_assets(asset_type_id):
    loop = asyncio.get_event_loop()
    asset_symbol = ASSETS_MAPPING_BY_ID[asset_type_id]
    data = await \
        connection.select_history_points_from_db(loop, asset_type=asset_symbol)

    points = [connection.convert_raw_to_asset_point(row).to_dict()
              for row in data]

    return points


async def write_asset_history(ws, asset_type_id):
    points = await get_history_assets(asset_type_id)
    msg = {"message": {"points": points}, "action": "asset_history"}
    await ws.send_json(msg)


async def get_data_point(asset_type_id):
    asset_symbol = ASSETS_MAPPING_BY_ID[asset_type_id]
    loop = asyncio.get_event_loop()
    data = await connection.select_last_point_from_db(loop,
                                                      asset_type=asset_symbol)
    return data


async def send_data_points(ws, asset_type_id):
    while True:
        data = await get_data_point(asset_type_id)
        asset_sym, asset_value, dt = data[0]
        timestamp = dt

        msg = {"action": "point",
               "message": {"assetName": asset_sym, "time": timestamp,
                           "assetId": asset_type_id,
                           "value": float(asset_value)}}
        await ws.send_json(msg)
        await asyncio.sleep(POINTS_SLEEP_INTERVAL_SEC)


async def subscribe_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    current_subscription_task = None

    async for msg in ws:
        data = json.loads(msg.data)
        if data['action'] == 'assets':
            await ws.send_json({"action": "assets",
                                "message": {"assets": ASSETS}})
        elif data['action'] == 'subscribe':
            if current_subscription_task:
                # отменяем предыдущую подписку
                current_subscription_task.cancel()
                with suppress(asyncio.CancelledError):
                    await current_subscription_task

            asset_type_id = data['message']['assetId']
            await write_asset_history(ws, asset_type_id)

            current_subscription_task = \
                asyncio.Task(send_data_points(ws, asset_type_id))
        elif msg.tp == WSMsgType.text:
            if msg.data == 'close':
                await ws.close()

    return ws


async def shutdown(_):
    logger.info("Received exit signal")
    tasks = [t for t in asyncio.all_tasks() if t is not
             asyncio.current_task()]

    [task.cancel() for task in tasks]

    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)


def get_app():
    app = web.Application()
    app.add_routes([web.get('/', subscribe_handler)])
    app.on_shutdown.append(shutdown)

    return app


if __name__ == "__main__":

    app = get_app()

    try:
        logger.info("Successful start")
        web.run_app(app)
    finally:
        logger.info("Successful shutdown")
