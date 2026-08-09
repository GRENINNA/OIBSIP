# Basic Weather App - Sample Output

The values below are illustrative because live weather changes continuously.
The file does not contain an API key.

## Example request

```text
Provider: WeatherAPI.com
Location query: New Delhi, India
Preferred units: Celsius
```

## Representative current conditions

```text
Resolved location: New Delhi, India
Temperature: 30.0 C / 86.0 F
Feels like: 33.0 C
Humidity: 60%
Condition: Partly cloudy
Wind: 3.5 m/s
```

## Representative hourly card

```text
Time: 02:00 PM
Temperature: 31 C
Condition: Partly cloudy
Rain probability: 20%
Wind: 3.8 m/s
```

## Representative daily card

```text
Date: Monday, 10 August
Maximum: 34 C
Minimum: 27 C
Condition: Patchy rain nearby
Rain probability: 65%
Average humidity: 72%
```

WeatherAPI.com's free plan may return three daily forecast cards. The app
automatically retries with the supported range if a five-day request is rejected
by the account plan.

## Expected error messages

```text
Enter a city name or postal code.
WeatherAPI.com rejected the API key.
No matching location was found. Check the city or postal code.
The WeatherAPI.com monthly request quota has been reached.
```

