int_to_day = {
    0: 'MONDAY',
    1: 'TUESDAY',
    2: 'WEDNESDAY',
    3: 'THURSDAY',
    4: 'FRIDAY',
    5: 'SATURDAY',
    6: 'SUNDAY'
}

day_to_int = {
    'm': 0,
    't': 1,
    'w': 2,
    'th': 3,
    'f': 4,
    'sa': 5,
    'su': 6
}


def convert_to_int(days: list[str]) -> list[int]:
    return [day_to_int[d] for d in days]


def convert_to_day(days: list[int]) -> list[str]:
    return [int_to_day[d] for d in days]
