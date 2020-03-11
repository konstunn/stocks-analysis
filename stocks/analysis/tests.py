
import datetime

import pytz
from django.urls import reverse
from django.utils import timezone

from openapi_genclient import (
    MarketInstrumentListResponse, MarketInstrumentList, MarketInstrument, CandleResolution
)
from rest_framework import status

from stocks.analysis import tasks
from stocks.analysis.models import Candle, Instrument
from stocks.settings import TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN

from rest_framework.test import APITestCase
from openapi_client.openapi import sandbox_api_client


class TestGetInstrumentsTask(APITestCase):
    def test_(self):
        tasks.get_instruments.now()
        # if no exceptions were thrown, then everything was fine


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
        tasks.get_candles.now(figi, _from, to, granularity)
        self.assertEqual(45, Candle.objects.count())
        self.assertEqual(1, Instrument.objects.count())
        # plus, if no exceptions were thrown, then everything was fine

    def test_high_granularity(self):
        figi = self._get_figi()
        to = timezone.datetime(year=2020, month=2, day=15, tzinfo=pytz.UTC)
        _from = to - datetime.timedelta(days=14)
        granularity = CandleResolution.HOUR
        tasks.get_candles.now(figi, _from, to, granularity)

        # the amount of historical data is not going to change
        self.assertEqual(90, Candle.objects.count())
        self.assertEqual(1, Instrument.objects.count())
        # if no exceptions were thrown so far, then everything was fine


class TestCandlesViewSet(APITestCase):
    pass


class TestInstrumentsViewSet(APITestCase):
    pass


class TestTaskViewSet(APITestCase):
    def test_post_task_get_instruments(self):
        self.skipTest('skip')
        url = reverse('task-list')
        response = self.client.post(url, data=dict(action='get_instruments'))
        self.assertEqual(status.HTTP_200_OK, response.status_code,
                         response.content)

        from django.core.management import call_command
        #
        call_command('process_tasks')
