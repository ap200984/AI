# Weather Proxy Service

This project provides a proxy service for fetching weather data.

## Technologies Used
- Python 3.12
- FastAPI
- httpx

## Installation and Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```
2. **Run the application:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## Endpoints

- `GET /` — confirms the service is running.
- `GET /health` — checks the operational status of the service.
- `GET /weather` — retrieves current weather data for given coordinates.
  - Query parameters: `latitude` (-90 to 90), `longitude` (-180 to 180).
  - Response: `latitude`, `longitude`, `temperature`, `wind_speed`, `source`.
- `GET /forecast` — retrieves weather forecast data for given coordinates.
  - Query parameters: `latitude` (-90 to 90), `longitude` (-180 to 180), `days` (1 to 7).
  - Response: `latitude`, `longitude`, `days`, `timezone`, `dates`, `temperature_celsius_max`, `temperature_celsius_min`, `wind_speed_kph_max`, `source`.

## Development
To run development tools (like Ruff):
