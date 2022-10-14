import unittest
from db.connection import convert_raw_to_asset_point


class TestApp(unittest.TestCase):
    def test_convert_raw_to_asset_point_valid(self):
        raw_data = ("EURUSD", 1.0007, 1641020400)

        asset_point = convert_raw_to_asset_point(raw_data)
        assert asset_point.asset_type == "EURUSD"
        assert asset_point.value == 1.0007
        assert asset_point.timestamp == 1641020400

    def test_convert_raw_to_asset_point_invalid_asset(self):
        raw_data = ("EURUSD1", "1.0007", "1641020400")
        expected ='Invalid asset type EURUSD1. ' \
                  'Expected one of: EURUSD,USDJPY,GBPUSD,AUDUSD,USDCAD'

        with self.assertRaises(ValueError) as e:
            convert_raw_to_asset_point(raw_data)

        self.assertEquals(str(e.exception), expected)
        # assert str(e.value) == expected

    def test_convert_raw_to_asset_point_invalid_value(self):
        raw_data = ("EURUSD", "1.o007", "1641020400")
        expected = 'asset value should be numeric'

        with self.assertRaises(ValueError) as e:
            convert_raw_to_asset_point(raw_data)

        self.assertEquals(str(e.exception), expected)

    def test_convert_raw_to_asset_point_invalid_timestamp(self):
        raw_data = ("EURUSD", 1.0007, "16410204o0")
        expected = 'timestamp should be valid unix timestamp'

        with self.assertRaises(ValueError) as e:
            convert_raw_to_asset_point(raw_data)

        self.assertEquals(str(e.exception), expected)
