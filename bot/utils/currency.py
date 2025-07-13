import yfinance as yf

# Simple cache to avoid repeated API calls during one run
EXCHANGE_CACHE = {}

def get_usd_to_currency_rate(target_currency):
    target_currency = target_currency.upper()

    if target_currency == "USD":
        return 1.0  # no conversion needed

    if target_currency in EXCHANGE_CACHE:
        return EXCHANGE_CACHE[target_currency]

    ticker = f"{target_currency}USD=X"
    data = yf.Ticker(ticker)
    price = data.history(period="1d")["Close"]

    if price.empty:
        raise ValueError(f"Could not fetch rate for {target_currency}")

    rate = 1 / price[-1]  # since ticker is XXXUSD=X, we invert to get USD->XXX

    EXCHANGE_CACHE[target_currency] = rate
    return rate

def convert_price(usd_price, target_currency):
    try:
        rate = get_usd_to_currency_rate(target_currency)
        return round(usd_price * rate, 2), target_currency.upper()
    except Exception as e:
        # fallback if API fails
        print(f"[WARN] Currency conversion failed: {e}")
        return usd_price, "USD"
