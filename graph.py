import requests
from datetime import datetime, timezone
import matplotlib.pyplot as plt

def main() -> None:
    series_id = 'KXCBDECISIONCANADA'
    market_id = 'KXCBDECISIONCANADA-25OCT-C25'
    data: list = get_candle_sticks(series_id, market_id, 60)

    print(type(data))

    dates = []
    prices = []

    for i in data:
        date = datetime.fromtimestamp(i['end_period_ts'])
        price = i.get('price', {}).get('close_dollars')

        print(f'{date=} {i=}')

        if date and price:
            dates.append(date)
            prices.append(price)

    plt.plot(dates, prices)
    plt.show()

def get_candle_sticks(series_id, market_id, interval):  # will make an integration for custom start/end later
    url = f"https://api.elections.kalshi.com/trade-api/v2/series/{series_id}/markets/{market_id}/candlesticks"

    market_info = get_market_info(market_id)
    open_time_iso = market_info['market']['open_time']  # gets time in iso
    dt = datetime.fromisoformat(open_time_iso.replace('Z', '+00:00'))  # parse UTC
    open_time = str(int(dt.timestamp()))  # convert to unix

    params = {
        "period_interval": interval,
        "start_ts": open_time,
        "end_ts": str(int(datetime.now(timezone.utc).timestamp()))
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data['candlesticks']

def get_market_info(market_id):  # market is a specific event that trades on a binary outcome
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{market_id}"
    response = requests.get(url)
    market_data = response.json()
    return market_data

if __name__ == '__main__':
    main()
