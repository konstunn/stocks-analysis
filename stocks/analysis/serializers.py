from openapi_genclient import CandleResolution

from rest_framework.exceptions import ValidationError, MethodNotAllowed
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from background_task.models import Task as BackgroundTask

from stocks.analysis.models import Instrument, Candle
from stocks.analysis import models
from stocks.analysis import tasks


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
        model = models.GetDataTask
        fields = (
            'id',
            'background_task',
            'action',
            'ctime',
            'end_at',
            'succeeded'
        )

    action = serializers.ChoiceField(choices=('get_instruments',), default='get_instruments')
    id = serializers.IntegerField(read_only=True)
    background_task = serializers.PrimaryKeyRelatedField(read_only=True)
    succeeded = serializers.BooleanField(read_only=True)
    end_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        instance = super().create(validated_data)
        task = tasks.get_instruments(get_data_task_pk=instance.pk)
        instance.background_task = task
        instance.save(update_fields=('background_task',))
        return instance

    def update(self, instance, validated_data):
        raise MethodNotAllowed('task updates are not supported')


class GetCandlesTaskSerializer(serializers.ModelSerializer):
    action = serializers.CharField(default='get_candles')
    interval = serializers.ChoiceField(choices=CandleResolution.allowable_values)
    from_time = serializers.DateTimeField(required=True)
    to_time = serializers.DateTimeField(required=True)
    # figi = serializers.SlugRelatedField(slug_field='figi', queryset=Instrument.objects.all())
    figi = serializers.CharField()

    class Meta:
        model = models.GetDataTask
        fields = (
            'id',
            'background_task',
            'action',
            'ctime',
            'end_at',
            'succeeded',
            'to_time',
            'from_time',
            'interval',
            'figi'
        )

    id = serializers.IntegerField(read_only=True)
    background_task = serializers.PrimaryKeyRelatedField(read_only=True)

    def create(self, validated_data):
        instance = super().create(validated_data)
        task = tasks.get_candles(get_data_task_pk=instance.pk)
        instance.background_task = task
        instance.save(update_fields=('background_task',))
        return instance

    def update(self, instance, validated_data):
        raise MethodNotAllowed('task updates are not supported')


class SummarySerializer(serializers.ModelSerializer):
    begin = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()
    absolute_diff = serializers.SerializerMethodField()
    relative_diff_percents = serializers.SerializerMethodField()

    class Meta:
        model = models.Instrument
        fields = (
            'figi',
            'ticker',
            'begin',
            'end',
            'name',
            'absolute_diff',
            'relative_diff_percents'
        )

    def get_end(self, instance):
        request = self.context['request']
        candles_queryset = instance.candles.order_by('-time')

        to_time = request.query_params.get('to', None)
        if to_time is not None:
            candles_queryset = candles_queryset.filter(time__lte=to_time)

        return candles_queryset.first().close

    def get_begin(self, instance):
        request = self.context['request']
        candles_queryset = instance.candles.order_by('time')

        from_time = request.query_params.get('from', None)
        if from_time is not None:
            candles_queryset = candles_queryset.filter(time__gte=from_time)

        return candles_queryset.first().open

    def get_absolute_diff(self, instance):
        end = self.get_end(instance)
        begin = self.get_begin(instance)
        return round(end - begin, 1)

    def get_relative_diff_percents(self, instance):
        abs_diff = self.get_absolute_diff(instance)
        begin = self.get_begin(instance)
        return round(abs_diff / begin, 2) * 100