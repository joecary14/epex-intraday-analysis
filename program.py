import order_book_handler.order_book_reconstruction as obr

orders_csv_filepath = '/Users/josephcary/Library/CloudStorage/OneDrive-Nexus365/First Year/Data/EPEX/Continuous_Orders-GB-20240126-20240127T044441000Z.csv'
product_name = 'GB_Half_Hour_Power'

def main(
    orders_csv_filepath: str,
    product_name: str
):
    obr.reconstruct_order_book_one_product_one_day(
        orders_csv_filepath,
        product_name
    )

main(
    orders_csv_filepath,
    product_name
)