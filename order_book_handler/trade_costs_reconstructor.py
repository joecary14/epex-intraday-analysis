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
        
        for trade_id, trades in trades_for_delivery_start_time.groupby('TradeId'):
            max_orderid_row = trades.loc[trades['OrderID'].idxmax()]

            execution_time = max_orderid_row['ExecutionTime']
            side = str(max_orderid_row['Side'])
            price = max_orderid_row['Price']

            earlier_times = midprice_df[midprice_df.index < execution_time]
            #TODO - there are some occasions where a purchase is happening below the mid price, i.e. the agressor is a buyer and they are pay7ing below the mid price
            if not earlier_times.empty:
                closest_earlier_time = earlier_times.index[-1]
                previous_mid_price = midprice_df.loc[closest_earlier_time, 'mid_price']
                if side == 'BUY':
                    implicit_trade_cost = price - previous_mid_price # type: ignore
                    buy_costs[execution_time] = implicit_trade_cost
                elif side == 'SELL':
                    implicit_trade_cost = previous_mid_price - price # type: ignore
                    sell_costs[execution_time] = implicit_trade_cost
                
                if implicit_trade_cost < 0: # type: ignore
                    banana = 1

        implicit_buy_costs_by_start_time[delivery_start_time] = pd.DataFrame.from_dict(
            buy_costs,
            orient='index',
            columns=['implicit_trade_cost']
        )
        implicit_sell_costs_by_start_time[delivery_start_time] = pd.DataFrame.from_dict(
            sell_costs,
            orient='index',
            columns=['implicit_trade_cost']
        )
        print(f"Implicit trade costs by side calculated for delivery start time: {delivery_start_time}")

    return implicit_buy_costs_by_start_time, implicit_sell_costs_by_start_time
    
def visualise_buy_sell_trade_costs(
    implicit_buy_costs: Dict[str, pd.DataFrame],
    implicit_sell_costs: Dict[str, pd.DataFrame],
    hours_before_end_of_session_to_visualise: int,
    output_filepath: str
):
    for delivery_start_time, buy_costs_df in implicit_buy_costs.items():
        buy_costs_df = buy_costs_df.copy()
        sell_costs_df = implicit_sell_costs[delivery_start_time].copy()
        buy_costs_df.index = pd.to_datetime(buy_costs_df.index)
        sell_costs_df.index = pd.to_datetime(sell_costs_df.index)
        max_time = buy_costs_df.index.max()
        min_time = max_time - pd.Timedelta(hours=hours_before_end_of_session_to_visualise)
        buy_costs_filtered = buy_costs_df[buy_costs_df.index >= min_time]
        sell_costs_filtered = sell_costs_df[sell_costs_df.index >= min_time]
        
        plt.figure(figsize=(10, 5))
        if not buy_costs_filtered.empty or not sell_costs_filtered.empty:
            if not buy_costs_filtered.empty:
                plt.step(
                    buy_costs_filtered.index,
                    buy_costs_filtered['implicit_trade_cost'],
                    where='post',
                    label='Buy Implicit Trade Cost',
                    color='green'
                )
            if not sell_costs_filtered.empty:
                plt.step(
                    sell_costs_filtered.index,
                    sell_costs_filtered['implicit_trade_cost'],
                    where='post',
                    label='Sell Implicit Trade Cost',
                    color='red'
                )
            plt.title(f"Buy/Sell Implicit Trade Costs - Delivery Start: {delivery_start_time}")
            plt.xlabel("Execution Time")
            plt.ylabel("Implicit Trade Cost")
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
    # base, ext = os.path.splitext(output_filepath)
    # for i, fig_num in enumerate(plt.get_fignums(), 1):
    #     plt.figure(fig_num)
    #     plt.savefig(f"{base}_{i}.png")
    #     plt.close()

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
        merged = trade_costs_filtered.join(volumes_filtered, how='inner')
        resampled_vwap = merged.resample('5min').apply(
            lambda x: (x['implicit_trade_cost'] * x['trade_volume']).sum() / x['trade_volume'].sum()
            if x['trade_volume'].sum() > 0 else float('nan')
        )
        resampled_volume = merged['trade_volume'].resample('5min').sum()

        fig, ax1 = plt.subplots(figsize=(10, 5))
        if not merged.empty:
            merged = merged.sort_index()
            ax1.plot(resampled_vwap.index, resampled_vwap.values, label='VWAP (5min)', color='orange', marker='x')
            ax1.set_ylabel('VWAP (5min)', color='orange')
            ax1.tick_params(axis='y', labelcolor='orange')

            ax2 = ax1.twinx()
            ax2.bar(resampled_volume.index, resampled_volume.values, width=0.003, alpha=0.3, color='blue', label='Volume')
            ax2.set_ylabel('Volume', color='blue')
            ax2.tick_params(axis='y', labelcolor='blue')

            plt.title(f"Implicit Trade Costs & Volume - Delivery Start: {delivery_start_time}")
            plt.xticks(tick_times)
            plt.xlabel("Execution Time")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()

    # base, ext = os.path.splitext(output_filepath)
    # for i, fig_num in enumerate(plt.get_fignums(), 1):
    #     plt.figure(fig_num)
    #     plt.savefig(f"{base}_{i}.png")
    #     plt.close()
    
