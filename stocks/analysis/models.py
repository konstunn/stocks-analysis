
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


class GetDataTask(models.Model):
    background_task = models.ForeignKey(Task, models.CASCADE, related_name='get_data_tasks', null=True)
    action = models.CharField(max_length=80)
    from_time = models.DateTimeField(null=True)
    to_time = models.DateTimeField(null=True)
    interval = models.CharField(max_length=10, null=True)
    figi = models.CharField(max_length=20, null=True)

    ctime = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True)
    end_at = models.DateTimeField(null=True, default=None)
    succeeded = models.BooleanField(null=True, default=None)

    class Meta:
        verbose_name = 'Прокси-задача'
        verbose_name_plural = 'Прокси-задачи'
