import order_book_handler.order_book_reconstructor as obr
import order_book_handler.trade_costs_reconstructor as tcr

orders_csv_filepath = '/Users/josephcary/Library/CloudStorage/OneDrive-Nexus365/First Year/Data/EPEX/Continuous_Orders-GB-20240126-20240127T044441000Z.csv'
trades_csv_filepath = '/Users/josephcary/Library/CloudStorage/OneDrive-Nexus365/First Year/Data/EPEX/Continuous_Trades-GB-20240126-20240127T002144000Z.csv'
product_name = 'GB_Half_Hour_Power'
output_filepath = '/Users/josephcary/Library/CloudStorage/OneDrive-Nexus365/First Year/Papers/Intraday Trading/Analysis/'
hours_before_end_of_session_to_visualise = 3

def main():
    implicit_trade_costs = tcr.calculate_implicit_trade_cost_by_product_by_day(
        trades_csv_filepath,
        orders_csv_filepath,
        product_name
    )
    tcr.visualise_trade_costs_by_product_by_day(
        implicit_trade_costs,
        hours_before_end_of_session_to_visualise,
        output_filepath
    )

main()