# Weather Proxy

This project is a FastAPI proxy service that fetches weather data from Open-Meteo and returns a normalized, standardized JSON structure.

## 🛠️ Technology Stack
*   **Language:** Python 3.12
*   **Framework:** FastAPI
*   **Dependencies:** `fastapi`, `uvicorn`, `httpx`, `pydantic`

## 🚀 How to Run

1.  **Install Dependencies:**
    ```bash
    uv sync
    ```
2.  **Run the Application:**
    The application is designed to be run using the following command (assuming the virtual environment is active):
    ```bash
    uv run uvicorn main:app --reload
    ```
    The service will start on `http://127.0.0.1:8000`.

## 🗺️ API Endpoints

### 1. Health Check
*   **GET `/health`**
    *   **Description:** Checks if the service is running and available.
    *   **Response:**
        ```json
        {
            "status": "ok"
        }
        ```

### 2. Current Weather
*   **GET `/weather?latitude={latitude}&longitude={longitude}`**
    *   **Parameters:**
        *   `latitude` (float): The latitude of the location (must be between -90 and 90).
        *   `longitude` (float): The longitude of the location (must be between -180 and 180).
    *   **Response (200 OK):**
        ```json
        {
            "latitude": 41.7151,
            "longitude": 44.8271,
            "temperature": 28.4,
            "wind_speed": 12.1,
            "source": "open-meteo"
        }
        ```

### 3. Forecast
*   **GET `/forecast?latitude={latitude}&longitude={longitude}&days={days}`**
    *   **Parameters:**
        *   `latitude` (float): The latitude of the location (must be between -90 and 90).
        *   `longitude` (float): The longitude of the location (must be between -180 and 180).
        *   `days` (int): The number of forecast days (must be between 1 and 7).
    *   **Response (200 OK):**
        ```json
        {
            "latitude": 41.7151,
            "longitude": 44.8271,
            "daily_forecasts": [
                {
                    "time": "2026-11-18T00:00:00+04:00",
                    "temperature_2m_max": 13.8,
                    "wind_speed_10m_max": 18.1
                },
                // ... up to 'days' entries
            ],
            "source": "open-meteo"
        }
        ```

## ⚠️ Error Handling
The service implements robust error handling for external API failures, returning appropriate HTTP 5xx status codes when Open-Meteo is unavailable or returns an unexpected format. Input validation (latitude, longitude, days) is handled by Pydantic and returns HTTP 422/400 codes where applicable.

**Note:** All project constraints (Python 3.12, UV dependency management, Ruff linting) are adhered to.
