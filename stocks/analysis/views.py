from django.db.models import Min, Max
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins

from stocks.analysis import models
from stocks.analysis.serializers import \
    InstrumentSerializer, \
    CandleSerializer, \
    GetInstrumentsTaskSerializer, GetCandlesTaskSerializer, SummarySerializer


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

    def get_queryset(self):
        if self.action == 'summary':
            queryset = models.Instrument.objects.with_candles().order_by('ticker')
            return queryset
        else:
            return models.Instrument.objects.all().order_by('ticker')

    def filter_queryset(self, queryset):
        if self.action == 'summary':

            from_time = self.request.query_params.get('from', None)
            if from_time is not None:
                queryset = queryset.annotate(
                    candles_min_time=Min('candles__time')
                ).filter(candles_min_time__lte=from_time)

            to = self.request.query_params.get('to', None)
            if to is not None:
                queryset = queryset.annotate(
                    candles_max_time=Max('candles__time')
                ).filter(candles_max_time__gte=to)

            return queryset
        else:
            return super().filter_queryset(queryset)

    def get_serializer_class(self):
        if self.action == 'summary':
            return SummarySerializer
        else:
            return InstrumentSerializer

    @action(detail=False, methods=['get'])
    def summary(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CandleViewSet(mixins.ListModelMixin,
                    GenericViewSet):
    serializer_class = CandleSerializer
    queryset = models.Candle.objects.all().order_by('-time')
