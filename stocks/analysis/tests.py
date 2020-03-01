
import os

from stocks.settings import TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN

from rest_framework.test import APITestCase
import openapi_client
from openapi_client.openapi import sandbox_api_client
import requests


class TestTinkoffInvestmentsAPI(APITestCase):
    def test_get(self):
        tinkoff_client = sandbox_api_client(TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN)
        # rez = tinkoff_client.market.market_orderbook_get('AAPL', 2)
        rez = tinkoff_client.market.market_stocks_get()
        # tinkoff_client.market.market_search_by_figi_get_with_http_info()
        print(rez)
        # print(TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN)
        # response = requests.get(url)
        from pprint import pprint
        # data = response.json()
        # print(response)
    pass
