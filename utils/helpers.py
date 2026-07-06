import math
import random
import string
from datetime import date


def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))


def calculate_age(birth_date: date) -> int:
    today = date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    """Returns distance in km between two coordinates."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def birth_date_from_age(age: int):
    """Return approximate birth date from age."""
    today = date.today()
    return today.replace(year=today.year - age)
