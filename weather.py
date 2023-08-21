# OpenMeteo time format ISO8601: "YYYY-MM-DDTHH:MM" where T is the separator

# COMMANDS

# /today: Tells if you can laba today, returns time window to laba
# /now: Tells if you can laba now, returns best next time(?)

# Immediately return false if later than 2pm.

# TASK 1: Show weather stats in the next 5 hours
# 1. Get current time in ISO8601 format
# 2. Matching current time with hourly weather data (Times are in 24 hr format)
# 3. Round up time if it's already >= 30 minutes in the hour.
# 4. Return 5-hour forecast data

# TASK 2: Make sense of the 5-hour forecast data
# 1. Check for specific weather windows and precipitation probability (pp).
#       a. Sunny - 3 hour window (wmo 0)
#       b. Overcast - 5 hour window (wmo 3)
#       c. Partly cloudy - 4 hour window (wmo 2)
#       d. Mainly clear - 3 hour window (wmo 1)
# 2. If pp > 0.5, do not count that hr
# 3. If decision = true, return decision and time window
# 4. If decision = false, return decision and next time window (optional)

# TASK 3: For today command, find period of time where score < threshold
# 
# 

# TODO Find way to dynamically change Open Meteo API key with location of user

# OPTIONAL:
# - If decision is false in /now command, give next time window
# - Predict time needed to dry clothes
#
# /setlaundrydays: 
# TASK 1: Laundry day notifications 
# 1. Allow user to set 'laundry days'.
# 2. Notify user if it is a good idea to wash clothes that day.
#    Specifically, if there is a sunny 

import requests, json
from datetime import datetime
from config import OPEN_METEO_KEY
from WMO_CODES import WMO_CODES

LABA_THRESHOLD = 0.5 # 50% precipitation chance

def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)

def weather() -> dict:
    """
    OpenMeteo API Call to get 2 days worth of hourly weather data.

    Keys:
        'time',
        'weathercode',
        'temperature_2m',
        'precipitation_probability'
    """
    response = requests.get(OPEN_METEO_KEY)
    hourly_data = response.json()['hourly']

    return hourly_data

def get_now_forecast(hourly_data) -> dict:
    """
     Get weather data in the next 5 or 6 hrs (depending on minute). 
     Returns `forecast` dictionary.
    """

    forecast = dict()
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
    now_idx = hourly_data['time'].index(iso_now)

    # Index range to get 5 or 6-hour forecast.
    next_idx += now_idx

    # Populate forecast dictionary
    for (k, v) in hourly_data.items():
        # print(k, v)
        if k == 'time':
            forecast.update({'time': v[now_idx:next_idx]})
        elif k == 'temperature_2m':
            forecast.update({'temperature_2m': v[now_idx:next_idx]})
        elif k == 'precipitation_probability':
            forecast.update({'pp': v[now_idx:next_idx]})
        elif k == 'weathercode':
            forecast.update({'weathercode': v[now_idx:next_idx]})
    # jprint(forecast)
    return forecast

def log_forecast(forecast: dict) -> None:
    print('datetime\tw_code\tweather\ttemp\tpp')

    for i in range(len(forecast['time'])):
        hour = forecast['time'][i]
        pp = forecast['pp'][i]
        temp = forecast['temperature_2m'][i]
        w_code = forecast['weathercode'][i]
        weather = WMO_CODES[forecast['weathercode'][i]]

        print(f'{hour.split("T")}\t{w_code}\t{weather}\t{temp}\t{pp}')

def print_forecast(forecast: dict) -> None:
    print('Time\tweather\ttemp\tpp')

    for i in range(len(forecast['time'])):
        dt = forecast['time'][i]
        hr = dt[-5:]
        pp = forecast['pp'][i]
        temp = forecast['temperature_2m'][i]
        weather = WMO_CODES[forecast['weathercode'][i]]

        print(f'{hr}\t{weather}\t{temp}\t{pp}')

def process_now_forecast(forecast_dict):
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

    for wmo_code in forecast_dict['weathercode']:
        score += wmo_code
        if wmo_code > 4:
            decision = False
            break

    if score > 15: decision = False

    print(f'Score: {score}\t Decision: {decision}')

    return decision

def now():

    hourly_data = weather()
    
    now = datetime.now()

    if now.hour > 17 and now.hour < 6:
        return 'Laba tomorrow.'
    
    forecast = get_now_forecast(hourly_data)
    print_forecast(forecast)
    if process_now_forecast(forecast):
        return 'Yes, you can laba right now.'
    else:
        return 'No, you can\'t laba right now'