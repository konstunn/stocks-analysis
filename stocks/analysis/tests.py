
import os
import datetime

import pytz
from django.utils import timezone

import openapi_genclient
from openapi_genclient import (
    MarketInstrumentListResponse, MarketInstrumentList, MarketInstrument, CandlesResponse, CandleResolution,
    ApiException)
from rest_framework import status

from stocks.analysis import tasks
from stocks.analysis.models import Candle, Instrument
from stocks.analysis.tasks import get_instruments, retry_on_rate_limits_exception
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


class TestGetCandlesTask(APITestCase):
    @staticmethod
    def _get_figi():
        ticker = 'ALRS'

        tinkoff_client = sandbox_api_client(TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN)
        response: MarketInstrumentListResponse = tinkoff_client.market.market_search_by_ticker_get(ticker)

        payload: MarketInstrumentList = response.payload
        instrument: MarketInstrument = payload.instruments[0]

        return instrument.figi

    def test_low_granularity(self):
        figi = self._get_figi()
        to = timezone.datetime(year=2020, month=2, day=8, tzinfo=pytz.UTC)
        _from = to - datetime.timedelta(days=7)
        granularity = CandleResolution.HOUR
        tasks.get_candles(figi, _from, to, granularity)
        self.assertEqual(45, Candle.objects.count())
        self.assertEqual(1, Instrument.objects.count())
        # plus, if no exceptions were thrown, then everything was fine

    def test_high_granularity(self):
        figi = self._get_figi()
        to = timezone.datetime(year=2020, month=2, day=15, tzinfo=pytz.UTC)
        _from = to - datetime.timedelta(days=14)
        granularity = CandleResolution.HOUR
        tasks.get_candles(figi, _from, to, granularity)
        self.assertEqual(90, Candle.objects.count())
        self.assertEqual(1, Instrument.objects.count())
        # plus, if no exceptions were thrown, then everything was fine
