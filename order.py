"""
Part 2: Order Lifecycle Simulator

This module defines the OrderState enum and the Order class,
which manages the state transitions of a trade order.
"""

from enum import Enum, auto
import sys


class OrderState(Enum):
    """Enumeration of possible order states."""
    NEW = auto()  # Just created, not yet sent to market
    ACKED = auto()  # Acknowledged by the market (risk-checked)
    FILLED = auto()  # Completely filled
    CANCELED = auto()  # Canceled by user (only possible if ACKED)
    REJECTED = auto()  # Rejected by risk engine or market


class Order:
    """
    Represents a single trade order and its state lifecycle.
    """

    def __init__(self, order_id: str, symbol: str, qty: int, side: str):
        """
        Initializes a new order.

        Args:
            order_id: A unique identifier for the order.
            symbol: The financial instrument (e.g., 'AAPL').
            qty: The order quantity (must be positive).
            side: The side of the order ('1' for Buy, '2' for Sell).
        """
        if not isinstance(qty, int) or qty <= 0:
            raise ValueError("Quantity must be a positive integer")
        if side not in {'1', '2'}:
            raise ValueError("Side must be '1' (Buy) or '2' (Sell)")

        self.order_id = order_id
        self.symbol = symbol
        self.qty = qty
        self.side = side  # '1' = Buy, '2' = Sell
        self.state = OrderState.NEW

        # Define the allowed state transitions
        self.allowed_transitions = {
            OrderState.NEW: {OrderState.ACKED, OrderState.REJECTED},
            OrderState.ACKED: {OrderState.FILLED, OrderState.CANCELED, OrderState.REJECTED},
            OrderState.FILLED: set(),
            OrderState.CANCELED: set(),
            OrderState.REJECTED: set(),
        }

    def transition(self, new_state: OrderState):
        """
        Attempts to transition the order to a new state.

        If the transition is allowed, the order's state is updated.
        If not, an error is printed to stderr.

        Args:
            new_state: The OrderState to transition to.
        """
        if new_state in self.allowed_transitions.get(self.state, set()):
            print(f"Order {self.order_id} ({self.symbol}): {self.state.name} -> {new_state.name}")
            self.state = new_state
        else:
            # In a real system, this would be a critical log
            print(f"INVALID TRANSITION: Order {self.order_id} ({self.symbol}) "
                  f"cannot move from {self.state.name} to {new_state.name}", file=sys.stderr)

    def __str__(self):
        side_str = "Buy" if self.side == '1' else "Sell"
        return f"Order(ID={self.order_id}, {self.symbol}, {side_str} {self.qty}, State={self.state.name})"


if __name__ == "__main__":
    # Example usage

    #Valid flow
    print("--- Valid Flow ---")
    order1 = Order("A001", "AAPL", 100, '1')
    print(order1)
    order1.transition(OrderState.ACKED)
    print(order1)
    order1.transition(OrderState.FILLED)
    print(order1)

    #Rejection flow
    print("\n--- Rejection Flow ---")
    order2 = Order("A002", "MSFT", 500, '2')
    print(order2)
    order2.transition(OrderState.REJECTED)
    print(order2)

    #Invalid transition attempt
    print("\n--- Invalid Transition ---")
    order3 = Order("A003", "GOOG", 50, '1')
    print(order3)
    order3.transition(OrderState.FILLED)  # Not allowed from NEW
    print(order3)
    order3.transition(OrderState.ACKED)  # This one is allowed
    print(order3)
    order3.transition(OrderState.NEW)  # Not allowed from ACKED
    print(order3)