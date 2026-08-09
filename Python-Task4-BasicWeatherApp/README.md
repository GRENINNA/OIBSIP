# Task 4 - Basic Weather App

A modular Tkinter weather application that retrieves live current conditions,
hourly data, and daily forecasts from WeatherAPI.com. It supports city and
postal-code searches, provider icons, unit switching, and approximate IP-based
location detection.

## Features

- City, postal code, coordinates, and location-name search
- Current temperature, feels-like temperature, humidity, condition, and wind
- Celsius and Fahrenheit unit toggle
- WeatherAPI.com condition icons
- The next six one-hour forecast entries
- Up to five daily forecast cards, depending on the account plan
- Automatic fallback to three forecast days for free accounts
- Optional approximate location lookup using IPinfo
- Helpful in-app messages for invalid keys, missing locations, quotas, plan
  restrictions, timeouts, and network failures
- API keys and weather responses remain in memory and are not saved

## Requirements

- Python 3.10 or newer
- Tkinter, normally included with the Windows Python installer
- Requests
- Pillow, which supplies the `PIL` package used for weather icons
- A WeatherAPI.com API key

## Installation

Open PowerShell in this task folder and install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

## WeatherAPI.com key

1. Create or sign in to an account at [WeatherAPI.com](https://www.weatherapi.com/my/).
2. Copy the API key displayed on the account page.
3. Paste only that key into the masked field in the application.

The key can instead be supplied for the current PowerShell session:

```powershell
$env:WEATHERAPI_KEY = "your_key_here"
python main.py
```

Do not commit a real API key to GitHub or place it directly in a Python file.

## Forecast-plan limitation

The application requests five forecast days. WeatherAPI.com's free plan
currently provides three forecast days. If the five-day request is rejected
with plan error `2009`, the application automatically retries with three days
and displays a notice in its status bar. Five or more forecast days require a
WeatherAPI.com plan that includes extended forecast access.

## Run the application

Execute only the task's `main.py` file:

```powershell
python main.py
```

Do not run files inside `weather_app` directly; they are imported by `main.py`.

## Location examples

| Location type | Example |
| --- | --- |
| City | `Delhi` |
| City and country | `London,UK` |
| Postal code | `602024` |
| Coordinates | `28.61,77.21` |

**Use My Location** asks IPinfo for an approximate city based on the public IP
address. It is not GPS and may return a nearby city. An `IPINFO_TOKEN`
environment variable can optionally be supplied if anonymous lookup is limited.

## Project files

| File | Purpose |
| --- | --- |
| `main.py` | Creates the Tkinter window and starts the application |
| `weather_app/ui.py` | Builds the GUI and coordinates searches, units, and display panels |
| `weather_app/api.py` | Calls WeatherAPI.com and translates provider error codes |
| `weather_app/forecast.py` | Parses current, hourly, and daily WeatherAPI.com data |
| `weather_app/icons.py` | Downloads and prepares WeatherAPI.com icons with Pillow |
| `weather_app/location.py` | Performs optional IPinfo location detection |
| `weather_app/models.py` | Defines the application's structured weather data |
| `weather_app/errors.py` | Defines user-friendly application error types |
| `weather_app/__init__.py` | Marks `weather_app` as a Python package |
| `requirements.txt` | Lists Requests and Pillow dependencies |

## Troubleshooting

### `ModuleNotFoundError: No module named 'PIL'`

Install Pillow using the same Python executable that runs the application:

```powershell
python -m pip install -r requirements.txt
python main.py
```

### Invalid API key (`2006`)

Copy only the key from the WeatherAPI.com account page. Do not paste an
OpenWeather key because provider keys are not interchangeable.

### No matching location (`1006`)

Try a city name or coordinates. For example, use `Chennai` or `13.08,80.27`.

### Forecast-plan error (`2009`)

The app normally handles this automatically by retrying with the free plan's
three-day range. If the retry is also rejected, review the subscription status
on the WeatherAPI.com account page.

## Official references

- [WeatherAPI.com documentation](https://www.weatherapi.com/docs/)
- [WeatherAPI.com pricing and forecast limits](https://www.weatherapi.com/pricing.aspx)
- [Requests documentation](https://requests.readthedocs.io/)
- [Pillow documentation](https://pillow.readthedocs.io/)

