from django.shortcuts import render
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins

from stocks.analysis.serializers import InstrumentSerializer, CandleSerializer


class TaskViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):

    pass


class InstrumentViewSet(mixins.ListModelMixin,
                        GenericViewSet):
    serializer_class = InstrumentSerializer


class CandleViewSet(mixins.ListModelMixin,
                    GenericViewSet):
    serializer_class = CandleSerializer
