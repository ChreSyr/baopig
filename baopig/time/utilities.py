
import math


MILLISECONDS = .001
SECONDS = 1
MINUTES = 60
HOURS = 60 * MINUTES
DAYS = 24 * HOURS


def format_time(time, formatter=None):
    """
    Function who create a string from a time and a formatter
    The time value is considered as seconds

    It uses letters in formatter in order to create the appropriate string:
        - %D : days
        - %H : hours
        - %M : minutes
        - %S : seconds
        - %m : milliseconds

    Examples :

        format_time(time=600, formatter="%H hours and %M minutes") -> "10 hours and 0 minutes"

    """

    formatter_is_unset = formatter is None
    if formatter is None:
        formatter = "%D:%H:%M:%S:%m"

    require_days = formatter.count("%D")
    require_hours = formatter.count("%H")
    require_minutes = formatter.count("%M")
    require_seconds = formatter.count("%S")
    require_milliseconds = formatter.count("%m")

    # Days
    days = int(time // 86400)
    if require_days:
        formatter = formatter.replace("%D", "{:0>2}".format(days))
        time = time % 86400

    # Hours
    hours = int(time // 3600)
    if require_hours:
        formatter = formatter.replace("%H", "{:0>2}".format(hours))
        time = time % 3600

    # Minutes
    minutes = int(time // 60)
    if require_minutes:
        formatter = formatter.replace("%M", "{:0>2}".format(minutes))
        time = time % 60

    # Seconds
    if require_seconds:
        formatter = formatter.replace("%S", "{:0>2}".format(int(time)))
        time = time % 1

    # milliseconds
    if require_milliseconds:
        formatter = formatter.replace("%m", "{:0>3}".format(int(time * 1000)))

    if formatter_is_unset:
        while formatter.startswith("00:") and len(formatter) > 6:
            formatter = formatter[3:]

    return formatter


def present_time(time, max_unit=SECONDS, min_unit=MILLISECONDS):
    """
    Arrondi au superieur
    If min_unit is set, the time will be given in the unit
    If max_unit is set, the time will contain every unit from min_unit to max_unit
    max_unit cannot be lower than SECONDS
    """
    # Round the time
    # If time = 1.5 seconds and min_unit is SECONDS, then we round it to 2
    time = math.ceil(time / min_unit) * min_unit

    res = ""
    got_max_unit = False

    # Hours
    hours = int(time // HOURS)
    if min_unit >= HOURS:
        return res + str(hours)
    if hours or max_unit >= HOURS:
        got_max_unit = True
        res += str(hours) + ":"
        time = time % HOURS

    # Minutes
    minutes = int(time // MINUTES)
    if min_unit >= MINUTES:
        return res + ("{:0>2}".format(minutes) if got_max_unit else str(minutes))
    if got_max_unit:
        res += "{:0>2}:".format(minutes)
        if minutes:
            time = time % MINUTES
    elif minutes or max_unit >= MINUTES:
        got_max_unit = True
        res += str(minutes) + ":"
        time = time % MINUTES

    # Seconds
    seconds = int(time // SECONDS)
    if min_unit >= SECONDS:
        return res + ("{:0>2}".format(seconds) if got_max_unit else str(seconds))
    if got_max_unit:
        res += "{:0>2}:".format(seconds)
    else:  # If the time is .345, we want 0:345
        res += str(seconds) + ":"
    if seconds:
        time = time % SECONDS

    # milliseconds
    milliseconds = int(time // MILLISECONDS)
    assert min_unit >= MILLISECONDS, "Wrong min_unit value"
    return res + "{:0>3}".format(milliseconds)


# TESTS UNITAIRES
"""
time = 400 * 60 + .8
print("Time :", time)
print(format_time(time, "Days : %D"))
print(format_time(time, "Hours : %H"))
print(format_time(time, "Minutes : %M"))
print(format_time(time, "Seconds : %S"))
print(format_time(time, "Milliseconds : %m"))

print(format_time(time, "%D:%H:%M:%S:%m"))
print(format_time(time, "%H:%M:%S:%m"))
print(format_time(time, "%M:%S:%m"))
print(format_time(time))

print(present_time(time, min_unit=MINUTES))
"""