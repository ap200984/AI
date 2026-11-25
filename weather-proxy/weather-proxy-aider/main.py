import asyncio

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="Weather Proxy Service")

# Base URL for the external weather API
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

# Fields requested for the current weather
CURRENT_FIELDS = "temperature_2m,wind_speed_10m"

# Fields requested for the forecast
FORECAST_FIELDS = "temperature_2m_max,temperature_2m_min,wind_speed_10m_max"


class WeatherRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class ForecastRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    days: int = Field(..., ge=1, le=7)


@app.get("/")
def read_root():
    """
    A minimal endpoint to confirm the service is running.
    """
    return {"message": "Weather Proxy Service is initialized."}


@app.get("/health")
def health_check():
    """
    Checks the operational status of the service.
    """
    return {"status": "ok"}


@app.get("/weather")
async def get_weather(
    latitude: float = Query(..., ge=-90, le=90), longitude: float = Query(..., ge=-180, le=180)
):
    """
    Retrieves current weather data from Open-Meteo based on coordinates.
    """
    request = WeatherRequest(latitude=latitude, longitude=longitude)

    params = {
        "latitude": request.latitude,
        "longitude": request.longitude,
        "current": CURRENT_FIELDS,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(WEATHER_API_URL, params=params)
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
            data = response.json()

            if "current" not in data:
                raise ValueError("External API response structure is missing 'current' data.")

            current_weather = data["current"]

            # Extract required fields
            temperature = current_weather.get("temperature_2m")
            wind_speed = current_weather.get("wind_speed_10m")

            if temperature is None or wind_speed is None:
                raise ValueError(
                    "External API response is missing required weather metrics "
                    "(temperature or wind speed)."
                )

            return {
                "latitude": request.latitude,
                "longitude": request.longitude,
                "temperature": temperature,
                "wind_speed": wind_speed,
                "source": "open-meteo",
            }

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"External API error: {e.response.status_code}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=f"Could not connect to external weather service: {e}"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=500, detail=f"Error processing external API response: {e}"
            )


@app.get("/forecast")
async def get_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    days: int = Query(..., ge=1, le=7),
):
    """
    Retrieves weather forecast data from Open-Meteo based on coordinates.
    """
    request = ForecastRequest(latitude=latitude, longitude=longitude, days=days)

    params = {
        "latitude": request.latitude,
        "longitude": request.longitude,
        "forecast_days": request.days,
        "daily": FORECAST_FIELDS,
        "timezone": "auto",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(WEATHER_API_URL, params=params)
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
            data = response.json()

            if "daily" not in data:
                raise ValueError("External API response structure is missing 'daily' data.")

            daily = data["daily"]

            # Extract required fields
            temperature_max = daily.get("temperature_2m_max")
            temperature_min = daily.get("temperature_2m_min")
            wind_speed_max = daily.get("wind_speed_10m_max")

            if temperature_max is None or temperature_min is None or wind_speed_max is None:
                raise ValueError("External API response is missing required forecast metrics.")

            dates = [daily["time"][i] for i in range(request.days)]

            return {
                "latitude": request.latitude,
                "longitude": request.longitude,
                "days": request.days,
                "timezone": "auto",
                "dates": dates,
                "temperature_celsius_max": temperature_max,
                "temperature_celsius_min": temperature_min,
                "wind_speed_kph_max": wind_speed_max,
                "source": "open-meteo",
            }

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"External API error: {e.response.status_code}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=f"Could not connect to external weather service: {e}"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=500, detail=f"Error processing external API response: {e}"
            )


if __name__ == "__main__":
    # This block is typically used for local testing,
    # but the service is meant to be run via uvicorn.
    asyncio.run(app)
