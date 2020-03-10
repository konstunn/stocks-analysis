from openapi_genclient import CandleResolution
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from stocks.analysis.models import Instrument, Candle, TaskProxy


class InstrumentSerializer(ModelSerializer):
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


ACTION_CHOICE = ('get_instruments', 'get_candles')


class GetInstrumentsTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskProxy
        fields = (
            'action'
        )

    action = serializers.ChoiceField(choices=('get_instruments',), required=True)
    task = serializers.PrimaryKeyRelatedField(read_only=True)


class TaskProxySerializer(serializers.ModelSerializer):
    action = serializers.ChoiceField(choices=ACTION_CHOICE, required=True)
    interval = serializers.ChoiceField(choices=CandleResolution.allowable_values, required=False)
    _from = serializers.DateTimeField(source='from', required=False)
    to = serializers.DateTimeField(required=False)
    figi = serializers.CharField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        action = attrs['action']

        if action == 'get_instruments':  # TODO: make a enum
            if len(attrs) > 1:
                raise ValidationError('extra fields {} for action = {}'.format(attrs.pop('action'), action))
        elif action == 'get_candles':
            _from = attrs.get('from')
            to = attrs.get('to')
            figi = attrs.g

            if not _from or not to or _from >= to:
                raise ValidationError(
                    'datetimes "from" and "to" required, such that from < to, but {} >= {}'.format(_from, to))

        return attrs

    def create(self, validated_data):
        # TODO: schedule task
        pass
