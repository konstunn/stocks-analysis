
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


class TestInstruments(APITestCase):
    def test_(self):
        url = reverse('task-get-instruments')
        data = dict(action='get_instruments')
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self.assertEqual(models.Task.objects.count(), 1)
        self.assertEqual(models.GetDataTask.objects.count(), 1)

        url = reverse('task-list')
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        task: models.GetDataTask = models.GetDataTask.objects.first()
        self.assertIsNone(task.end_at)
        self.assertFalse(task.succeeded)

        tasks.get_instruments.now(get_data_task_pk=task.pk)

        task.refresh_from_db()
        self.assertIsNotNone(task.end_at)
        self.assertTrue(task.succeeded)
        self.assertGreater(Instrument.objects.count(), 0)

        url = reverse('instrument-list')
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        instrument = Instrument.objects.first()
        url = reverse('instrument-detail', kwargs=dict(pk=instrument.pk))
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)


def get_figi():
    ticker = 'ALRS'

    tinkoff_client = sandbox_api_client(TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN)
    response: MarketInstrumentListResponse = tinkoff_client.market.market_search_by_ticker_get(ticker)

    payload: MarketInstrumentList = response.payload
    instrument: MarketInstrument = payload.instruments[0]

    return instrument.figi


class TestCandles(APITestCase):

    def test_low_granularity(self):
        figi = get_figi()
        to = timezone.datetime(year=2020, month=2, day=8, tzinfo=pytz.UTC)
        _from = to - datetime.timedelta(days=7)
        granularity = CandleResolution.HOUR

        url = reverse('task-get-candles')
        data = {
            'figi': figi,
            'from_time': _from,
            'to_time': to,
            'interval': granularity
        }
        response = self.client.post(url, data=data)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        task = models.GetDataTask.objects.first()
        self.assertIsNone(task.end_at)
        self.assertFalse(task.succeeded)

        url = reverse('task-list')
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        tasks.get_candles.now(get_data_task_pk=task.pk)

        task.refresh_from_db()
        self.assertTrue(task.succeeded)
        self.assertIsNotNone(task.end_at)

        # the amount of historical data is not going to change
        self.assertEqual(45, Candle.objects.count())
        self.assertEqual(1, Instrument.objects.count())

        url = reverse('candle-list')
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_high_granularity(self):
        # TODO: reduce copy-paste
        figi = get_figi()
        to = timezone.datetime(year=2020, month=2, day=15, tzinfo=pytz.UTC)
        _from = to - datetime.timedelta(days=14)
        granularity = CandleResolution.HOUR

        url = reverse('task-get-candles')
        data = {
            'figi': figi,
            'from_time': _from,
            'to_time': to,
            'interval': granularity
        }
        response = self.client.post(url, data=data)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        task = models.GetDataTask.objects.first()
        self.assertIsNone(task.end_at)
        self.assertFalse(task.succeeded)

        url = reverse('task-list')
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        tasks.get_candles.now(get_data_task_pk=task.pk)

        task.refresh_from_db()
        self.assertTrue(task.succeeded)
        self.assertIsNotNone(task.end_at)

        # the amount of historical data is not going to change
        self.assertEqual(90, Candle.objects.count())
        self.assertEqual(1, Instrument.objects.count())

        url = reverse('candle-list')
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        # TODO: implement summary
        url = reverse('instrument-summary')
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
