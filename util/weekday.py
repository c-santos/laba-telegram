from datetime import datetime as dt

WEEKDAYS = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}


def is_equal(laundrydays: str) -> bool:
    # Convert laundry days string into a list
    laundrydays_list = laundrydays.split()

    # Convert weekdays from string to int
    for i, day in enumerate(laundrydays_list):
        laundrydays_list[i] = WEEKDAYS[day]

    # Get current weekday
    curr_weekday = dt.weekday(dt.now())

    if curr_weekday in laundrydays_list:
        return True

    return False
