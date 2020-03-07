
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
    # datetime
    # price_open
    # price_high
    # price_low
    # price_close

    class Meta:
        verbose_name = 'Котировка'
        verbose_name_plural = 'Котировки'
