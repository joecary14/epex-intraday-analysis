import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timedelta
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
        
        best_bid = bids_df['price'].max()
        best_ask = asks_df['price'].min()
        bid_ask_spread = best_ask - best_bid
        mid_price = (best_ask - best_bid) / 2 + best_bid
        relative_bid_ask_spread_over_time = 100 * bid_ask_spread / mid_price if mid_price != 0 else 0
        
        if best_bid > self.current_best_bid:
            self.current_best_bid = best_bid
            self.best_bid_over_time[transaction_time] = best_bid
        if best_ask < self.current_best_ask:
            self.current_best_ask = best_ask
            self.best_ask_over_time[transaction_time] = best_ask
        if bid_ask_spread != self.current_bid_ask_spread:
            self.current_bid_ask_spread = bid_ask_spread
            self.bid_ask_spread_over_time[transaction_time] = bid_ask_spread
        if mid_price != self.current_mid_price:
            self.current_mid_price = mid_price
            self.mid_price_over_time[transaction_time] = mid_price
        if relative_bid_ask_spread_over_time != self.current_relative_bid_ask_spread:
            self.current_relative_bid_ask_spread = relative_bid_ask_spread_over_time
            self.relative_bid_ask_spread_over_time[transaction_time] = relative_bid_ask_spread_over_time
        
    def visualise_relative_bas_over_time(
        self,
        hours_before_end_of_trading_session_to_visualise
    ):
        
        latest_time = max(datetime.fromisoformat(t) for t in self.relative_bid_ask_spread_over_time.keys())
        three_hours_ago = latest_time - timedelta(hours=hours_before_end_of_trading_session_to_visualise)

        filtered = {
            t: v for t, v in self.relative_bid_ask_spread_over_time.items()
            if datetime.fromisoformat(t) >= three_hours_ago
        }
        if not filtered:
            print("No data in the last three hours to plot.")
            return
        times = list(filtered.keys())
        spreads = list(filtered.values())
        times_dt = [datetime.fromisoformat(t) for t in times]
        times_array = np.array(times_dt)

        plt.figure(figsize=(12, 6))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator())
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

        plt.plot(times_array, spreads, label='Bid-Ask Spread')
        plt.xlabel('Transaction Time')
        plt.ylabel('Bid-Ask Spread')
        plt.title('Bid-Ask Spread Over Time')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    
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