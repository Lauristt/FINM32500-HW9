# Assignment 9: Mini Trading System
*FINM 32500 – University of Chicago*  
*Author: Yuting Li, Xiangchen Liu, Simon Guo, Rajdeep Choudhury*

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green)
![Build Passing](https://img.shields.io/badge/build-passing-brightgreen)

This project implements a simplified **FIX (Financial Information eXchange) protocol workflow**, including:

- A **FIX message generator**
- A **FIX message parser**
- Order object modeling
- A configurable **risk engine**
- A full **end-to-end testing pipeline** validating FIX message correctness and order processing logic

It mirrors real-world sell-side/buy-side integration where trading systems exchange normalized FIX messages for order routing, risk checks, logging, and compliance.

---

## Overview

FIX is the industry-standard protocol used by exchanges, brokers, OMS, and HFT systems to transmit orders and market events.  
This assignment implements core FIX functionality:

### ✔ FIX Message Generator  
- Constructs standardized FIX messages  
- Ensures tag ordering, delimiter formatting, field validation  
- Computes checksum and ensures message integrity  
- Supports message types such as `D` (New Order – Single)

### ✔ FIX Message Parser  
- Parses raw FIX strings into structured Python dictionaries  
- Validates tags, body length, checksum  
- Supports custom field extraction  
- Handles malformed messages gracefully

### ✔ Order Modeling  
- `Order` class represents order state  
- Supports attributes such as `symbol`, `side`, `quantity`, `price`, and FIX routing metadata  
- Integrated with FIX generator to ensure consistent serialization

### ✔ Risk Engine  
- Performs basic pre-trade checks including:  
  - Max quantity limits  
  - Price band validation  
  - Notional limit  
- Can be extended to support real OMS-style compliance layers

### ✔ Test Suite  
- Validates FIX generator correctness  
- Verifies parser accuracy and error handling  
- Unit tests cover order creation, FIX round-trip encoding, and risk-engine rejection logic

---

## Architecture

```
+-------------------+          +-------------------+          +-------------------+
|  FIX Generator    |  -->     |   Risk Engine     |  -->     |   FIX Parser      |
| (encode orders)   |          | (pre-trade checks)|          | (decode messages) |
+-------------------+          +-------------------+          +-------------------+
              ^---------------------------------------------------------------+
                        Full order round-trip validation through test suite
```

Each component is modular and can be plugged into a larger OMS, gateway, or matching engine.

---

## Implementation Highlights

### 1. FIX Message Formatting  
Message fields adhere to the FIX 4.2 structural convention:

```
8=FIX.4.2 | 35=D | 55=AAPL | 54=1 | 38=100 | 44=185.00 | 10=***
```

Where:
- **8** – BeginString  
- **35** – MessageType  
- **55** – Symbol  
- **54** – Side  
- **38** – Quantity  
- **44** – Price  
- **10** – Checksum  

Checksum is auto-computed mod 256.

### 2. Parser Design  
- Splits message by FIX delimiter `|`  
- Converts each tag into dictionary pairs  
- Validates required fields  
- Verifies checksum correctness  
- Throws structured exceptions for malformed FIX input

### 3. Risk Engine Logic  
Configurable validation rules:

| Check | Description |
|-------|-------------|
| Max Quantity | Rejects orders exceeding allowed size |
| Price Bands | Ensures prices fall into an allowable range |
| Notional Limit | Protects against excessive exposure |

All violations return descriptive errors.

---

## File Structure

```
fix_message_generator.py   # FIX encoder implementation
fix_parser.py              # FIX message parser + validations
order.py                   # Order class and representation
risk_engine.py             # Pre-trade risk checks
logger.py                  # Simple logging abstraction
main.py                    # Example workflow entrypoint
test_trading_system.py     # Unit tests for end-to-end FIX handling
.github/workflows/         # Optional CI configuration
requirements.txt
```

---

## Testing and Validation

### Unit Test Coverage
The test suite verifies:

- FIX message construction & checksum correctness  
- Parser correctness under clean and corrupted inputs  
- Order creation and FIX ↔ Order round-trip consistency  
- Risk engine behaviors (pass, reject, correct diagnostics)

Example validated workflow:

1. Create an `Order`  
2. Encode it using the FIX generator  
3. Parse back the encoded string  
4. Compare output fields with original order  
5. Apply risk checks  
6. Verify system behavior

---

## Example Workflow

```python
from fix_message_generator import FIXMessageGenerator
from fix_parser import FIXParser
from order import Order
from risk_engine import RiskEngine

order = Order(symbol="AAPL", side="BUY", quantity=100, price=185.50)
generator = FIXMessageGenerator()
risk = RiskEngine()

msg = generator.generate(order)
risk.validate(order)

parsed = FIXParser.parse(msg)
print(parsed)
```

---

## Notes on FIX Protocol (for context)

- Widely used by BlackRock Aladdin, Bloomberg TOMS, Citadel, Jane Street, and exchanges  
- Designed for deterministic, low-latency text-based communication  
- Ensures strict field ordering, body length, and checksums  
- Industry standard for order routing, trade confirmations, and market-data snapshots  

Your implementation captures **core structural logic** used in real OMS workflows.

---


## License

This project is protected under the MIT LICENSE. For more details, refer to the LICENSE file.


##  Acknowledgments

This project was created as part of the FINM 32500 course at The University of Chicago. Inspiration from various open-source backtesting frameworks.

**Copyright © 2025 Lauristt**