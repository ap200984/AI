# Weather Proxy Service

Асинхронный прокси-сервис к API погоды [Open-Meteo](https://open-meteo.com/).

## Технологии

- Python 3.12
- FastAPI
- Uvicorn
- httpx.AsyncClient-клиента (`httpx.get`)
- Pydantic
- UV
- Ruff

## Запуск

```bash
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## Конфигурация

| Параметр        | Значение по умолчанию                          | Описание                              |
|-----------------|-----------------------------------------------|--------------------------------------|
| `WEATHER_PROXY_UPSTREAM_URL` | `https://api.open-meteo.com/v1/forecast` | URL внешнего API |
| `WEATHER_PROXY_TIMEOUT_SECONDS` | `10.0` | Таймаут HTTP-запроса, сек |

Также можно создать файл `.env` с теми же переменными окружения.

Пример:

```bash
WEATHER_PROXY_UPSTREAM_URL=https://api.open-meteo.com/v1/forecast
WEATHER_PROXY_TIMEOUT_SECONDS=10.0
uv run uvicorn weather_proxy:app --host 0.0.0.0 --port 8000
```

## HTTP-запросы

### 1. GET /health

Проверка работоспособности сервиса.

```bash
curl http://127.0.0.1:8000/health
```

Ответ:

```json
{"status": "ok"}
```

### 2. GET /weather

Текущая погода для заданной координаты.

```bash
curl "http://127.0.0.1:8000/weather?latitude=36.72&longitude=-4.42"
```

Ответ:

```json
{
  "latitude": 36.72,
  "longitude": -4.42,
  "temperature": 20.4,
  "wind_speed": 19.6,
  "source": "open-meteo"
}
```

### 3. GET /forecast

Прогноз погоды на 1–7 дней.

```bash
curl "http://127.0.0.1:8000/forecast?latitude=36.72&longitude=-4.42&days=3"
```

Ответ:

```json
{
  "latitude": 36.72,
  "longitude": -4.42,
  "daily_forecasts": [
    {
      "time": "2026-11-19",
      "temperature_2m_max": 21.8,
      "wind_speed_10m_max": 25.8
    }
  ],
  "source": "open-meteo"
}
```

## Валидация

| Параметр       | Диапазон          |
|----------------|-------------------|
| `latitude`     | от -90 до 90     |
| `longitude`    | от -180 до 180   |
| `days`         | от 1 до 7        |

Некорректные значения возвращаются с кодом `422`. Ошибки внешнего API — с кодом `502`.

## Проверка кода

```bash
uv run ruff format
uv run ruff check
```