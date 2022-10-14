CURRENCY_TO_HANDLE = ('EURUSD', 'USDJPY', 'GBPUSD', 'AUDUSD', 'USDCAD')
QUANTIZE = '1000000.00000'


def cleanup_response(response: str) -> str:
    # remove prefix "null(" and suffix ");"
    r = response[5:-3]

    return r
