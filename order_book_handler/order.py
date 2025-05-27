from dataclasses import dataclass

@dataclass(slots=True)
class Order:
    initial_id : int
    price : float
    available_volume : float
