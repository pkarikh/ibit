import aiomysql
from datetime import datetime, timedelta
from server.asset_points import AssetPoint

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 3306


async def get_pool(loop):
    return await aiomysql.create_pool(host=DEFAULT_HOST, port=DEFAULT_PORT,
                                      user='user', password='password',
                                      db='points_db', loop=loop)


async def insert_points_into_db(loop, data: list):
    pool = await get_pool(loop)

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(
                "INSERT INTO currency_points (currency, value, timestamp)"
                "values (%s,%s,%s)", data)
            await conn.commit()

    pool.close()
    await pool.wait_closed()


async def select_last_point_from_db(loop, asset_type: str):
    pool = await get_pool(loop)

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT currency, value, timestamp "
                "FROM currency_points WHERE currency='{currency}' "
                "ORDER BY timestamp desc limit 1"
                .format(currency=asset_type)
            )
            raw_data = await cur.fetchall()

    pool.close()
    await pool.wait_closed()
    return raw_data


async def select_history_points_from_db(loop, asset_type: str):
    pool = await get_pool(loop)
    dt = (datetime.now() - timedelta(minutes=30)).strftime('%s')

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT currency, value, timestamp "
                "FROM currency_points WHERE currency='{currency}' "
                "AND timestamp >= '{timestamp}'"
                "ORDER BY timestamp desc"
                .format(timestamp=dt, currency=asset_type)
            )
            raw_data = await cur.fetchall()

    pool.close()
    await pool.wait_closed()
    return raw_data


def convert_raw_to_asset_point(data: tuple) -> AssetPoint:
    asset_sym, asset_value, timestamp = data
    asset_point = AssetPoint(asset_type=asset_sym, value=asset_value,
                             timestamp=timestamp)
    return asset_point
