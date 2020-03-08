
from django.db import models


class Instrument(models.Model):
    figi = models.CharField(max_length=20)
    ticker = models.CharField(max_length=20)
    name = models.CharField(max_length=256)
    type = models.CharField(max_length=20)
    isin = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Инструмент'
        verbose_name_plural = 'Инструменты'


class Candle(models.Model):
    instrument = models.ForeignKey(Instrument, models.CASCADE, related_name='candles')
    time = models.DateTimeField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    interval = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'Котировка'
        verbose_name_plural = 'Котировки'
