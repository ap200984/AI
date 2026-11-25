"""Weather Proxy Service.

Async proxy to the Open-Meteo weather API.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict

app = FastAPI(
    title="Weather Proxy Service",
    version="0.1.0",
    description="Async proxy to the Open-Meteo weather API.",
)

DEFAULT_UPSTREAM_URL = "https://api.open-meteo.com/v1/forecast"
UPSTREAM_URL_ENV_VAR = "WEATHER_PROXY_UPSTREAM_URL"
TIMEOUT_SECONDS = 10.0


class Settings(BaseModel):
    """External API endpoint and request timeout configuration."""

    model_config = SettingsConfigDict(env_prefix="WEATHER_PROXY_", env_file=".env")

    upstream_url: str = Field(default=DEFAULT_UPSTREAM_URL)
    timeout_seconds: float = Field(default=TIMEOUT_SECONDS, ge=1.0, le=60.0)


settings = Settings()


class LatitudeLongitude(BaseModel):
    """Shared coordinates used by all endpoints."""

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


async def _call_upstream(url: str, params: dict[str, Any], timeout: float) -> dict[str, Any]:
    """GET the Open-Meteo forecast endpoint and return its parsed payload."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url=url, params=params)
    except httpx.TransportError as exc:
        raise HTTPException(status_code=502, detail=f"Unable to reach upstream API: {exc}") from exc

    if response.status_code != 200:
        detail = response.text.strip() or f"HTTP {response.status_code}"
        raise HTTPException(
            status_code=502, detail=f"Upstream API error {response.status_code}: {detail[:500]}"
        )

    try:
        return response.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Upstream API returned an invalid JSON payload")


@app.get("/health")
def health() -> dict[str, str]:
    """Readiness probe."""
    return {"status": "ok"}


@app.get("/weather")
async def get_current_weather(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
) -> dict[str, Any]:
    """Current temperature and wind speed for a location."""
    payload = await _call_upstream(
        url=settings.upstream_url,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m",
        },
        timeout=settings.timeout_seconds,
    )

    try:
        temperature = float(payload["current"]["temperature_2m"])
        wind_speed = float(payload["current"]["wind_speed_10m"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=502, detail=f"Invalid current weather payload: {exc}"
        ) from exc

    return {
        "latitude": latitude,
        "longitude": longitude,
        "temperature": temperature,
        "wind_speed": wind_speed,
        "source": "open-meteo",
    }


@app.get("/forecast")
async def get_forecast(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    days: int = Query(..., ge=1, le=7),
) -> dict[str, Any]:
    """7-day maximum temperature and wind speed forecast for a location."""
    payload = await _call_upstream(
        url=settings.upstream_url,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "forecast_days": days,
            "daily": "temperature_2m_max,wind_speed_10m_max",
            "timezone": "auto",
        },
        timeout=settings.timeout_seconds,
    )

    daily: dict[str, list[Any]] = payload.get("daily") or {}
    try:
        daily_forecasts = [
            {
                "time": daily["time"][i],
                "temperature_2m_max": daily["temperature_2m_max"][i],
                "wind_speed_10m_max": daily["wind_speed_10m_max"][i],
            }
            for i in range(len(daily["time"]))
        ]
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Invalid daily payload: {exc}") from exc

    return {
        "latitude": latitude,
        "longitude": longitude,
        "daily_forecasts": daily_forecasts,
        "source": "open-meteo",
    }
