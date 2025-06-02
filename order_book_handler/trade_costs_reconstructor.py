import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import order_book_handler.order_book_reconstructor as ob_reconstruction
from typing import Dict

def calculate_implicit_trade_cost_by_product_by_day(
    trades_csv_filepath: str,
    orders_csv_filepath: str,
    product_name: str
):
    trades_one_day = pd.read_csv(
        trades_csv_filepath,
        header=1,
        usecols=['Product', 'Side', 'DeliveryStart', 'ExecutionTime', 'Price', 'Volume'],
        dtype={
            'Price': float,
            'Volume': float
        },
        parse_dates=['ExecutionTime', 'DeliveryStart']
    )
    
    trades_one_day_one_product = trades_one_day[trades_one_day['Product'] == product_name]
    unique_trades_one_day_one_product = trades_one_day_one_product[trades_one_day_one_product['Side'] == 'BUY']  # Arbitrarily filter to get only the unique trades (since both buy and sell feature in the trade book)
    
    order_book_by_delivery_start_time = ob_reconstruction.reconstruct_order_book_one_product_one_day(
        orders_csv_filepath,
        product_name
    )
    
    midprice_df_by_delivery_start_time = {
        delivery_start_time: pd.DataFrame.from_dict(
            order_book.mid_price_over_time,
            orient='index',
            columns=['mid_price']
        )
        for delivery_start_time, order_book in order_book_by_delivery_start_time.items()
    }
    
    implicit_trade_costs_and_volumes = {}
    
    for delivery_start_time, midprice_df in midprice_df_by_delivery_start_time.items():
        trades_for_delivery_start_time = unique_trades_one_day_one_product[unique_trades_one_day_one_product['DeliveryStart'] == delivery_start_time]
        trade_costs = {}
        execution_times = trades_for_delivery_start_time['ExecutionTime'].sort_values()
        midprice_times = midprice_df.index.sort_values()
        
        closest_index = np.searchsorted(midprice_times, execution_times, side='right') - 1
        closest_times = midprice_times[closest_index]
        previous_mid_prices = pd.Series(midprice_df.loc[closest_times, 'mid_price']).values
        prices = trades_for_delivery_start_time['Price'].to_numpy()
        volumes = trades_for_delivery_start_time['Volume'].values
        implicit_trade_costs = np.abs(prices - previous_mid_prices)
        #TODO - may be ablke to delete this, once happy with the vectorised operations
        for index, trade_row in trades_for_delivery_start_time.iterrows():
            execution_time = trade_row['ExecutionTime']
            earlier_times = midprice_df[midprice_df.index < execution_time]
            closest_earlier_time = earlier_times.index[-1]
            previous_mid_price = midprice_df.loc[closest_earlier_time, 'mid_price']
            implicit_trade_cost = abs(trade_row['Price'] - previous_mid_price)
            trade_costs[execution_time] = (implicit_trade_cost, trade_row['Volume'])
        #Delete up to here, and then change the conversion to a dataframe
        implicit_trade_costs_and_volumes[delivery_start_time] = pd.DataFrame.from_dict(
            trade_costs,
            orient='index',
            columns=['implicit_trade_cost', 'trade_volume']
        )
        print(f"Implicit trade costs calculated for delivery start time: {delivery_start_time}")
    
    return implicit_trade_costs_and_volumes

#This calculates the trade costs for the aggressor, based on the later order ID in a transaction pair
def calculate_implicit_trade_costs_by_side_by_product_by_day(
    trades_csv_filepath: str,
    orders_csv_filepath: str,
    product_name: str
):
    trades_one_day = pd.read_csv(
        trades_csv_filepath,
        header=1,
        usecols=['TradeId', 'Product', 'Side', 'DeliveryStart', 'ExecutionTime', 'Price', 'Volume', 'OrderID']
    )
    
    trades_one_day_one_product = trades_one_day[trades_one_day['Product'] == product_name]
    
    order_book_by_delivery_start_time = ob_reconstruction.reconstruct_order_book_one_product_one_day(
        orders_csv_filepath,
        product_name
    )
    
    midprice_df_by_delivery_start_time = {
        delivery_start_time: pd.DataFrame.from_dict(
            order_book.mid_price_over_time,
            orient='index',
            columns=['mid_price']
        )
        for delivery_start_time, order_book in order_book_by_delivery_start_time.items()
    }
    
    implicit_buy_costs_by_start_time = {}
    implicit_sell_costs_by_start_time = {}
    
    for delivery_start_time, midprice_df in midprice_df_by_delivery_start_time.items():
        trades_for_delivery_start_time = trades_one_day_one_product[trades_one_day_one_product['DeliveryStart'] == delivery_start_time]
        buy_costs = {}
        sell_costs = {}
        #TODO - the same goes for here as the function above
        for trade_id, trades in trades_for_delivery_start_time.groupby('TradeId'):
            max_orderid_row = trades.loc[trades['OrderID'].idxmax()]
            execution_time = max_orderid_row['ExecutionTime']
            side = str(max_orderid_row['Side'])
            price = max_orderid_row['Price']
            volume = max_orderid_row['Volume']

            earlier_times = midprice_df[midprice_df.index < execution_time]
            
            if not earlier_times.empty:
                closest_earlier_time = earlier_times.index[-1]
                previous_mid_price = midprice_df.loc[closest_earlier_time, 'mid_price']
                if side == 'BUY':
                    implicit_trade_cost = price - previous_mid_price # type: ignore
                    buy_costs[execution_time] = (abs(implicit_trade_cost), volume, price)
                elif side == 'SELL':
                    implicit_trade_cost = previous_mid_price - price # type: ignore
                    sell_costs[execution_time] = (abs(implicit_trade_cost), volume, price)

        implicit_buy_costs_by_start_time[delivery_start_time] = pd.DataFrame.from_dict(
            buy_costs,
            orient='index',
            columns=['implicit_trade_cost', 'trade_volume', 'trade_price']
        )
        implicit_sell_costs_by_start_time[delivery_start_time] = pd.DataFrame.from_dict(
            sell_costs,
            orient='index',
            columns=['implicit_trade_cost', 'trade_volume', 'trade_price']
        )
        print(f"Implicit trade costs by side calculated for delivery start time: {delivery_start_time}")

    return implicit_buy_costs_by_start_time, implicit_sell_costs_by_start_time
