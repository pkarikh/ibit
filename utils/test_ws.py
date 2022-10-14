import json

from aiohttp.test_utils import AioHTTPTestCase
import asyncio
from server.app import get_app
from aiohttp.client_exceptions import WSServerHandshakeError
from unittest import mock
from decimal import Decimal


class TestApp(AioHTTPTestCase):
    RESP_EURUSD_HISTORY = [
        {"assetName": "EURUSD", "time": 1455883484, "assetId": 1,
         "value": 1.110481},
        {"assetName": "EURUSD", "time": 1455883485, "assetId": 1,
         "value": 1.110948},
        {"assetName": "EU RUSD", "time": 1455883486, "assetId": 1,
         "value": 1.111122}]

    EURUSD_DATA_POINT = (("EURUSD", Decimal('1.079755'), 1453556718),)
    USDJPY_DATA_POINT = (("USDJPY", Decimal('1.022222'), 1453556799),)
    EURUSD_SUBSCR_MSG = '{"action": "subscribe", "message": {"assetId": 1}}'
    USDJPY_SUBSCR_MSG = '{"action": "subscribe", "message": {"assetId": 2}}'

    async def get_application(self):
        return get_app()

    async def get_ws(self):
        return await self.client.ws_connect("/")

    async def test_wrong_path_raises_exception(self):
        with self.assertRaises(WSServerHandshakeError) as e:
            _ = await self.client.ws_connect("/ws1")

        assert str(e.exception.status) == '404'
        assert str(e.exception.message) == 'Invalid response status'

    async def test_subscribe_and_fetch_data_works_ok(self):
            ws = await self.get_ws()

            # Test subscribtion
            expected_value = {"action": "assets", "message": {
                "assets": [{"id": 1, "name": "EURUSD"},
                           {"id": 2, "name": "USDJPY"},
                           {"id": 3, "name": "GBPUSD"},
                           {"id": 4, "name": "AUDUSD"},
                           {"id": 5, "name": "USDCAD"}]}}

            payload = '{"action":"assets","message":{}}'
            await ws.send_str(payload)

            resp = await ws.receive()
            assert json.loads(resp.data) == expected_value

            with (mock.patch('server.app.get_history_assets',
                             return_value=self.RESP_EURUSD_HISTORY),
                  mock.patch('server.app.get_data_point',
                             side_effect=[self.EURUSD_DATA_POINT,
                                          self.USDJPY_DATA_POINT]),
                  ):

                # Получаем историю
                payload = self.EURUSD_SUBSCR_MSG
                expected_history_msg = {
                    "message": {"points": self.RESP_EURUSD_HISTORY},
                    "action": "asset_history"}

                await ws.send_str(payload)

                resp = await ws.receive()
                self.assertDictEqual(json.loads(resp.data),
                                     expected_history_msg)

                # await asyncio.sleep(2)
                # Получаем новую точку
                expected_asset_point_msg = {
                    "message": {"assetName": "EURUSD", "time": 1453556718,
                                "assetId": 1, "value": 1.079755},
                    "action": "point"}

                response = await asyncio.wait_for(ws.receive(), timeout=2)

                self.assertDictEqual(json.loads(response.data),
                                     expected_asset_point_msg)

                # Подпишемся на другую валюту и получим уже ее датапоинт
                payload = self.USDJPY_SUBSCR_MSG
                await ws.send_str(payload)

                expected_usdjpy_asset_point_msg = {
                    "message": {"assetName": "USDJPY", "time": 1453556799,
                                "assetId": 2, "value": 1.022222},
                    "action": "point"}

                # отбрасываем следующее сообщение, потому что мы
                # могли не успеть в секундный промежуток
                # и там будет точка от старой валюты
                _ = await asyncio.wait_for(ws.receive(), timeout=1)

                response = await asyncio.wait_for(ws.receive(), timeout=2)

                self.assertDictEqual(json.loads(response.data),
                                     expected_usdjpy_asset_point_msg)

    async def test_subscribe_fetch_and_switch_is_ok(self):
            ws = await self.get_ws()

            # Test subscribtion
            expected_value = {"action": "assets", "message": {
                "assets": [{"id": 1, "name": "EURUSD"},
                           {"id": 2, "name": "USDJPY"},
                           {"id": 3, "name": "GBPUSD"},
                           {"id": 4, "name": "AUDUSD"},
                           {"id": 5, "name": "USDCAD"}]}}
            payload = '{"action":"assets","message":{}}'

            await ws.send_str(payload)

            resp = await ws.receive()
            assert json.loads(resp.data) == expected_value

            with (mock.patch('server.app.get_history_assets',
                             return_value=self.RESP_EURUSD_HISTORY),
                  mock.patch('server.app.get_data_point',
                             return_value=self.EURUSD_DATA_POINT)
                  ):
                # Получаем историю
                payload = '{"action": "subscribe", "message": {"assetId": 1}}'

                expected_history_msg = {
                    "message": {"points": self.RESP_EURUSD_HISTORY},
                    "action": "asset_history"}

                await ws.send_str(payload)

                resp = await ws.receive()
                self.assertDictEqual(json.loads(resp.data),
                                     expected_history_msg)
                await asyncio.sleep(10)

                # Получаем новую точку
                expected_asset_point_msg = {
                    "message": {"assetName": "EURUSD", "time": 1453556718,
                                "assetId": 1, "value": 1.079755},
                    "action": "point"}

                response = await asyncio.wait_for(ws.receive(), timeout=2)

                self.assertDictEqual(json.loads(response.data),
                                     expected_asset_point_msg)
