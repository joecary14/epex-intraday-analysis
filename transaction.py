class Transaction:
    def  __init__(
        self,
        initial_id : int,
        buy_side : bool,
        action_code : str,
        price : float,
        quantity : float
    ):
        self.initial_id = initial_id
        self.buy_side = buy_side
        self.action_code = action_code
        self.price = price
        self.quantity = quantity
    