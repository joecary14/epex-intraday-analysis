class LimitOrder:
    def __init__(
    self,
    order_id : int,
    price : float,
    available_volume : float
    ):
        self.order_id = order_id
        self.price = price
        self.available_volume = available_volume
