from decimal import Decimal, getcontext

import aiohttp
import asyncio
import aiofiles
import json
import signal
import time
from datetime import datetime

from functools import partial
from argparse import ArgumentParser
from utils import cleanup_response, CURRENCY_TO_HANDLE
from collections import namedtuple
from db.connection import insert_points_into_db
import logging

logger = logging.getLogger("fetcher")

DataPoint = namedtuple('DataPoint', 'symbol value timestamp')
stop_event = asyncio.Event()


def get_points_data(response: dict, timestamp: int) -> list:
    rates = response['Rates']

    data_to_insert = []
    # проитерироваться по нему, вычленив нужные валюты
    # подготовить данные для записи
    for row in rates:
        if row['Symbol'] not in CURRENCY_TO_HANDLE:
            continue

        getcontext().prec = 6
        bid = Decimal(row['Bid'])
        ask = Decimal(row['Ask'])

        value = Decimal(bid + ask) / Decimal(2)
        point = DataPoint(row['Symbol'], value, timestamp)

        data_to_insert.append(point)

    return [(point.symbol, point.value, point.timestamp)
            for point in data_to_insert]


async def handle_response(response: dict):
    # принять параметр со словарем с данными
    timestamp = int(time.mktime(datetime.now().timetuple()))
    data = get_points_data(response, timestamp)
    # записать в базу
    loop = asyncio.get_event_loop()

    await insert_points_into_db(loop, data)


async def mock_fetch(filename: str) -> str:
    async with aiofiles.open(filename, mode='r') as f:
        resp = await f.read()

    contents = cleanup_response(resp)
    return json.loads(contents)


async def fetch(session: aiohttp.ClientSession, url: str):
    async with session.get(url, ssl=False) as response:
        resp = await response.text()

    contents = cleanup_response(resp)
    return json.loads(contents)


async def fetch_data(_args):
    async with aiohttp.ClientSession() as session:
        if _args.filename:
            fetch_func = partial(mock_fetch, args.filename)
        else:
            fetch_func = partial(fetch, session, _args.url)

        response = await fetch_func()

        await handle_response(response=response)


async def main(_args):
    while not stop_event.is_set():
        await fetch_data(_args)
        await asyncio.sleep(1)


async def handler():
    await asyncio.sleep(0.3)
    asyncio.get_event_loop().stop()


def setup():
    loop = asyncio.get_event_loop()
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame),
                                lambda: asyncio.create_task(handler()))


def inner_ctrl_c_signal_handler(sig, frame):
    logger.info("SIGINT caught!")
    stop_event.set()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-f", "--file", dest="filename",
                        help="read from FILE")
    parser.add_argument("-u", "--url", dest="url",
                        help="read from URI",
                        default='https://ratesjson.fxcm.com/DataDisplayer')
    args = parser.parse_args()

    signal.signal(signal.SIGINT, inner_ctrl_c_signal_handler)
    asyncio.run(main(args))

