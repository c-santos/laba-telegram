import json
from datetime import datetime as dt

import requests

from config import OPEN_METEO_KEY
from WMO_CODES import WMO_CODES

# TODO Find better logic to determine if you can laba : can_laba()
# TODO Let user choose location, right now it's hardcoded


class Forecast:
    def __init__(self) -> None:
        self.forecast: dict = dict()  # 2-day forecast
        self.now_forecast: dict = dict()  # forecast when now() is called

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
        text: str = ''

        for i in range(len(forecast["time"])):
            time = forecast["time"][i]
            weather = WMO_CODES[forecast["weathercode"][i]]
            temp = forecast["temperature_2m"][i]
            pp = forecast["precipitation_probability"][i]

            text += f'{time.split("T")[1]:<7}{temp}{" C":<3} {pp}{"%":<3} {weather}\n'

        return text

    def weather(self) -> None:
        """
        OpenMeteo API Call to get 2 days worth of hourly weather data.

        Keys:
            'time',
            'weathercode',
            'temperature_2m',
            'precipitation_probability'

        Dictionary structure:
        {
            'time': [1,2,3,...],
            'weathercode': [0,1,2,...],
            'temperature_2m': [0,1,2,...],
            'precipitation_probability': [0,1,2,..]
        }
        """
        response: requests.Response = requests.get(OPEN_METEO_KEY)
        weather_data: dict = response.json()["hourly"]

        self.forecast = weather_data

    def extract_forecast(self, source: dict, start_idx: int, end_idx: int) -> dict:
        '''
        Extracts a new dictionary from source dictionary based on the start and end indices.
        '''
        extracted_forecast: dict = dict()

        for k, v in source.items():
            if k == 'time':
                extracted_forecast.update({'time': v[start_idx:end_idx]})
            elif k == 'weathercode':
                extracted_forecast.update(
                    {'weathercode': v[start_idx:end_idx]})
            elif k == 'temperature_2m':
                extracted_forecast.update(
                    {'temperature_2m': v[start_idx:end_idx]})
            elif k == 'precipitation_probability':
                extracted_forecast.update(
                    {'precipitation_probability': v[start_idx:end_idx]})

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

        print(f"Score: {score}\tDecision: {decision}")

        return decision

    def now(self) -> str:
        text: str = 'FORECAST\n'

        self.weather()  # Get fresh weather data
        self.now_forecast.clear()  # Reset self.now_forecast dictionary

        now: dt = dt.now()  # Get current datetime

        # Round up hour, if > 30 minutes.
        if now.minute > 30:
            next_idx: int = 6
            rounded_now: dt = dt(now.year, now.month, now.day, now.hour + 1)
        else:
            next_idx: int = 5
            rounded_now: dt = dt(now.year, now.month, now.day, now.hour)

        # Convert datetime object to isoformat. Removing seconds.
        iso_now: dt = rounded_now.isoformat()[:-3]

        # Find current time in forecast.
        now_idx: int = self.forecast["time"].index(iso_now)

        next_idx += now_idx  # Index range to extract 5 or 6-hour forecast.

        self.now_forecast = self.extract_forecast(
            self.forecast, now_idx, next_idx)

        # Display forecast
        text += self.display_forecast(self.now_forecast) + "\n"

        # Automatically return false if earlier than 06:00 or later than 15:00
        if 0 <= now.hour < 6:
            text += f"It's {now.hour}:{now.minute} AM. Check again later."
            return text
        elif 15 <= now.hour <= 23:
            text += f"It's {now.hour-12}{{now.minute}}:00 PM. Laba tomorrow."
            return text

        # Can I laba now?
        if self.can_laba(self.now_forecast):
            text += "Yes, you can laba right now."
            return text
        else:
            text += "No, you can't laba right now"
            return text

    def today(self) -> None:
        text: str = 'TODAY\'S FORECAST\n'
        self.weather()

        morning_forecast: dict = self.extract_forecast(self.forecast, 6, 11)
        noon_forecast: dict = self.extract_forecast(self.forecast, 11, 15)

        text += self.display_forecast(morning_forecast)
        text += self.display_forecast(noon_forecast)

        # Can I laba today?
        if self.can_laba(morning_forecast) or self.can_laba(noon_forecast):
            text += '\nYou can laba today!'
            return text
        else:
            text += '\nYou cannot laba today. The clothes will not dry. Try again tomorrow.'
            return text
