import os
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict


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
            buy_merged = buy_costs_filtered.copy()
            sell_merged = sell_costs_filtered.copy()
            # Calculate total implicit trade cost and total trade cost for buys
            buy_total_implicit_cost = (buy_merged['implicit_trade_cost'] * buy_merged['trade_volume']).sum() if not buy_merged.empty else 0
            buy_total_trade_cost = (buy_merged['trade_price'] * buy_merged['trade_volume']).sum() if not buy_merged.empty else 0
            buy_ratio = (buy_total_implicit_cost / buy_total_trade_cost) if buy_total_trade_cost > 0 else float('nan')

            # Calculate total implicit trade cost and total trade cost for sells
            sell_total_implicit_cost = (sell_merged['implicit_trade_cost'] * sell_merged['trade_volume']).sum() if not sell_merged.empty else 0
            sell_total_trade_cost = (sell_merged['trade_price'] * sell_merged['trade_volume']).sum() if not sell_merged.empty else 0
            sell_ratio = (sell_total_implicit_cost / sell_total_trade_cost) if sell_total_trade_cost > 0 else float('nan')

            # Print ratios on the plot
            plt.gcf().text(
                0.02, 0.95,
                f"Buy: total implicit/total = {buy_ratio:.4%}\nSell: total implicit/total = {sell_ratio:.4%}",
                fontsize=10,
                verticalalignment='top',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='gray')
            )
            if not buy_merged.empty:
                buy_merged['trade_volume'] = buy_merged['trade_volume'] if 'trade_volume' in buy_merged else 1
                buy_vwap = buy_merged.resample('5min').apply(
                    lambda x: (x['implicit_trade_cost'] * x['trade_volume']).sum() / x['trade_volume'].sum()
                    if x['trade_volume'].sum() > 0 else float('nan')
                )
                plt.plot(
                    buy_vwap.index,
                    buy_vwap.values,
                    label='Buy VWAP (5min)',
                    color='green',
                    marker='o'
                )
            if not sell_merged.empty:
                sell_merged['trade_volume'] = sell_merged['trade_volume'] if 'trade_volume' in sell_merged else 1
                sell_vwap = sell_merged.resample('5min').apply(
                    lambda x: (x['implicit_trade_cost'] * x['trade_volume']).sum() / x['trade_volume'].sum()
                    if x['trade_volume'].sum() > 0 else float('nan')
                )
                plt.plot(
                    sell_vwap.index,
                    sell_vwap.values,
                    label='Sell VWAP (5min)',
                    color='red',
                    marker='o'
                )
            plt.ylabel("VWAP Implicit Realtive Trade Cost (5min, %)")
            plt.xlabel("Trade Execution Time")
            plt.title(f"Buy/Sell Implicit Trade Costs - Delivery Start: {delivery_start_time}")
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
    base, ext = os.path.splitext(output_filepath)
    for i, fig_num in enumerate(plt.get_fignums(), 1):
        plt.figure(fig_num)
        plt.savefig(f"{base}_{i}.png")
        plt.close()

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
    
