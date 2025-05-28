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
    trade_volumes = {}
    
    for delivery_start_time, midprice_df in midprice_df_by_delivery_start_time.items():
        trades_for_delivery_start_time = trades_one_day_one_product[trades_one_day_one_product['DeliveryStart'] == delivery_start_time]
        unique_trades_for_delivery_start_time = trades_for_delivery_start_time[trades_for_delivery_start_time['Side']=='BUY'] #Arbitrarily filter to get only the unique trades (since both buy and sell feature in the trade book)
        trade_costs = {}
        volumes = {}
        
        for index, trade_row in unique_trades_for_delivery_start_time.iterrows():
            execution_time = trade_row['ExecutionTime']
            earlier_times = midprice_df[midprice_df.index < execution_time]
            closest_earlier_time = earlier_times.index[-1]
            previous_mid_price = midprice_df.loc[closest_earlier_time, 'mid_price']
            implicit_trade_cost = abs(trade_row['Price'] - previous_mid_price)
            trade_costs[execution_time] = implicit_trade_cost
            volumes[execution_time] = trade_row['Volume']
        
        implicit_trade_costs[delivery_start_time] = pd.DataFrame.from_dict(
            trade_costs,
            orient='index',
            columns=['implicit_trade_cost']
        )
        trade_volumes[delivery_start_time] = pd.DataFrame.from_dict(
            volumes,
            orient='index',
            columns=['trade_volume']
        )
        print(f"Implicit trade costs calculated for delivery start time: {delivery_start_time}")
    
    return implicit_trade_costs, trade_volumes
    

def visualise_trade_costs_by_product_by_day(
    implicit_trade_costs: Dict[str, pd.DataFrame],
    trade_volumes: Dict[str, pd.DataFrame],
    hours_before_end_of_session_to_visualise: int,
    output_filepath: str
):
    for delivery_start_time, trade_costs_df in implicit_trade_costs.items():
        trade_costs_df = trade_costs_df.copy()
        volumes_df = trade_volumes[delivery_start_time].copy()
        trade_costs_df.index = pd.to_datetime(trade_costs_df.index)
        volumes_df.index = pd.to_datetime(volumes_df.index)
        max_time = trade_costs_df.index.max()
        min_time = max_time - pd.Timedelta(hours=hours_before_end_of_session_to_visualise)
        trade_costs_filtered = trade_costs_df[trade_costs_df.index >= min_time]
        volumes_filtered = volumes_df[volumes_df.index >= min_time]
        interval = pd.Timedelta(minutes=15)
        tick_times = pd.date_range(start=trade_costs_filtered.index.min(), end=trade_costs_filtered.index.max(), freq=interval)
        # Resample to 5-minute windows, computing volume-weighted average implicit trade cost
        merged = trade_costs_filtered.join(volumes_filtered, how='inner')
        
        plt.figure(figsize=(10, 5))
        if not merged.empty:
            merged = merged.sort_index()
            resampled = merged.resample('5min').apply(
                lambda x: (x['implicit_trade_cost'] * x['trade_volume']).sum() / x['trade_volume'].sum()
                if x['trade_volume'].sum() > 0 else float('nan')
            )
            plt.plot(resampled.index, resampled.values, label='VWAP (5min)', color='orange', marker='x')
            plt.show()
        
    #     plt.step(
    #         trade_costs_filtered.index,
    #         trade_costs_filtered['implicit_trade_cost'],
    #         where='post',
    #         marker='o'
    #     )
    #     plt.title(f"Implicit Trade Costs - Delivery Start: {delivery_start_time}")
    #     plt.xticks(tick_times)
    #     plt.xlabel("Execution Time")
    #     plt.ylabel("Implicit Trade Cost")
    #     plt.xticks(rotation=45)
    #     plt.tight_layout()

    # base, ext = os.path.splitext(output_filepath)
    # for i, fig_num in enumerate(plt.get_fignums(), 1):
    #     plt.figure(fig_num)
    #     plt.savefig(f"{base}_{i}.png")
    #     plt.close()
    
