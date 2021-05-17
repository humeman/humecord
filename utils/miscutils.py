import math
import time
import datetime

def get_duration(seconds):
    seconds = math.trunc(seconds)

    if seconds < 60:
        return time.strftime("%Ss", time.gmtime(seconds))

    elif seconds < 3600: # 1 hour
        if seconds % 60 > 0:
            return time.strftime("%Mm, %Ss", time.gmtime(seconds))

        return time.strftime("%Mm", time.gmtime(seconds))
    
    else:
        return time.strftime("%Hh, %Mm, %Ss", time.gmtime(seconds))

def get_datetime(seconds):
    return f"{datetime.datetime.fromtimestamp(seconds).strftime('%b %d, %Y at %H:%M %Z')}"