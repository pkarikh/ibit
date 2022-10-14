from decimal import Decimal

ASSETS_MAPPING_BY_ID = {1: "EURUSD",
                        2: "USDJPY",
                        3: "GBPUSD",
                        4: "AUDUSD",
                        5: "USDCAD"}

ASSETS_MAPPING_BY_SYMBOL = {"EURUSD": 1,
                            "USDJPY": 2,
                            "GBPUSD": 3,
                            "AUDUSD": 4,
                            "USDCAD": 5}

ASSETS = [{"id": 1, "name": "EURUSD"},
          {"id": 2, "name": "USDJPY"},
          {"id": 3, "name": "GBPUSD"},
          {"id": 4, "name": "AUDUSD"},
          {"id": 5, "name": "USDCAD"}]


class AssetPoint:
    def __init__(self, asset_type: str, value: Decimal, timestamp: int):
        self.asset_type = asset_type
        self.value = value
        self.timestamp = timestamp

    @property
    def asset_type(self):
        return self._asset_type

    @asset_type.setter
    def asset_type(self, value):
        valid_symbols = ASSETS_MAPPING_BY_SYMBOL.keys()

        if value not in valid_symbols:
            raise ValueError("Invalid asset type {asset_type}. "
                             "Expected one of: {allowed_symbols}".format(
                              allowed_symbols=",".join(valid_symbols),
                              asset_type=value))
        self._asset_type = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValueError("asset value should be numeric")
        self._value = value

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        try:
            int(value)
        except ValueError:
            raise ValueError("timestamp should be valid unix timestamp")
        self._timestamp = value

    def to_dict(self) -> dict:
        result = {"assetName": self.asset_type, "time": self.timestamp,
                  "assetId": ASSETS_MAPPING_BY_SYMBOL[self.asset_type],
                  "value": str(self.value)}

        return result

