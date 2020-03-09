
from django.db import models

from background_task.models import Task


class Instrument(models.Model):
    figi = models.CharField(max_length=20, unique=True, db_index=True)
    ticker = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=256)
    type = models.CharField(max_length=20)
    isin = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name = 'Инструмент'
        verbose_name_plural = 'Инструменты'


class Candle(models.Model):
    instrument = models.ForeignKey(Instrument, models.CASCADE, related_name='candles', db_index=True)
    time = models.DateTimeField(db_index=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    interval = models.CharField(max_length=10, db_index=True)

    class Meta:
        verbose_name = 'Котировка'
        verbose_name_plural = 'Котировки'


class TaskProxy(Task):
    action = models.CharField(max_length=80)
    _from = models.DateTimeField(name='from', null=True)
    to = models.DateTimeField(null=True)
    interval = models.CharField(max_length=10, null=True)
    figi = models.CharField(max_length=20, null=True)

    class Meta:
        verbose_name = 'Прокси-задача'
        verbose_name_plural = 'Прокси-задачи'
