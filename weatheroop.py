import requests, json
from datetime import datetime
from config import OPEN_METEO_KEY
from WMO_CODES import WMO_CODES

class Forecast:
    
    def __init__(self) -> None:
        self.forecast: dict = dict()
        self.now_forecast: dict = dict()

    def __str__(self) -> str:
        text: str = 'FORECAST\n'
        for i in range(len(self.forecast['time'])):
            time = self.forecast['time'][i]
            weather = WMO_CODES[self.forecast['weathercode'][i]]
            temp = self.forecast['temperature_2m'][i]
            pp = self.forecast['precipitation_probability'][i]

            text += f'{time.split("T")[1]:<7}{temp}{" C":<3} {pp}{"%":<3}{weather}\n'

        return text
        
    def display_forecast(self, forecast: dict) -> str:
        """
            General printer function for forecasts.
        """
        text: str = 'FORECAST\n'
        for i in range(len(forecast['time'])):
            time = self.forecast['time'][i]
            weather = WMO_CODES[self.forecast['weathercode'][i]]
            temp = self.forecast['temperature_2m'][i]
            pp = self.forecast['precipitation_probability'][i]

            text += f'{time.split("T")[1]}\t\t\t{temp} C\t\t\t{pp}%\t\t\t{weather}\n'

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
        response = requests.get(OPEN_METEO_KEY)
        hourly_data = response.json()['hourly']

        self.forecast = hourly_data

    def get_now_forecast(self) -> None:
        """
        Get weather data in the next 5 or 6 hrs (depending on minute). 

        Populates self.now_forecast dictionary.

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

        self.weather() # Get fresh weather data
        self.now_forecast = dict() # Reset self.now_forecast

        now = datetime.now()

        # Round up hour, if > 30 minutes.
        if now.minute > 30:
            next_idx = 6
            rounded_now = datetime(now.year, now.month, now.day, now.hour+1)
        else:
            next_idx = 5
            rounded_now = datetime(now.year, now.month, now.day, now.hour)

        # Convert datetime object to isoformat. Removing seconds.
        iso_now = rounded_now.isoformat()[:-3]

        # Find current time in hourly_data.
        now_idx = self.forecast['time'].index(iso_now)

        # Index range to get 5 or 6-hour forecast.
        next_idx += now_idx

        # Populate forecast dictionary
        for (k, v) in self.forecast.items():
            # print(k, v)
            if k == 'time':
                self.now_forecast.update({'time': v[now_idx:next_idx]})
            elif k == 'weathercode':
                self.now_forecast.update({'weathercode': v[now_idx:next_idx]})
            elif k == 'temperature_2m':
                self.now_forecast.update({'temperature_2m': v[now_idx:next_idx]})
            elif k == 'precipitation_probability':
                self.now_forecast.update({'precipitation_probability': v[now_idx:next_idx]})
 

    def process_forecast(self) -> bool:
        """
        TASK 2: Make sense of the 5-hour forecast data
        1. Check for specific weather windows and precipitation probability (pp).
            a. Sunny - 2 hour window (wmo 0)
            b. Overcast - 5 hour window (wmo 3)
            c. Partly cloudy - 4 hour window (wmo 2)
            d. Mainly clear - 3 hour window (wmo 1)
        2. If pp > 0.5, do not count that hr
        3. If decision = true, return decision and time window
        4. If decision = false, return decision and next time window (optional)
        """

        score = 0
        decision = True

        for wmo_code in self.now_forecast['weathercode']:
            score += wmo_code
            if wmo_code > 4:
                decision = False
                break

        if score > 15: decision = False

        print(f'Score: {score}\t Decision: {decision}')

        return decision
    
    def now(self) -> str:
        self.get_now_forecast()

        text: str = self.display_forecast(self.now_forecast) + '\n'
        now = datetime.now()

        if now.hour > 17 or now.hour < 6:
            if now.hour >= 0:
                text += f'It\'s {now.hour}:00 AM. Check again later.'
                return text
            else: 
                text += f'It\'s {now.hour}:00 PM. Laba tomorrow.'
                return text


        # print(self)

        if self.process_forecast():
            text += 'Yes, you can laba right now.'
            return text
        else:
            text += 'No, you can\'t laba right now'
            return text


    def today(self) -> None:
        pass

    