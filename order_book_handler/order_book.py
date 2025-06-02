import pandas as pd
import numpy as np
import order_book_handler.order as order
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class OrderBook:
    def __init__(
        self
    ):
        self.orders = {
            'BUY': {},
            'SELL': {}
        }
        
        self.hibernated_orders = {
            'BUY': {},
            'SELL': {}
        }
        #TODO - issues with some of these numbers being negative
        self.current_best_bid = -10000
        self.current_best_ask = 10000
        self.current_bid_ask_spread = 20000
        self.current_mid_price = 100000
        self.current_relative_bid_ask_spread = 0
        
        self.best_bid_over_time = {}
        self.best_ask_over_time = {}
        self.bid_ask_spread_over_time = {}
        self.mid_price_over_time = {}
        self.relative_bid_ask_spread_over_time = {}
    
    def calculate_order_book_features(
        self,
        transaction_time: str
    ) -> None:
        bids_df = pd.DataFrame.from_dict(self.orders['BUY'], orient='index')
        asks_df = pd.DataFrame.from_dict(self.orders['SELL'], orient='index')
        
        no_bids = bids_df.empty == True
        no_asks = asks_df.empty == True
        
        if no_bids or no_asks:
            return
        
        self.recalculate_order_book_features(
            bids_df,
            asks_df,
            transaction_time
        )
    
    def add_order(
        self,
        order : order.Order,
        order_side : str
    ):  
        if self.orders[order_side].get(order.initial_id) is not None:
            raise ValueError(f"Order with initial_id {order.initial_id} already exists in {order_side} orders.")
        else:
            self.orders[order_side][order.initial_id] = order
        
        try:
            del self.hibernated_orders[order_side][order.initial_id]
        except KeyError:
            return
    
    def change_existing_order(
        self,
        order: order.Order,
        order_side: str
    ):
        if self.orders[order_side].get(order.initial_id) is None and self.hibernated_orders[order_side].get(order.initial_id) is None:
            raise ValueError(f"Order with initial_id {order.initial_id} does not exist in {order_side} orders.")
        else:
            if self.hibernated_orders[order_side].get(order.initial_id) is not None:
                self.hibernated_orders[order_side][order.initial_id] = order
            else:
                self.orders[order_side][order.initial_id] = order
    
    def delete_order(
        self,
        order: order.Order,
        order_side: str
    ):
        try:
            del self.orders[order_side][order.initial_id]
        except KeyError:
            try:
                del self.hibernated_orders[order_side][order.initial_id]
            except KeyError:
                raise KeyError(f"Order with initial_id {order.initial_id} does not exist in {order_side} orders.")
            
    def hibernate_order(
        self,
        order: order.Order,
        order_side: str
    ):
        try:
            del self.orders[order_side][order.initial_id]
            self.hibernated_orders[order_side][order.initial_id] = order
        except KeyError:
            raise KeyError(f"Order with initial_id {order.initial_id} does not exist in {order_side} orders.")
      
    def recalculate_order_book_features(
        self,
        bids_df: pd.DataFrame,
        asks_df: pd.DataFrame,
        transaction_time: str
    ):  
        best_bid = bids_df['price'].max()
        best_ask = asks_df['price'].min()
        
        if best_bid >= best_ask:
            n = 2
            if best_bid != self.current_best_bid:
                while best_bid >= best_ask:
                    n += 1
                    best_bid = bids_df['price'].nlargest(n).iloc[1]
            else:
                while best_ask <= best_bid:
                    n += 1
                    best_ask = asks_df['price'].nsmallest(n).iloc[1]
        
        self.update_all_order_book_features(
            best_bid,
            best_ask,
            transaction_time
        )
    
    def update_all_order_book_features(
        self,
        best_bid: float,
        best_ask: float,
        transaction_time: str
    ):
        bid_ask_spread = best_ask - best_bid
        mid_price = (best_ask + best_bid) / 2
        relative_bid_ask_spread_over_time = 100 * bid_ask_spread / mid_price if mid_price != 0 else 0
        
        self.current_best_bid = self.update_order_book_feature(best_bid, self.current_best_bid, self.best_bid_over_time, transaction_time)
        self.current_best_ask = self.update_order_book_feature(best_ask, self.current_best_ask, self.best_ask_over_time, transaction_time)
        self.current_bid_ask_spread = self.update_order_book_feature(bid_ask_spread, self.current_bid_ask_spread, self.bid_ask_spread_over_time, transaction_time)
        self.current_mid_price = self.update_order_book_feature(mid_price, self.current_mid_price, self.mid_price_over_time, transaction_time)
        self.current_relative_bid_ask_spread = self.update_order_book_feature(relative_bid_ask_spread_over_time, self.current_relative_bid_ask_spread, self.relative_bid_ask_spread_over_time, transaction_time)
    
    def update_order_book_feature(
        self,
        new_value: float,
        value_to_update: float,
        values_over_time_to_update: dict,
        transaction_time: str
    ) -> float:
        if new_value != value_to_update:
            values_over_time_to_update[transaction_time] = new_value
            return new_value

        return value_to_update
            
    action_code_to_action = {
        'A': add_order,
        'C': change_existing_order,
        'D': delete_order,
        'P': change_existing_order,
        'M': delete_order,
        'X': delete_order,
        'H': hibernate_order,
        'I': change_existing_order
    }