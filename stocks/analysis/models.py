
from django.db import models

from background_task.models import Task
from django.db.models import Count, Min, Max


class InstrumentManager(models.Manager):
    def with_candles(self):
        return self.annotate(
            candles_count=Count('candles'),
        ).filter(candles_count__gt=0)


class Instrument(models.Model):
    objects = InstrumentManager()

    figi = models.CharField(max_length=20, unique=True, db_index=True)
    ticker = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=256)
    type = models.CharField(max_length=20)
    isin = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return 'Instrument type={}, ticker={}, figi={}'.\
            format(self.type, self.ticker, self.figi)

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
