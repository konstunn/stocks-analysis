
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from stocks.analysis.models import Instrument, Candle


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


class CandleSerializer(ModelSerializer):
    o = serializers.FloatField(source='open')
    h = serializers.FloatField(source='high')
    l = serializers.FloatField(source='low')
    c = serializers.FloatField(source='close')
    time = serializers.DateTimeField()
    figi = serializers.SlugRelatedField(slug_field='figi', queryset=Instrument.objects.all(), source='instrument')

    class Meta:
        model = Candle
        fields = (
            'time',
            'o',
            'h',
            'l',
            'c',
            'figi'
        )
