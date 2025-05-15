import pandas as pd
import transaction
from pandas.core.groupby import DataFrameGroupBy

class OrderBook:
    def __init__(
        self
    ):
        self.bids = {}
        self.asks = {}
        self.bids_df = pd.DataFrame()
        self.asks_df = pd.DataFrame()
        self.current_best_bid = None
        self.current_best_ask = None
        self.best_bid_over_time = {}
        self.best_ask_over_time = {}
        
    def add_transaction(
        self,
        order : pd.Series,
        order_index : int,
        orders_in_transaction_group : DataFrameGroupBy,
        transaction_time : str,
        initial_id : int
    ):
        side = order['Side']
        price = order['Price']
        quantity = order['Volume']
        
        if side == 'BUY':
            next_index = order_index + 1
            try:
                next_order = orders_in_transaction_group.get_group(next_index)
            except KeyError:
                next_order = None
            
            if next_order is None:
                if price > self.current_best_bid:
                    self.current_best_bid = price
                    self.best_bid_over_time[transaction_time] = price
                
                self.bids[initial_id] = (price, quantity)
    
    