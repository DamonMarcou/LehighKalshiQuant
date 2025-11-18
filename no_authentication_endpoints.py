
import requests
from datetime import datetime, timezone
import pandas as pd
from useful_tools import useful_tools
import numpy as np

class no_authentication_endpoints:
    
    def __init__(self):
        pass
    def get_series_info(self,series_id)->dict:#a series is a collection of related events
        url = f"https://api.elections.kalshi.com/trade-api/v2/series/{series_id}"
        response = requests.get(url)
        series_data = response.json()
        return series_data

    def all_markets_in_series(self,series_id)->dict:
        markets_url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series_id}&status=open"
        markets_response = requests.get(markets_url)
        markets_data = markets_response.json()
        return markets_data

    def get_all_markets(self, series_ticker):
        """Fetch all markets for a series, handling pagination"""
        all_markets = []
        cursor = None
        base_url = "https://api.elections.kalshi.com/trade-api/v2/markets"

        while True:
            # Build URL with cursor if we have one
            url = f"{base_url}?series_ticker={series_ticker}&limit=100"
            if cursor:
                url += f"&cursor={cursor}"

            response = requests.get(url)
            data = response.json()

            # Add markets from this page
            all_markets.extend(data['markets'])

            # Check if there are more pages
            cursor = data.get('cursor')
            if not cursor:
                break

            print(f"Fetched {len(data['markets'])} markets, total: {len(all_markets)}")

        return all_markets

    def list_of_all_historical_markets_in_a_series(self,series_ticker):
        markets = self.get_all_markets(series_ticker)
        market_list = []
        for market_dict in markets:
            m = market_dict['ticker']
            market_list.append(m)
        return market_list
   




    def get_event_info(self,event_id)-> dict:#an event is a collection of markets
        event_url = f"https://api.elections.kalshi.com/trade-api/v2/events/{event_id}"
        event_response = requests.get(event_url)
        event_data = event_response.json()
        return event_data

    def get_market_info(self,market_id)-> dict:#market is a specific event that trades on a binary outcome
        url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{market_id}"
        response = requests.get(url)
        market_data = response.json()
        return market_data
    
    
    def get_candle_sticks(self, series_id, market_id, period_interval:int, start=None, end=None):#will make an integration for custom start/end later
        '''
        for the period interval you can either choose 1 (1 min), 60 (1 hour), or 1440 (1 day)-must be an int
        start/end must be in unix time(might make it so you can just enter an array)
        '''
        url = f"https://api.elections.kalshi.com/trade-api/v2/series/{series_id}/markets/{market_id}/candlesticks"
        
        open_time_iso = self.get_market_info(market_id)['market']['open_time'] #gets time in iso
        dt = datetime.fromisoformat(open_time_iso.replace('Z', '+00:00'))  # parse UTC
        open_time = str(int(dt.timestamp()))#convert to unix
        
        params = {
            "period_interval": period_interval,  
            "start_ts": open_time,
            "end_ts": str(int(datetime.now(timezone.utc).timestamp()))
        }

        response = requests.get(url, params=params).json()
        return response

    import pandas as pd

    def candle_sticks_in_pandas(self,series_id, market_id, period_interval:int, start=None, end=None):
        data = self.get_candle_sticks(series_id, market_id, period_interval, start, end)

        # Flatten the nested dictionary for each candlestick
        flattened_data = []
        for candle in data['candlesticks']:
            flat_candle = {
                'end_period_ts': candle['end_period_ts'],
                'open_interest': candle['open_interest'],
                'volume': candle['volume'],
            }
            # Flatten price
            for key, value in candle['price'].items():
                flat_candle[f'price_{key}'] = value
            # Flatten yes_ask
            for key, value in candle['yes_ask'].items():
                flat_candle[f'yes_ask_{key}'] = value
            # Flatten yes_bid
            for key, value in candle['yes_bid'].items():
                flat_candle[f'yes_bid_{key}'] = value

            flattened_data.append(flat_candle)

        df = pd.DataFrame(flattened_data)
        #make conversion to date time format so its more readable
        df['end_period_dt'] = pd.to_datetime(df['end_period_ts'], unit='s')
        
        cols = list(df.columns)#switch unix timestamp and datetime columns
        i, j = cols.index('end_period_ts'), cols.index('end_period_dt')
        cols[i], cols[j] = cols[j], cols[i]
        df = df[cols]

        return df 
    def pairplot_and_heatmap_given_2_markets(self,series1, market1, series2, market2, period_interval):
        
        df = self.candle_sticks_in_pandas(series1, market1, period_interval)
        df2 = self.candle_sticks_in_pandas(series2, market2, period_interval)
        returns = np.log(df['yes_bid_close']/ df['yes_bid_close'].shift(1)).dropna()
        returns2 = np.log(df2['yes_bid_close']/ df2['yes_bid_close'].shift(1)).dropna()
        ut  = useful_tools()
        ut.covariance_matrix(returns, returns2,True)
