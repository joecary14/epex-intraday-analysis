import pandas as pd
import matplotlib.pyplot as plt
import order_book_handler.order_book_reconstructor as ob_reconstruction
from typing import Dict
import os

def calculate_implicit_trade_cost_by_product_by_day(
    trades_csv_filepath: str,
    orders_csv_filepath: str,
    product_name: str
):
    trades_one_day = pd.read_csv(
        trades_csv_filepath,
        header=1,
        usecols=['Product', 'Side', 'DeliveryStart', 'ExecutionTime', 'Price', 'Volume']
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
    
    implicit_trade_costs = {}
    
    for delivery_start_time, midprice_df in midprice_df_by_delivery_start_time.items():
        trades_for_delivery_start_time = trades_one_day_one_product[trades_one_day_one_product['DeliveryStart'] == delivery_start_time]
        unique_trades_for_delivery_start_time = trades_for_delivery_start_time[trades_for_delivery_start_time['Side']=='BUY'] #Arbitrarily filter to get only the unique trades (since both buy and sell feature in the trade book)
        trade_costs = {}
        for index, trade_row in unique_trades_for_delivery_start_time.iterrows():
            execution_time = trade_row['ExecutionTime']
            earlier_times = midprice_df[midprice_df.index < execution_time]
            closest_earlier_time = earlier_times.index[-1]
            previous_mid_price = midprice_df.loc[closest_earlier_time, 'mid_price']
            implicit_trade_cost = abs(trade_row['Price'] - previous_mid_price)
            trade_costs[execution_time] = implicit_trade_cost
        
        implicit_trade_costs[delivery_start_time] = pd.DataFrame.from_dict(
            trade_costs,
            orient='index',
            columns=['implicit_trade_cost']
        )
    
    return implicit_trade_costs
    

def visualise_trade_costs_by_product_by_day(
    implicit_trade_costs: Dict[str, pd.DataFrame],
    hours_before_end_of_session_to_visualise: int,
    output_filepath: str
):
    for delivery_start_time, df in implicit_trade_costs.items():
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df.index):
            df.index = pd.to_datetime(df.index)
        max_time = df.index.max()
        min_time = max_time - pd.Timedelta(hours=hours_before_end_of_session_to_visualise)
        df_filtered = df[df.index >= min_time]
        interval = pd.Timedelta(minutes=15)
        tick_times = pd.date_range(start=df_filtered.index.min(), end=df_filtered.index.max(), freq=interval)
        
        plt.figure(figsize=(10, 5))
        plt.scatter(df_filtered.index, df_filtered['implicit_trade_cost'])
        plt.title(f"Implicit Trade Costs - Delivery Start: {delivery_start_time}")
        plt.xticks(tick_times)
        plt.xlabel("Execution Time")
        plt.ylabel("Implicit Trade Cost")
        plt.xticks(rotation=45)
        plt.tight_layout()

    base, ext = os.path.splitext(output_filepath)
    for i, fig_num in enumerate(plt.get_fignums(), 1):
        plt.figure(fig_num)
        plt.savefig(f"{base}_{i}.png")
        plt.close()
    
