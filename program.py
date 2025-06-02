import order_book_handler.order_book_reconstructor as obr
import order_book_handler.trade_costs_reconstructor as tcr
import order_book_handler.data_visualisation as dv

orders_csv_filepath = '/Users/josephcary/Library/CloudStorage/OneDrive-Nexus365/First Year/Data/EPEX/Continuous_Orders-GB-20240126-20240127T044441000Z.csv'
trades_csv_filepath = '/Users/josephcary/Library/CloudStorage/OneDrive-Nexus365/First Year/Data/EPEX/Continuous_Trades-GB-20240126-20240127T002144000Z.csv'
product_name = 'GB_Half_Hour_Power'
output_filepath = '/Users/josephcary/Library/CloudStorage/OneDrive-Nexus365/First Year/Papers/Intraday Trading/Analysis/'
hours_before_end_of_session_to_visualise = 10

def main():
    buy_costs, sell_costs = tcr.calculate_relative_implicit_trade_costs_by_side_by_product_by_day(
        trades_csv_filepath,
        orders_csv_filepath,
        product_name
    )
    dv.visualise_buy_sell_trade_costs(
        buy_costs,
        sell_costs,
        hours_before_end_of_session_to_visualise,
        output_filepath,
    )

main()