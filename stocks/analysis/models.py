from django.db import models

# Create your models here.


class Stock(models.Model):
    figi = models.CharField()
    ticker = models.CharField()


class Quote(models.Model):
    stock = models.ForeignKey(Stock, models.CASCADE, related_name='quotes')
    # datetime
    # price_open
    # price_high
    # price_low
    # price_close
