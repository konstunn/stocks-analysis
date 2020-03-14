import functools
import itertools
import math
import time
import logging
from typing import List
from datetime import datetime, timedelta

from django.conf import settings

from background_task import background
from django.utils import timezone

from openapi_client.openapi import sandbox_api_client, SandboxOpenApi

from openapi_genclient.models import \
    MarketInstrumentListResponse, MarketInstrumentList, MarketInstrument, SearchMarketInstrument

from openapi_genclient.models import Candles, Candle, CandleResolution
from openapi_genclient.models import Currency
from openapi_genclient.exceptions import ApiException

from stocks.analysis import models
from stocks.analysis.models import Instrument, GetDataTask
# from stocks.analysis.serializers import InstrumentSerializer, CandleSerializer
from stocks.analysis import serializers

DELAY_LIMIT = 120
DELAY_MULTIPLIER = 3


def get_next_delay(last_delay):
    next_delay = last_delay * DELAY_MULTIPLIER
    if next_delay > DELAY_LIMIT:
        next_delay = DELAY_LIMIT
    return next_delay


# there are little chances that our application could be banned and so that we will fail to handle rate limits
def retry_on_rate_limits_exception(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        delay = 1
        while True:
            try:
                return func(*args, **kwargs)
            except ApiException as exc:
                if exc.status == 429:
                    time.sleep(delay)
                    delay = get_next_delay(delay)
                else:
                    raise
    return wrapper


def update_get_data_task(func):
    @functools.wraps(func)
    def wrapper(*args, get_data_task_pk, **kwargs):
        task = GetDataTask.objects.get(pk=get_data_task_pk)
        task.started_at = timezone.now()
        task.save(update_fields=('started_at',))
        try:
            rez = func(*args, get_data_task_pk=get_data_task_pk, **kwargs)
        except Exception:
            logging.exception('exception occurred')
            task.succeeded = False
            raise
        else:
            task.succeeded = True
        finally:
            task.end_at = timezone.now()
            task.save(update_fields=('end_at', 'succeeded'))

        return rez

    return wrapper


@background
@update_get_data_task
@retry_on_rate_limits_exception
def get_instruments(*args, get_data_task_pk, **kwargs):
    currency = Currency.RUB
    logging.debug('started get_instruments()')
    tinkoff_client: SandboxOpenApi = sandbox_api_client(settings.TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN)

    response: MarketInstrumentListResponse = tinkoff_client.market.market_stocks_get()
    payload: MarketInstrumentList = response.payload
    instruments: List[MarketInstrument] = payload.instruments
    instruments = list(filter(lambda i: i.currency == currency, instruments))

    for instrument in instruments:
        data = instrument.to_dict()
        if not Instrument.objects.filter(figi=instrument.figi):
            instrument = serializers.InstrumentSerializer(data=data)
            instrument.is_valid(raise_exception=True)
            instrument.save()

    logging.debug('completed get_instruments()')


GRANULARITY_INTERVAL_TO_MAX_OVERALL_INTERVAL_MAP = {
    CandleResolution._1MIN: timedelta(days=1),
    CandleResolution._2MIN: timedelta(days=1),
    CandleResolution._3MIN: timedelta(days=1),
    CandleResolution._5MIN: timedelta(days=1),
    CandleResolution._10MIN: timedelta(days=1),
    CandleResolution._15MIN: timedelta(days=1),
    CandleResolution._30MIN: timedelta(days=1),
    CandleResolution.HOUR: timedelta(days=7),
    CandleResolution.DAY: timedelta(days=365),
    CandleResolution.WEEK: timedelta(days=365*2),
    CandleResolution.MONTH: timedelta(days=365*10)
}


# tinkoff openapi specific stuff
def get_max_overall_interval_from_granularity_interval(granularity_interval: str) -> timedelta:
    return GRANULARITY_INTERVAL_TO_MAX_OVERALL_INTERVAL_MAP[granularity_interval]


def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


@background
@update_get_data_task
def get_candles(*args, get_data_task_pk, **kwargs):
    task = GetDataTask.objects.get(pk=get_data_task_pk)
    granularity_interval = task.interval
    to = task.to_time
    _from = task.from_time
    figi = task.figi
    if granularity_interval not in CandleResolution.allowable_values:
        raise ValueError(f'granularity_interval = {granularity_interval} not in {CandleResolution.allowable_values}')

    overall_interval = to - _from
    max_overall_interval = get_max_overall_interval_from_granularity_interval(granularity_interval)

    sub_intervals_count = math.ceil(overall_interval / max_overall_interval)

    sub_interval_length = overall_interval / sub_intervals_count

    time_points = [_from + sub_interval_length * i for i in range(sub_intervals_count)]
    time_points.append(to)

    tinkoff_client: SandboxOpenApi = sandbox_api_client(settings.TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN)

    try:
        instrument = Instrument.objects.get(figi=figi)
    except Instrument.DoesNotExist:
        market_search_by_figi_with_retry_on_rate_limits = \
            retry_on_rate_limits_exception(tinkoff_client.market.market_search_by_figi_get)

        response: MarketInstrumentListResponse = market_search_by_figi_with_retry_on_rate_limits(figi)
        instrument: SearchMarketInstrument = response.payload
        instrument_serializer = serializers.InstrumentSerializer(data=instrument.to_dict())
        instrument_serializer.is_valid(raise_exception=True)
        instrument_serializer.save()

        instrument = instrument_serializer.instance

    for start, end in pairwise(time_points):

        market_candles_get_with_retry_on_rate_limits = \
            retry_on_rate_limits_exception(tinkoff_client.market.market_candles_get_with_http_info)

        response, status, headers = market_candles_get_with_retry_on_rate_limits(figi,
                                                                                 start,
                                                                                 end,
                                                                                 granularity_interval)

        payload: Candles = response.payload
        candles: List[Candle] = payload.candles

        for candle in candles:
            if not models.Candle.objects.filter(instrument=instrument, time=candle.time, interval=candle.interval):
                candle_serializer = serializers.CandleSerializer(data=candle.to_dict())
                candle_serializer.is_valid(raise_exception=True)
                candle_serializer.save()
