"""
(New File)
FIX Message Generator

This module provides a simple FIX message generator for creating
test New Order (35=D) messages.
It can generate both valid and invalid messages.
"""

import random


class FixMessageGenerator:
    """Class to generate random FIX 35=D order messages."""

    def __init__(self, symbols=None, max_qty=1000):
        """
        Initializes the generator.

        Args:
            symbols (list, optional): List of symbols to trade. Defaults to ['AAPL', 'GOOG', 'MSFT', 'TSLA'].
            max_qty (int, optional): Maximum order quantity for random generation. Defaults to 1000.
        """
        self.symbols = symbols or ['AAPL', 'GOOG', 'MSFT', 'TSLA']
        self.max_qty = max_qty
        self.base_msg_template = {
            '8': 'FIX.4.2',
            '35': 'D',
            '10': random.randint(100, 200)  # Checksum
        }

    def _create_message(self, overrides: dict, required_tags: list) -> str:
        """
        Builds a FIX string from the provided tags.

        Args:
            overrides (dict): Tags to include or override.
            required_tags (list): List of tags that must exist in the final message.

        Returns:
            str: A formatted FIX message string.
        """
        msg_dict = {**self.base_msg_template, **overrides}

        # Ensure all required tags are present
        for tag in required_tags:
            if tag not in msg_dict:
                # This is an intentional omission for testing the parser
                pass

                # Sort by tag number (not required by FIX, but helps readability)
        sorted_tags = sorted(msg_dict.keys(), key=int)

        fields = [f"{tag}={msg_dict[tag]}" for tag in sorted_tags if tag in msg_dict]
        return "|".join(fields)

    def create_valid_message(self) -> str:
        """
        Generates a structurally valid FIX order message.
        It can be a Market (40=1) or Limit (40=2) order.
        """
        symbol = random.choice(self.symbols)
        side = random.choice(['1', '2'])  # 1=Buy, 2=Sell
        qty = random.randint(1, self.max_qty)
        ord_type = random.choice(['1', '2'])  # 1=Market, 2=Limit

        tags = {
            '55': symbol,
            '54': side,
            '38': qty,
            '40': ord_type
        }

        required = ['8', '35', '55', '54', '38', '40', '10']

        if ord_type == '2':  # Limit order needs a price
            price = round(random.uniform(100.0, 500.0), 2)
            tags['44'] = price
            required.append('44')

        return self._create_message(tags, required)

    def create_invalid_message(self) -> str:
        """
        Generates an intentionally invalid FIX message for testing.
        May be missing tags or have invalid values.
        """
        choice = random.choice(['missing_symbol', 'missing_side', 'zero_qty', 'missing_price_limit'])

        tags = {
            '55': random.choice(self.symbols),
            '54': random.choice(['1', '2']),
            '38': random.randint(1, self.max_qty),
            '40': '1'  # Default to Market order
        }
        required = ['8', '35', '55', '54', '38', '40', '10']

        if choice == 'missing_symbol':
            tags.pop('55', None)
            required.remove('55')  # Simulate a missing tag

        elif choice == 'missing_side':
            tags.pop('54', None)
            required.remove('54')

        elif choice == 'zero_qty':
            tags['38'] = 0  # This will fail in the Order constructor

        elif choice == 'missing_price_limit':
            tags['40'] = '2'  # Limit order
            # But we intentionally do not add '44' (Price)
            required.append('44')  # The parser should catch that '44' is missing

        return self._create_message(tags, required)


if __name__ == "__main__":
    generator = FixMessageGenerator()

    print("--- 5 Valid Random Messages ---")
    for _ in range(5):
        print(generator.create_valid_message())

    print("\n--- 3 Invalid Random Messages ---")
    for _ in range(3):
        print(generator.create_invalid_message())