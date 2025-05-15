import pandas as pd
import order_book as ob

def reconstruct_order_book_one_product_one_day(
    orders_csv_filepath : str,
    product_name : str
):
    orders = pd.read_csv(orders_csv_filepath, usecols=['InitialId', 'Side', 'Product', 'DeliveryStartTime', 'ActionCode', 'TransactionTime', 'Price', 'Volume'])
    orders = orders[orders['Product'] == product_name]
    
    order_book = ob.OrderBook()
    
    orders_by_settlement_period = orders.groupby('DeliveryStartTime')
    for delivery_start_time, orders_one_settlement_period in orders_by_settlement_period:
        orders_by_settlement_period_by_transaction_time = orders_one_settlement_period.groupby('TransactionTime')
        for transaction_time, orders_by_transaction_time in orders_by_settlement_period_by_transaction_time:
            orders_by_initial_id = orders_by_transaction_time.groupby('InitialId')
            for initial_id, orders in orders_by_initial_id:
                for index, order in orders.iterrows():
                    action_code = order['ActionCode']