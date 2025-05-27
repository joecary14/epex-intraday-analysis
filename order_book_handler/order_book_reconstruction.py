import pandas as pd
import order_book_handler.order_book as ob
import order_book_handler.order as o
from typing import cast
from time import time

def reconstruct_order_book_one_product_one_day(
    orders_csv_filepath : str,
    product_name : str
):
    orders = pd.read_csv(
        orders_csv_filepath, 
        header=1,
        usecols=['InitialId', 'Side', 'Product', 'DeliveryStart', 'ActionCode', 'TransactionTime', 'Price', 'Volume']
    )
    orders = orders[orders['Product'] == product_name]
    order_book_by_delivery_start_time = {}
    orders_by_settlement_period = orders.groupby('DeliveryStart')
    for delivery_start_time, orders_one_settlement_period in orders_by_settlement_period:
        start_time = time()
        order_book = ob.OrderBook()
        orders_by_settlement_period_by_transaction_time = orders_one_settlement_period.groupby('TransactionTime')
        for transaction_time, orders_by_transaction_time in orders_by_settlement_period_by_transaction_time:
            orders_by_initial_id = orders_by_transaction_time.groupby('InitialId')
            for initial_id, orders_for_id in orders_by_initial_id:
                order_book_side = orders_for_id.iloc[0]['Side']
                for index, order_row in orders_for_id.iterrows():
                    action_code = order_row['ActionCode']
                    order = o.Order(
                        initial_id=order_row['InitialId'],
                        price=order_row['Price'],
                        available_volume=order_row['Volume']
                    )
                    action_method = order_book.action_code_to_action[action_code]
                    action_method(order_book, order, order_book_side)
            order_book.calculate_order_book_features(str(transaction_time))
        
        order_book_by_delivery_start_time[delivery_start_time] = order_book
        order_book.visualise_bas_over_time()
        end_time = time()
        print("time taken for order book reconstruction for delivery start time", delivery_start_time, ":", end_time - start_time, "seconds")
    
    return order_book_by_delivery_start_time
            
        