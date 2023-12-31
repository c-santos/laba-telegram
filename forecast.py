from datetime import datetime as dt, timezone, timedelta
import requests

WMO_CODES = {
    0: "☼ Clear sky",
    1: "🌤 Mainly clear",
    2: "⛅ Partly cloudy",
    3: "☁ Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "☂ Light drizzle",
    53: "☔ Fair drizzle",
    55: "🌦 Dense drizzle",
    56: "Freezing drizzle: Light intensity",
    57: "Freezing drizzle: Dense intensity",
    61: "☔ Light rain",
    63: "🌧 Moderate rain",
    65: "🌧 Heavy rain",
    66: "Freezing rain: Light intensity",
    67: "Freezing rain: Heavy intensity",
    71: "Snow fall: Slight intensity",
    73: "Snow fall: Moderate intensity",
    75: "Snow fall: Heavy intensity",
    77: "Snow grains",
    80: "🌦 Light showers",
    81: "🌦 Moderate showers",
    82: "🌦 Violent showers",
    85: "Snow showers: Slight intensity",
    86: "Snow showers: Heavy intensity",
    95: "⛈ Thunderstorm",
    96: "⛈ Thunderstorm with hail",
    97: "⛈ Heavy thunderstorm",
    98: "⛈ Heavy thunderstorm with hail",
}


class Forecast:
    def __init__(self, lon: float, lat: float) -> None:
        self.forecast: dict = dict()  # 3-day forecast
        self.lon: float = lon
        self.lat: float = lat
        self.tz: timezone = timezone(timedelta(hours=8))

        self._OPEN_METEO_API = f"https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}&hourly=temperature_2m,precipitation_probability,weathercode&forecast_days=3"

    def __str__(self) -> str:
        text: str = "FORECAST\n"

        for i in range(len(self.forecast["time"])):
            time = self.forecast["time"][i]
            weather = WMO_CODES[self.forecast["weathercode"][i]]
            temp = self.forecast["temperature_2m"][i]
            pp = self.forecast["precipitation_probability"][i]

            text += f'{time.split("T")[1]:<7}{temp}{" C":<3} {pp}{"%":<3} {weather}\n'

        return text

    def display_forecast(self, forecast: dict) -> str:
        """
        General printer function for forecasts.
        """
        text: str = ""

        for i in range(len(forecast["time"])):
            time = forecast["time"][i]
            weather = WMO_CODES[forecast["weathercode"][i]]
            temp = forecast["temperature_2m"][i]
            pp = forecast["precipitation_probability"][i]

            text += f'{time.split("T")[1]:<7}{temp}{" C":<3} {pp}{"%":<3} {weather}\n'

        return text

    def get_weather(self) -> None:
        """
        OpenMeteo API Call to get 2 days worth of hourly weather data.

        Keys:
            'time',
            'weathercode',
            'temperature_2m',
            'precipitation_probability'

        Dictionary structure:
        {
            'time': [00:00,01:00,02:00,...],
            'weathercode': [0,1,0,...],
            'temperature_2m': [32,31,35,...],
            'precipitation_probability': [0,23,40,..]
        }
        """
        response: requests.Response = requests.get(self._OPEN_METEO_API)
        weather_data: dict = response.json()["hourly"]
        # weather_data: dict = response.json()
        # print(weather_data)

        self.forecast = weather_data

    def extract_forecast(self, source: dict, start_idx: int, end_idx: int) -> dict:
        """
        Extracts a new dictionary from source dictionary based on the start and end indices.
        """
        extracted_forecast: dict = dict()

        for k, v in source.items():
            if k == "time":
                extracted_forecast.update({"time": v[start_idx:end_idx]})
            elif k == "weathercode":
                extracted_forecast.update({"weathercode": v[start_idx:end_idx]})
            elif k == "temperature_2m":
                extracted_forecast.update({"temperature_2m": v[start_idx:end_idx]})
            elif k == "precipitation_probability":
                extracted_forecast.update(
                    {"precipitation_probability": v[start_idx:end_idx]}
                )

        return extracted_forecast

    def can_laba(self, forecast: dict) -> bool:
        """
        Make sense of the 5-hour forecast data
        1. Check for specific weather windows and precipitation probability (pp).
            Sunny - 2 hour window (wmo 0)
            Mainly clear - 3 hour window (wmo 1)
            Partly cloudy - 4 hour window (wmo 2)
            Overcast - 5 hour window (wmo 3)
        2. If pp > 0.5, do not count that hr
        3. If decision = true, return decision and time window
        4. If decision = false, return decision and next time window (optional)
        """

        score: int = 0
        decision: bool = True

        for wmo_code in forecast["weathercode"]:
            score += wmo_code

            if wmo_code > 4:
                decision = False
                break

        if score > 15:
            decision = False

        # print(f"Score: {score}\tDecision: {decision}")

        return decision

    def now(self) -> str:
        text: str = "CURRENT FORECAST\n"

        self.get_weather()  # Get fresh weather data

        now: dt = dt.now(tz=self.tz)  # Get current datetime

        # Get forecast of next 6 hours if minute > 30 minutes. Else, 5 hours
        if now.minute > 30:
            next_idx: int = 6
            now: dt = dt(now.year, now.month, now.day, now.hour + 1)
        else:
            next_idx: int = 5
            now: dt = dt(now.year, now.month, now.day, now.hour)

        # Convert datetime object to isoformat. Removing seconds.
        iso_now: dt = now.isoformat()[:-3]

        # Get index of current time in forecast.
        now_idx: int = self.forecast["time"].index(iso_now)

        next_idx += now_idx  # Index range to extract 5 or 6-hour forecast.

        now_forecast = self.extract_forecast(
            self.forecast, now_idx, next_idx
        )  # Get forecast data starting from now_idx to next_idx

        # Display forecast
        text += self.display_forecast(now_forecast) + "\n"

        # Automatically return false if earlier than 06:00 or later than 15:00
        if now.hour == 0:
            text += f"It's 12 AM. Check again later."
            return text
        elif 0 < now.hour < 6:
            text += f"It's {now.hour} AM. Check again later."
            return text
        elif 15 <= now.hour <= 23:
            text += f"It's {now.hour-12} PM. Laba tomorrow."
            return text
        else:
            # Can I laba now?
            if self.can_laba(now_forecast):
                text += "Yes, you can laba right now."
                return text
            else:
                text += "No, you can't laba right now"
                return text

    def today(self) -> str:
        today = dt.now(tz=self.tz)
        text: str = f"TODAY'S FORECAST ({today.date()})\n"
        self.get_weather()

        morning_forecast: dict = self.extract_forecast(self.forecast, 6, 11)
        noon_forecast: dict = self.extract_forecast(self.forecast, 11, 15)

        text += self.display_forecast(morning_forecast)
        text += self.display_forecast(noon_forecast)

        # Can I laba today?
        if self.can_laba(morning_forecast) or self.can_laba(noon_forecast):
            text += "\nYou can laba today!"
            return text
        else:
            text += (
                "\nYou cannot laba today. The clothes will not dry. Try again tomorrow."
            )
            return text


if __name__ == "__main__":
    lon = 121.1222
    lat = 14.5786
    f = Forecast(lon, lat)
    print(f.now())
    print(f.today())
