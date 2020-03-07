import time
from typing import List

from django.conf import settings
from django.db import transaction
from stocks.analysis.serializers import InstrumentFromTinkoffSerializer

from openapi_client.openapi import sandbox_api_client, SandboxOpenApi
from openapi_genclient.models import MarketInstrumentListResponse, MarketInstrumentList, MarketInstrument
from openapi_genclient.models import Candles, Candle, CandlesResponse
from openapi_genclient.models import Currency
from openapi_genclient.exceptions import ApiException


# run in background on demand
def get_instruments_with_retry_on_rate_limit(currency=Currency.RUB):
    while True:
        try:
            tinkoff_client: SandboxOpenApi = sandbox_api_client(settings.TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN)

            response: MarketInstrumentListResponse = tinkoff_client.market.market_stocks_get()
            payload: MarketInstrumentList = response.payload
            instruments: List[MarketInstrument] = payload.instruments
            instruments = list(filter(lambda i: i.currency == currency, instruments))

            # TODO: wrap this in a transaction

            with transaction.atomic():
                for instrument in instruments:
                    data = instrument.to_dict()
                    instrument = InstrumentFromTinkoffSerializer(data=data)
                    instrument.is_valid(raise_exception=True)
                    instrument.save()

            break

        except ApiException as exc:
            if exc.status == 429:
                time.sleep(1)
                continue
            elif exc.status == 500:
                raise
        except Exception as exc:
            raise


def get_stocks():
    pass


# run regularly or on demand
def get_liquid_stocks_from_moex():
    pass
