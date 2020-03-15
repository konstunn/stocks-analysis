
import datetime
import logging

import pytz

from django.urls import reverse
from django.utils import timezone
from django.core.management import call_command

from rest_framework import status
from rest_framework.test import APITestCase

from openapi_client.openapi import sandbox_api_client
from openapi_genclient import (
    MarketInstrumentListResponse,
    MarketInstrumentList,
    MarketInstrument,
    CandleResolution
)

from stocks.analysis import tasks, serializers, models
from stocks.analysis.models import Candle, Instrument
from stocks.settings import TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN


class TestGetInstrumentsTask(APITestCase):
    def test_(self):
        task = models.GetDataTask.objects.create(action='get_data_task')
        tasks.get_instruments.now(get_data_task_pk=task.pk)
        self.assertGreater(Instrument.objects.count(), 0)
        # if no exceptions were thrown, then everything was fine


def get_figi():
    ticker = 'ALRS'

    tinkoff_client = sandbox_api_client(TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN)
    response: MarketInstrumentListResponse = tinkoff_client.market.market_search_by_ticker_get(ticker)

    payload: MarketInstrumentList = response.payload
    instrument: MarketInstrument = payload.instruments[0]

    return instrument.figi


class TestGetCandlesTask(APITestCase):

    def test_low_granularity(self):
        figi = get_figi()
        to = timezone.datetime(year=2020, month=2, day=8, tzinfo=pytz.UTC)
        _from = to - datetime.timedelta(days=7)
        granularity = CandleResolution.HOUR
        task = models.GetDataTask.objects.create(figi=figi, from_time=_from, to_time=to, interval=granularity)
        tasks.get_candles.now(get_data_task_pk=task.pk)

        # the amount of historical data is not going to change
        self.assertEqual(45, Candle.objects.count())
        self.assertEqual(1, Instrument.objects.count())
        # plus, if no exceptions were thrown, then everything was fine

    def test_high_granularity(self):
        figi = get_figi()
        to = timezone.datetime(year=2020, month=2, day=15, tzinfo=pytz.UTC)
        _from = to - datetime.timedelta(days=14)
        granularity = CandleResolution.HOUR
        task = models.GetDataTask.objects.create(figi=figi, from_time=_from, to_time=to, interval=granularity)
        tasks.get_candles.now(get_data_task_pk=task.pk)

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
        url = reverse('task-get-instruments')
        response = self.client.post(url, data=dict(action='get_instruments'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code,
                         response.content)
        call_command('process_tasks', duration=3, verbosity=3)
        self.assertGreater(Instrument.objects.count(), 0)

    def test_post_task_get_candles(self):
        url = reverse('task-get-instruments')
        response = self.client.post(url, data=dict(action='get_instruments'))
        self.assertEqual(status.HTTP_201_CREATED, response.status_code,
                         response.content)
        call_command('process_tasks', duration=5, verbosity=3)

        to = timezone.datetime(year=2020, month=2, day=15, tzinfo=pytz.UTC)
        _from = to - datetime.timedelta(days=14)
        granularity = CandleResolution.HOUR

        url = reverse('task-get-candles')
        data = {
            'action': 'get_candles',
            'from_time': _from,
            'to_time': to,
            'figi': get_figi(),
            'interval': granularity
        }
        response = self.client.post(url, data=data)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code,
                         response.content)
        call_command('process_tasks', duration=5, verbosity=3)
        self.assertEqual(90, Candle.objects.count())
        self.assertGreater(Instrument.objects.count(), 0)
