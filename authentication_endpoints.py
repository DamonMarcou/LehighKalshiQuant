import requests
import datetime
import base64
import uuid
from no_authentication_endpoints import no_authentication_endpoints
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding

class authentication_endpoints(no_authentication_endpoints):
    def __init__(self,api_key, file_path_to_private_key):
        super().__init__()
        self.API_KEY_ID = api_key
        self.PRIVATE_KEY_PATH = file_path_to_private_key  # Using raw string for Windows path
        self.BASE_URL = 'https://demo-api.kalshi.co'  # or 'https://api.kalshi.com' for production
        self.private_key = self.load_private_key(self.PRIVATE_KEY_PATH)

    
    def load_private_key(self,key_path):
        """Load the private key from file."""
        with open(key_path, "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

    def create_signature(self,private_key, timestamp, method, path):
        """Create the request signature."""
        # Strip query parameters before signing
        path_without_query = path.split('?')[0]
        message = f"{timestamp}{method}{path_without_query}".encode('utf-8')
        signature = private_key.sign(
            message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')

    def get(self, private_key, api_key_id, path,base_url=None):
        """Make an authenticated GET request to the Kalshi API."""
        if(base_url==None):
            base_url=self.BASE_URL
        timestamp = str(int(datetime.datetime.now().timestamp() * 1000))
        signature = self.create_signature(private_key, timestamp, "GET", path)

        headers = {
            'KALSHI-ACCESS-KEY': api_key_id,
            'KALSHI-ACCESS-SIGNATURE': signature,
            'KALSHI-ACCESS-TIMESTAMP': timestamp
        }

        return requests.get(base_url + path, headers=headers)
    def get_order_book(self, market_id):
        """
        The order book shows all active bid orders for both yes and no sides of a binary market.
        don't forget about the reciprical nature of the contracts: yes bid at 20 is used for same order of no ask at 80 
        It returns yes bids and no bids only! 
        if you index by no or yes format is in [cents, contracts available]
        if you index by no_dollars or yes_dollars format is in [dollars, contracts available]
        """
        
        orderbook_response = self.get(self.private_key, self.API_KEY_ID, f"/trade-api/v2/markets/{market_id}/orderbook")
        orderbook_data = orderbook_response.json()
        return orderbook_data

    def get_portfolio_balance(self):#cash available in account in dollars
        response = self.get(self.private_key, self.API_KEY_ID, "/trade-api/v2/portfolio/balance")
        return f"{response.json()['balance'] / 100:.2f}"
    def get_portfolio_value(self):#market val of positions in dollars-api docs say total so there might be an error
        response = self.get(self.private_key, self.API_KEY_ID, "/trade-api/v2/portfolio/balance")
        return f"{response.json()['portfolio_value'] / 100:.2f}"
    def get_fills(self):#filter by market could be future one
        response = self.get(self.private_key, self.API_KEY_ID, "/trade-api/v2/portfolio/fills")
        return response.json()
    def get_fills_by_market(self):#will return all fills related to market ticker
        pass
    
    def get_order_groups(self):
        response = self.get(self.private_key, self.API_KEY_ID, "/trade-api/v2/portfolio/order_groups")
        return response.json()
    def get_order_group(self, order_group_id):
        response = self.get(self.private_key, self.API_KEY_ID, f"/trade-api/v2/portfolio/order_groups/{str(order_group_id)}")
        return response.json()
    
    def get_order_groups(self):#for future to https://docs.kalshi.com/api-reference/portfolio/get-orders 
        #then make more based on the query parameters
        response = self.get(self.private_key, self.API_KEY_ID, "/trade-api/v2/portfolio/order_groups")
        return response.json()
        
    def post(self,private_key, api_key_id, path, data, base_url=None):
        """Make an authenticated POST request to the Kalshi API."""
        if(base_url==None):
            base_url=self.BASE_URL
        timestamp = str(int(datetime.datetime.now().timestamp() * 1000))
        signature = self.create_signature(private_key, timestamp, "POST", path)

        headers = {
            'KALSHI-ACCESS-KEY': api_key_id,
            'KALSHI-ACCESS-SIGNATURE': signature,
            'KALSHI-ACCESS-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }

        return requests.post(base_url + path, headers=headers, json=data)
    
    def place_limit_order(self,market_id:str, sell_or_buy:str, yes_or_no:str, contract_count:int,price:int):
        '''
        sell_or_buy must be buy or sell string, yes_or_no must be yes or no string
        '''
        order_data = {
            "ticker": market_id,
            "action": sell_or_buy,
            "side": yes_or_no,
            "count": contract_count,
            "type": 'limit',
            "yes_price": price,
            "client_order_id": str(uuid.uuid4())  # Unique ID for deduplication
        }
        response = self.post(self.private_key, self.API_KEY_ID, '/trade-api/v2/portfolio/orders', order_data)
        return response
    
    def place_trades_given_portfolio_at_closest_bid(self, portfolio:dict):
        '''
        portfolio is a dictionary that points to 2d array with each market as an array with its tickers/yes_or_no trade as another. order of ticker array is series, event, market
        for example, yess/no  ' 'Politics': [['KXGOVSHUTLENGTH', 'KXGOVSHUTLENGTH-26JAN01','KXGOVSHUTLENGTH-26JAN01-38D'],['KXEPSTEINBILL','KXEPSTEINBILL-26JAN01', 'KXEPSTEINBILL-26JAN01']]
        '''
        for sector in portfolio.keys():
            for market in range(len(portfolio[sector])):
                market_ticker = portfolio[sector][market][2]
                try:
                    
                    yes_or_no_trade  = portfolio[sector][market][3]
                    orderbook  = self.get_order_book(market_ticker)
                    
                    closest_price = 0 
                    if yes_or_no_trade=='yes':
                        closest_price = 100 - int(orderbook['orderbook']['no'][-1][0])
                    elif yes_or_no_trade=='no':
                        closest_price = 100- int(orderbook['orderbook']['yes'][-1][0])
                    print(closest_price)
                    self.place_limit_order(market_ticker,'buy',yes_or_no_trade,1, closest_price)
                except Exception:
                    print(f'order_issue for {market_ticker}')
            
            