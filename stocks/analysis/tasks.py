import functools
import itertools
import time
from typing import List
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction

from stocks.analysis.models import Instrument
from stocks.analysis.serializers import InstrumentFromTinkoffSerializer

from openapi_client.openapi import sandbox_api_client, SandboxOpenApi
from openapi_genclient.models import MarketInstrumentListResponse, MarketInstrumentList, MarketInstrument
from openapi_genclient.models import Candles, Candle, CandlesResponse, CandleResolution
from openapi_genclient.models import Currency
from openapi_genclient.exceptions import ApiException


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
                    delay *= 2
                else:
                    raise
    return wrapper


@retry_on_rate_limits_exception
def get_instruments(currency=Currency.RUB):
    tinkoff_client: SandboxOpenApi = sandbox_api_client(settings.TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN)

    response: MarketInstrumentListResponse = tinkoff_client.market.market_stocks_get()
    payload: MarketInstrumentList = response.payload
    instruments: List[MarketInstrument] = payload.instruments
    instruments = list(filter(lambda i: i.currency == currency, instruments))

    with transaction.atomic():
        for instrument in instruments:
            data = instrument.to_dict()
            instrument = InstrumentFromTinkoffSerializer(data=data)
            instrument.is_valid(raise_exception=True)
            instrument.save()


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


def get_candles(figi: str, _from: datetime, to: datetime, granularity_interval: str):
    if granularity_interval not in CandleResolution.allowable_values:
        raise ValueError(f'granularity_interval = {granularity_interval} not in {CandleResolution.allowable_values}')

    overall_interval = to - _from
    max_overall_interval = get_max_overall_interval_from_granularity_interval(granularity_interval)

    sub_intervals_count = overall_interval // max_overall_interval + 1

    sub_interval_length = overall_interval / sub_intervals_count

    time_points = [_from + sub_interval_length * i for i in range(sub_intervals_count)]
    time_points.append(to)

    tinkoff_client: SandboxOpenApi = sandbox_api_client(settings.TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN)

    with transaction.atomic():

        instrument = Instrument.objects.filter(figi=figi)
        if not instrument:
            market_search_by_figi_with_retry_on_rate_limits = \
                retry_on_rate_limits_exception(tinkoff_client.market.market_search_by_figi_get)

            response: MarketInstrumentListResponse = market_search_by_figi_with_retry_on_rate_limits(figi)
            payload: MarketInstrumentList = response.payload
            instruments: List[MarketInstrument] = payload.instruments
            instrument = instruments[0]
            instrument_serializer = InstrumentFromTinkoffSerializer(data=instrument.to_dict())
            instrument_serializer.is_valid(raise_exception=True)
            instrument_serializer.save()

        for start, end in pairwise(time_points):

            market_candles_get_with_retry_on_rate_limits = \
                retry_on_rate_limits_exception(tinkoff_client.market.market_candles_get)

            response: CandlesResponse = market_candles_get_with_retry_on_rate_limits(figi,
                                                                                     start,
                                                                                     end,
                                                                                     granularity_interval)

            payload: Candles = response.payload
            candles: List[Candle] = payload.candles

            for candle in candles:
                # TODO: serialize and save candles
                raise NotImplementedError('not implemented yet')
                pass
