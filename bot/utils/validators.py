import re

def is_valid_airport_code(code: str):
    return re.fullmatch(r"[A-Z]{3}", code) is not None

def is_valid_date(date_str):
    from datetime import datetime
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except:
        return False