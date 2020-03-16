# stock-analysis

# Задача

Разработать приложение для анализа информации по ликвидным российским акциям.

В приложении должно быть:

1) Возможность задать список акций, для закачки данных.
2) Механизм получения и сохранения котировок (OHLC) по заданным инструментам за 
произвольный период времени.
3) Веб-сервис, в котором будет реализован метод "get_summary", который вернет список 
всех сохраненных инструментов и процент(%) изменения цены для каждого инструмента за 
заданный промежуток времени.
4) Инструкция по запуску и использованию.

# Описание возможных решений задачи

## Источники данных

Получать данные будем через Tinkoff Инвестиции OpenAPI.

## Асинхронные фоновые запросы к источникам данных

Т.к. запросы к источникам данных могут занимать секунды и более, если данных много, 
то будем выполнять запросы асинхронно в фоновом режиме. Для простоты и скорости разработки
будем использовать django-background-tasks.

# Инструкция по запуску и использованию

Потребуется docker и docker-compose.

1. Склонировать репозиторий

```
git clone https://github.com/konstunn/stocks-analysis.git
cd stocks-analysis
```

 Положить токен от песочницы Тинькофф Инвестиции в файл .env в виде
```
TINKOFF_INVESTMENTS_SANDBOX_OPEN_API_TOKEN=THETOKEN
```

2. Собрать образ

```
docker-compose build
```

3. Запустить автотесты

```
docker-compose run web manage.py test -v=3
```

4. Поднять все сервисы (pg, bg-tasks, web)

```
docker-compose up
```

5. Создать задачу на синхронизацию списков акций

```
curl -X POST http://localhost:8000/tasks/get_instruments/
```

В отчет получите подобное

```
{
    "action": "get_instruments",
    "background_task": 1,
    "ctime": "2020-03-16T17:09:04.745378Z",
    "end_at": null,
    "id": 1,
    "succeeded": null
}
```


6. Получить список фоновых задач

```
curl http://localhost:8000/tasks/
```

В ответ получите

```
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "action": "get_instruments",
            "background_task": null,
            "ctime": "2020-03-16T17:09:04.745378Z",
            "end_at": "2020-03-16T17:09:11.900216Z",
            "id": 1,
            "succeeded": true
        }
    ]
}
```

    "succeeded": true
    "end_at": "2020-03-16T17:09:11.900216Z",
    
Значит задача успешно выполнена. Можно использовать результаты. 
Если задача не выполнилась, нужно подождать и попробовать снова. 
Если succeeded == False, значит задание провалено.

7. Получим синхронизированный список инструментов

```
curl http://localhost:8000/instruments/
```

В ответ получите подобное

```
{
    "count": 131,
    "next": "http://localhost:8000/instruments/?page=2",
    "previous": null,
    "results": [
        {
            "figi": "BBG002W2FT69",
            "isin": "RU000A0JS5T7",
            "name": "\u0410\u0431\u0440\u0430\u0443\u0414\u044e\u0440\u0441\u043e",
            "ticker": "ABRD",
            "type": "Stock"
        },
        {
            "figi": "BBG004S68614",
            "isin": "RU000A0DQZE3",
            "name": "\u0410\u0424\u041a \u0421\u0438\u0441\u0442\u0435\u043c\u0430",
            "ticker": "AFKS",
            "type": "Stock"
        },
        {
            "figi": "BBG004S683W7",
            "isin": "RU0009062285",
            "name": "\u0410\u044d\u0440\u043e\u0444\u043b\u043e\u0442",
            "ticker": "AFLT",
            "type": "Stock"
        },
        {
            "figi": "BBG007N0Z367",
            "isin": "US7496552057",
            "name": "\u0420\u0443\u0441\u0410\u0433\u0440\u043e",
            "ticker": "AGRO",
            "type": "Stock"
        },
        {
            "figi": "BBG004S688G4",
            "isin": "RU0009028674",
            "name": "\u0410\u043a\u0440\u043e\u043d",
            "ticker": "AKRN",
            "type": "Stock"
        },
        {
            "figi": "BBG002B25NL9",
            "isin": "RU000A0JP468",
            "name": "\u0410\u041b\u0420\u041e\u0421\u0410-\u041d\u044e\u0440\u0431\u0430",
            "ticker": "ALNU",
            "type": "Stock"
        },
        {
            "figi": "BBG004S68B31",
            "isin": "RU0007252813",
            "name": "\u0410\u041b\u0420\u041e\u0421\u0410",
            "ticker": "ALRS",
            "type": "Stock"
        },
    ]
}
```

8. Создадим задачу на получение данных о котировках акций АЛРОСА, например.

```
curl --header "Content-Type: application/json" \
  --request POST \
  --data \
  '{  
       "figi": "BBG004S68B31",
       "from_time": "2020-02-01 12:00:00Z", 
       "to_time": "2020-02-07 12:00:00Z",
       "interval": "1min"
   }' \
  http://localhost:8000/tasks/get_candles/
```

В ответ получим задачу

```
{
    "action": "get_candles",
    "background_task": 2,
    "ctime": "2020-03-16T17:27:17.753879Z",
    "end_at": null,
    "figi": "BBG004S68B31",
    "from_time": "2020-02-01T12:00:00Z",
    "id": 2,
    "interval": "1min",
    "succeeded": null,
    "to_time": "2020-02-07T12:00:00Z"
}
```

9. Получим статус задачи

```
curl http://localhost:8000/tasks/2/
```

Получим ответ

```
{
    "action": "get_candles",
    "background_task": null,
    "ctime": "2020-03-16T17:27:17.753879Z",
    "end_at": "2020-03-16T17:28:00.182647Z",
    "id": 2,
    "succeeded": true
}
```

Задача выполнена. Если задача не выполнена, придется подождать, периодически опрашивая ресурс.

10. Получить данные о котировках

```
curl http://localhost:8000/candles/
```

Получим нечто такое

```
{
    "count": 2398,
    "next": "http://localhost:8000/candles/?page=2",
    "previous": null,
    "results": [
        {
            "c": 83.72,
            "figi": "BBG004S68B31",
            "h": 83.72,
            "l": 83.69,
            "o": 83.69,
            "time": "2020-02-07T11:59:00Z"
        },
        {
            "c": 83.7,
            "figi": "BBG004S68B31",
            "h": 83.7,
            "l": 83.69,
            "o": 83.69,
            "time": "2020-02-07T11:58:00Z"
        },
        {
            "c": 83.69,
            "figi": "BBG004S68B31",
            "h": 83.7,
            "l": 83.66,
            "o": 83.66,
            "time": "2020-02-07T11:57:00Z"
        }
    ]
}
```

11. Можно запросить "сводку" (summary)

```
curl --header "Content-Type: application/json" \
  --request GET \
  -d from="2020-02-02 12:00:00Z" \
  -d to="2020-02-04 12:00:00Z" \
  http://localhost:8000/instruments/summary/
```

Получим

```
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "absolute_diff": 3.7,
            "begin": 79.99,
            "end": 83.72,
            "figi": "BBG004S68B31",
            "name": "\u0410\u041b\u0420\u041e\u0421\u0410",
            "relative_diff_percents": 5.0,
            "ticker": "ALRS"
        }
    ]
}
```

При наличии данных о котировках других акций они тоже будут включены в выдачу.