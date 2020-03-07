
import os
import datetime
from datetime import timezone
from django.utils import timezone

import openapi_genclient
from openapi_genclient import (
    MarketInstrumentListResponse, MarketInstrumentList, MarketInstrument, CandlesResponse, CandleResolution
)
from rest_framework import status

from stocks.analysis.tasks import get_instruments_with_retry_on_rate_limit
from stocks.settings import TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN

from rest_framework.test import APITestCase
from openapi_client.openapi import sandbox_api_client
import requests


class TestTinkoffInvestmentsAPI(APITestCase):
    def test_get(self):
        tinkoff_client = sandbox_api_client(TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN)
        #

        alrs: MarketInstrumentListResponse = tinkoff_client.market.market_search_by_ticker_get('ALRS')

        payload: MarketInstrumentList = alrs.payload
        alrs: MarketInstrument = payload.instruments[0]

        to = timezone.now()
        days = 365
        start = to - datetime.timedelta(days=days)
        interval = CandleResolution._1MIN

        for i in range(days):
            _from = start + datetime.timedelta(days=i)
            to = start + datetime.timedelta(days=i+1)

            candles_response: CandlesResponse = tinkoff_client.market.market_candles_get(alrs.figi, _from, to, interval)
            from pprint import pprint
            pprint(candles_response)
            print(len(candles_response.payload.candles))
    pass

    def test_foo(self):
        get_instruments_with_retry_on_rate_limit()


class TestGetLiquidStocks(APITestCase):
    def test_get_from_moex(self):
        url = 'https://iss.moex.com/iss/statistics/engines/stock/markets/index/analytics/MOEXBC.json'
        response = requests.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        url = 'https://iss.moex.com/iss/engines/stock/'

    pass
