import httpx
from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel
from typing import Literal
from datetime import datetime, timezone
from settings import OPEN_METEO_BASE_URL, API_TIMEOUT

# --- Pydantic Models ---

# Note: We removed the wrapper Pydantic model for coordinates, as they are now passed as Query parameters.


class WeatherDataResponse(BaseModel):
    latitude: float
    longitude: float
    temperature: float
    wind_speed: float
    source: Literal["open-meteo"]


class DailyForecast(BaseModel):
    time: str
    temperature_2m_max: float
    wind_speed_10m_max: float


class ForecastResponse(BaseModel):
    latitude: float
    longitude: float
    daily_forecasts: list[DailyForecast]
    source: Literal["open-meteo"]


# --- App Initialization ---
app = FastAPI(
    title="Weather Proxy", description="Proxy service for Open-Meteo API with normalized responses."
)

# --- API Endpoints ---


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/weather", response_model=WeatherDataResponse)
async def get_weather(
    latitude: float = Query(..., ge=-90, le=90), longitude: float = Query(..., ge=-180, le=180)
):
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        # NOTE: The /current endpoint is no longer served by Open-Meteo (HTTP 404).
        # Current conditions are taken from the hourly series of /v1/forecast,
        # restricted to a single day (forecast_days=1).
        url = (
            f"{OPEN_METEO_BASE_URL}/v1/forecast"
            f"?latitude={latitude}&longitude={longitude}"
            f"&hourly=temperature_2m,wind_speed_10m&forecast_days=1&timezone=auto"
        )

        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Open-Meteo API error.")
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to Open-Meteo: {e}",
            )

        # Normalize the response
        try:
            hourly = data["hourly"]
            # The hourly time series is ISO 8601, so the current step index is the current hour.
            hour_index = int(datetime.now(timezone.utc).hour)

            temperature = float(hourly["temperature_2m"][hour_index])
            wind_speed = float(hourly["wind_speed_10m"][hour_index])

            return WeatherDataResponse(
                latitude=latitude,
                longitude=longitude,
                temperature=temperature,
                wind_speed=wind_speed,
                source="open-meteo",
            )
        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected structure in Open-Meteo response: Missing key {e}",
            )
        except IndexError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Open-Meteo did not provide enough hourly data.",
            )


@app.get("/forecast", response_model=ForecastResponse)
async def get_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    days: int = Query(..., ge=1, le=7),
):
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        # NOTE: `daily=time` is not a valid parameter value; the Open-Meteo daily
        # endpoint returns the `time` array automatically when `daily=` is set.
        url = (
            f"{OPEN_METEO_BASE_URL}/v1/forecast"
            f"?latitude={latitude}&longitude={longitude}"
            f"&daily=temperature_2m_max,wind_speed_10m_max"
            f"&forecast_days={days}&timezone=auto"
        )

        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Open-Meteo API error.")
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to Open-Meteo: {e}",
            )

    # Normalize the response
    try:
        daily_forecasts = []

        time_data = data["daily"]["time"]
        temp_data = data["daily"]["temperature_2m_max"]
        wind_data = data["daily"]["wind_speed_10m_max"]

        if len(time_data) < days:
            raise IndexError("API did not return enough days of data.")

        for i in range(days):
            daily_forecasts.append(
                DailyForecast(
                    time=time_data[i],
                    temperature_2m_max=temp_data[i],
                    wind_speed_10m_max=wind_data[i],
                )
            )

        return ForecastResponse(
            latitude=latitude,
            longitude=longitude,
            daily_forecasts=daily_forecasts,
            source="open-meteo",
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected structure in Open-Meteo response: Missing key {e}",
        )
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Open-Meteo did not provide enough daily data.",
        )
