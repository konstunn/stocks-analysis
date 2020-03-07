
from rest_framework.serializers import ModelSerializer

from stocks.analysis.models import Instrument


class InstrumentFromTinkoffSerializer(ModelSerializer):
    class Meta:
        model = Instrument
        fields = (
            'figi',
            'isin',
            'ticker',
            'name',
            'type'
        )
