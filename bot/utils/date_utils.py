from datetime import datetime, timedelta

def get_today():
    return datetime.today().strftime("%Y-%m-%d")

def get_tomorrow():
    return (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

def get_next_saturday():
    today = datetime.today()
    days_until_sat = (5 - today.weekday()) % 7
    return (today + timedelta(days=days_until_sat)).strftime("%Y-%m-%d")

def get_next_week():
    return (datetime.today() + timedelta(days=7)).strftime("%Y-%m-%d")