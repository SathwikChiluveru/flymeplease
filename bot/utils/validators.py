import re

def is_valid_airport_code(code: str):
    return re.fullmatch(r"[A-Z]{3}", code) is not None