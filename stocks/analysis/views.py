from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, status

from stocks.analysis import models
from stocks.analysis.serializers import \
    InstrumentSerializer, \
    CandleSerializer, \
    GetInstrumentsTaskSerializer, GetCandlesTaskSerializer


class TaskViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    queryset = models.GetDataTask.objects.all().order_by('-ctime')

    def get_serializer_class(self):
        if self.action == 'get_instruments':
            return GetInstrumentsTaskSerializer
        elif self.action == 'get_candles':
            return GetCandlesTaskSerializer
        else:
            return GetInstrumentsTaskSerializer

    @action(detail=False, methods=['post'])
    def get_instruments(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def get_candles(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class InstrumentViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        GenericViewSet):
    queryset = models.Instrument.objects.all().order_by('ticker')
    serializer_class = InstrumentSerializer

    # @action(detail=False, methods=['get'])
    # def candles(self, request, *args, **kwargs):
    #     pass

    @action(detail=False, methods=['get'])
    def summary(self, request, *args, **kwargs):
        raise NotImplementedError('not implemented yet')


class CandleViewSet(mixins.ListModelMixin,
                    GenericViewSet):
    serializer_class = CandleSerializer
    queryset = models.Candle.objects.all().order_by('-time')
