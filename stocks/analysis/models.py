
from django.db import models


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
