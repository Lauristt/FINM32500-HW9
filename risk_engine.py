from collections import defaultdict
from order import Order  # Import Order to use type hinting


class RiskEngine:
    """
    Manages pre-trade risk checks and post-trade position updates.

    Tracks positions per symbol.
    """

    def __init__(self, max_order_size: int = 1000, max_position: int = 2000):
        """
        Initializes the risk engine with default or specified limits.

        Args:
            max_order_size: The maximum quantity allowed for a single order.
            max_position: The maximum absolute net position allowed per symbol.
        """
        if max_order_size <= 0 or max_position <= 0:
            raise ValueError("Risk limits must be positive")

        self.max_order_size = max_order_size
        self.max_position = max_position
        # Use defaultdict to automatically handle new symbols with a starting position of 0
        self.positions = defaultdict(int)
        print(f"RiskEngine Initialized: MaxOrderSize={max_order_size}, MaxPosition={max_position}")

    def check(self, order: Order) -> bool:
        """
        Performs pre-trade risk checks on a new order.

        Args:
            order: The Order object to check.

        Returns:
            True if the order passes all checks.

        Raises:
            ValueError: If the order fails a risk check.
        """
        # 1. Check order size limit
        if order.qty > self.max_order_size:
            raise ValueError(f"Risk Check Failed: Order size {order.qty} "
                             f"exceeds limit {self.max_order_size}")

        # 2. Check position limit
        current_position = self.positions[order.symbol]

        if order.side == '1':  # Buy
            new_position = current_position + order.qty
        elif order.side == '2':  # Sell
            new_position = current_position - order.qty
        else:
            # This should be caught by the Order class, but good to have defense
            raise ValueError(f"Invalid order side: {order.side}")

        if abs(new_position) > self.max_position:
            raise ValueError(f"Risk Check Failed: New position {new_position} "
                             f"for {order.symbol} exceeds limit {self.max_position} "
                             f"(Current: {current_position})")

        # If all checks pass
        print(f"Risk Check OK: {order.order_id} ({order.symbol})")
        return True

    def update_position(self, order: Order):
        """
        Updates the net position for a symbol based on a filled order.
        This should only be called *after* an order is confirmed filled.

        Args:
            order: The *filled* Order object.
        """
        if order.side == '1':  # Buy
            self.positions[order.symbol] += order.qty
        elif order.side == '2':  # Sell
            self.positions[order.symbol] -= order.qty

        print(f"Position Update: {order.symbol} is now {self.positions[order.symbol]}")

    def get_position(self, symbol: str) -> int:
        """Helper to get current position for a symbol."""
        return self.positions[symbol]


if __name__ == "__main__":
    # Example usage
    from order import Order, OrderState

    risk = RiskEngine(max_order_size=500, max_position=1000)

    # Valid order
    print("\n--- Test Case 1: Valid Order ---")
    order1 = Order("B001", "AAPL", 300, '1')  # Buy 300
    try:
        risk.check(order1)
        order1.transition(OrderState.ACKED)
        # Simulate fill
        risk.update_position(order1)
        order1.transition(OrderState.FILLED)
    except ValueError as e:
        print(f"REJECTED: {e}")
        order1.transition(OrderState.REJECTED)
    print(f"Final Position AAPL: {risk.get_position('AAPL')}")

    #Order size rejection
    print("\n--- Test Case 2: Order Size Rejection ---")
    order2 = Order("B002", "MSFT", 600, '1')  # Qty 600 > 500 limit
    try:
        risk.check(order2)
        order2.transition(OrderState.ACKED)
    except ValueError as e:
        print(f"REJECTED: {e}")
        order2.transition(OrderState.REJECTED)
    print(f"Final Position MSFT: {risk.get_position('MSFT')}")

    #Position limit rejection
    print("\n--- Test Case 3: Position Limit Rejection ---")
    order3 = Order("B003", "AAPL", 800, '1')  # Buy 800
    # Current AAPL pos = 300. New pos = 300 + 800 = 1100 > 1000 limit
    try:
        risk.check(order3)
        order3.transition(OrderState.ACKED)
    except ValueError as e:
        print(f"REJECTED: {e}")
        order3.transition(OrderState.REJECTED)
    print(f"Final Position AAPL: {risk.get_position('AAPL')}")

    #Valid sell order
    print("\n--- Test Case 4: Valid Sell Order ---")
    order4 = Order("B004", "AAPL", 200, '2')  # Sell 200
    # Current AAPL pos = 300. New pos = 300 - 200 = 100. OK.
    try:
        risk.check(order4)
        order4.transition(OrderState.ACKED)
        # Simulate fill
        risk.update_position(order4)
        order4.transition(OrderState.FILLED)
    except ValueError as e:
        print(f"REJECTED: {e}")
        order4.transition(OrderState.REJECTED)
    print(f"Final Position AAPL: {risk.get_position('AAPL')}")