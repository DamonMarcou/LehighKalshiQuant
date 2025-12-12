import numpy as np
import pandas as pd
import requests
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import no_authentication_endpoints as nae

def main() -> None:
    #series_id = 'KXCBDECISIONCANADA'
    #market_id = 'KXCBDECISIONCANADA-25OCT-C25'

    series_id: str = 'KXBTCMAXY'
    market_id: str = 'KXBTCMAXY-25'

    o = nae.no_authentication_endpoints()

    market = o.get_market_info(market_id)

    print(f'{market=}')

    print(f'{candle_sticks=}')

    dates = []
    prices = []

    for i in candle_sticks:
        date = datetime.fromtimestamp(i['end_period_ts'])
        price: str = i['price']['close_dollars']

        if date and price:
            dates.append(date)
            prices.append(float(price))

    plt.plot(dates, prices)
    plt.show()

    candle_sticks = pd.DataFrame()
    candle_sticks['Close'] = prices

    buy_threshold = 0.15

    differences = difference_in_moving_averages(prices, 5, 23)

    # Add the differences as a column in the original candle_sticks frame
    candle_sticks['differences'] = differences

    # This column represents the signal
    candle_sticks['Signal'] = 0

    # Set a buy signal(1) when difference is above the threshold
    candle_sticks.loc[candle_sticks['differences'] > buy_threshold, 'Signal'] = 1

    # The position is decided by difference in the signal
    candle_sticks['Position'] = candle_sticks['Signal'].diff()

    # Add daily returns to the dataframe
    candle_sticks['Returns'] = candle_sticks['Close'].pct_change()

    # Add the daily returns of our strategy, we shift by one to make sure we aren't using information we don't have
    candle_sticks['Strategy_Returns'] = candle_sticks['Returns'] * candle_sticks['Signal'].shift(1)

    # Handle NaNs
    candle_sticks.dropna(inplace=True)

    # Calculate cumulative returns
    candle_sticks['Cumulative_Returns'] = (1 + candle_sticks['Returns']).cumprod()

    # Calculate cumulative Strategy Returns
    candle_sticks['Cumulative_Strategy'] = (1 + candle_sticks['Strategy_Returns']).cumprod()

    # The original dataframe with more information about signals and positions
    print(candle_sticks)

    # Print the performance candle_sticks
    plt.plot(candle_sticks['Cumulative_Returns'], label='Buy & Hold', color='blue')
    plt.plot(candle_sticks['Cumulative_Strategy'], label='Strategy', color='green')
    plt.title('Portfolio Simulation: MA Crossover vs. Buy & Hold')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Return')
    plt.legend()
    plt.show()

def moving_average(data, n):
    return [np.mean(data[i - n:i]) for i in range(n, len(data) + 1)]

def difference_in_moving_averages(prices, n1, n2):
    a1 = moving_average(prices, n1)
    a2 = moving_average(prices, n2)
    offset = max(n1, n2)
    dp = len(prices) - offset
    return offset*[np.nan]+list(np.subtract(a2[:dp], a1[:dp]))


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
