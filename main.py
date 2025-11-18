try:
    from fix_parser import FixParser
    from order import Order, OrderState
    from risk_engine import RiskEngine
    from logger import Logger  # To create unique order IDs
    from fix_message_generator import FixMessageGenerator  # Import the generator
except ImportError as e:
    print(f'Error when importing.. Module Not Found. Aborting...Error:{e}')
import time

USE_GENERATOR = True
NUMBER_OF_GENERATED_MESSAGES = 10  # How many messages to create if using the generator

try:
    parser = FixParser()
    risk = RiskEngine(max_order_size=1000, max_position=2000)
    # Get the singleton logger instance
    # We'll save the log to 'trading_events.json'
    log = Logger("trading_events.json")
except ValueError as e:
    print(f"Failed to initialize system: {e}")
    exit(1)

log.log("SystemInitialized", {
    "max_order_size": risk.max_order_size,
    "max_position": risk.max_position
})

#Message Stream

if USE_GENERATOR:
    print("\n--- Using FIX Message Generator ---")
    generator = FixMessageGenerator(max_qty=1500)  # Use a slightly larger max_qty to test risk limits
    raw_messages = []
    for i in range(NUMBER_OF_GENERATED_MESSAGES):
        # Create a mix of valid and invalid messages
        if i % 4 == 0:
            raw_messages.append(generator.create_invalid_message())
        else:
            raw_messages.append(generator.create_valid_message())
else:
    print("\n--- Using Hardcoded Message List ---")
    # A list of raw FIX messages to simulate a trading day
    raw_messages = [
        "8=FIX.4.2|35=D|55=AAPL|54=2|38=400|40=1|10=107"
    ]

print("\n--- Processing Message Stream ---")
for i, raw_msg in enumerate(raw_messages):
    print(f"\n--- Processing Message {i + 1} ---")

    order = None
    order_id = f"Ord_{int(time.time())}_{i}"  # Create a simple unique ID

    try:
        #Parse Message
        msg_dict = parser.parse(raw_msg)

        #Create Order Object
        order = Order(
            order_id=order_id,
            symbol=msg_dict["55"],
            qty=int(msg_dict["38"]),
            side=msg_dict["54"]
        )
        log.log("OrderCreated", {
            "order_id": order.order_id,
            "symbol": order.symbol,
            "qty": order.qty,
            "side": order.side,
            "fix_msg": msg_dict
        })

        # 3. Risk Check
        risk.check(order)

        #Acknowledge
        order.transition(OrderState.ACKED)
        log.log("OrderAcked", {"order_id": order.order_id})

        #Simulate Fill & Update Position
        # For this sim, we assume an ACKed order is immediately FILLED.
        risk.update_position(order)
        order.transition(OrderState.FILLED)
        log.log("OrderFilled", {
            "order_id": order.order_id,
            "symbol": order.symbol,
            "new_position": risk.get_position(order.symbol)
        })

    except ValueError as e:
        # This catches errors from FixParser, Order constructor, or RiskEngine
        rejection_reason = str(e)
        print(f"REJECTED: {rejection_reason}")

        if order:
            # If order was created before rejection, move to REJECTED state
            order.transition(OrderState.REJECTED)
            log.log("OrderRejected", {
                "order_id": order.order_id,
                "reason": rejection_reason
            })
        else:
            # If order creation failed (e.g., bad FIX), log a general rejection
            log.log("MessageRejected", {
                "raw_message": raw_msg,
                "reason": rejection_reason
            })

    except Exception as e:
        # Catch-all for other unexpected errors
        print(f"CRITICAL ERROR: {e}")
        log.log("SystemError", {"error": str(e), "raw_message": raw_msg})

print("\n--- End of Message Stream ---")