
import requests
from datetime import datetime, timezone
import pandas as pd

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
    def get_order_book(market_id):
        """
        The order book shows all active bid orders for both yes and no sides of a binary market.
        don't forget about the reciprical nature of the contracts: yes bid at 20 is used for same order of no ask at 80 
        It returns yes bids and no bids only! 
        if you index by no or yes format is in [cents, contracts available]
        if you index by no_dollars or yes_dollars format is in [dollars, contracts available]
        """
        orderbook_url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{market_id}/orderbook"
        orderbook_response = requests.get(orderbook_url)
        orderbook_data = orderbook_response.json()
        return orderbook_data
    
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

        return df 
