"""
Part 1: FIX Message Parser

This module contains the FixParser class which is responsible for
parsing raw FIX protocol strings into structured dictionaries and
validating the presence of required tags.
"""


class FixParser:
    """
    Parses FIX protocol strings into Python dictionaries.

    The Financial Information eXchange (FIX) protocol is a standard
    for electronic trading. Messages are delimited by the SOH character
    (which we'll represent as '|' for this exercise) and consist of
    tag=value pairs.
    """

    def __init__(self):
        """
        Initializes the parser.
        Defines the set of required tags for a New Order (35=D) message.
        """
        # Tags for a New Order Single (35=D) message
        self.required_tags = {
            '8',  # BeginString (e.g., FIX.4.2)
            '35',  # MsgType (e.g., D for New Order)
            '55',  # Symbol
            '54',  # Side (1=Buy, 2=Sell)
            '38',  # OrderQty
            '40',  # OrdType (e.g., 2=Limit)
            # '44',  # Price (if OrdType=2)
        }

    def parse(self, fix_string: str) -> dict:
        """
        Parses a raw FIX string into a dictionary.

        Args:
            fix_string: A string representing a FIX message,
                        with fields separated by '|'.

        Returns:
            A dictionary where keys are FIX tags (as strings)
            and values are the corresponding message values (as strings).

        Raises:
            ValueError: If a required tag is missing from the message.
        """
        try:
            fields = fix_string.split('|')
            fix_dict = {}
            for field in fields:
                if '=' not in field:
                    continue  # Skip malformed fields, like the last empty one

                parts = field.split('=', 1)
                if len(parts) == 2:
                    tag, value = parts
                    fix_dict[tag] = value

            # We only validate if it's a New Order message
            if fix_dict.get('35') == 'D':
                missing_tags = self.required_tags - fix_dict.keys()
                if missing_tags:
                    raise ValueError(f"Missing required tags: {sorted(list(missing_tags))}")

            # Specific validation for Limit orders (40=2) which require a price (44)
            if fix_dict.get('40') == '2' and '44' not in fix_dict:
                raise ValueError("Missing required tag: 44 (Price) for Limit Order")

            return fix_dict

        except Exception as e:
            # Re-raise parsing or validation errors as a ValueError
            raise ValueError(f"Failed to parse FIX message: {e}")


if __name__ == "__main__":
    # Example usage
    parser = FixParser()

    #Valid Limit Order
    msg1 = "8=FIX.4.2|35=D|55=AAPL|54=1|38=100|40=2|44=150.25|10=128"
    print(f"Parsing: {msg1}")
    try:
        parsed1 = parser.parse(msg1)
        print(f"Parsed: {parsed1}\n")
    except ValueError as e:
        print(f"Error: {e}\n")

    #Valid Market Order (no price needed)
    msg2 = "8=FIX.4.2|35=D|55=GOOG|54=2|38=50|40=1|10=130"
    print(f"Parsing: {msg2}")
    try:
        parsed2 = parser.parse(msg2)
        print(f"Parsed: {parsed2}\n")
    except ValueError as e:
        print(f"Error: {e}\n")

    #Invalid Order (Missing Symbol 55)
    msg3 = "8=FIX.4.2|35=D|54=1|38=100|40=2|44=150.25|10=128"
    print(f"Parsing: {msg3}")
    try:
        parsed3 = parser.parse(msg3)
        print(f"Parsed: {parsed3}\n")
    except ValueError as e:
        print(f"Error: {e}\n")

    #Invalid Limit Order (Missing Price 44)
    msg4 = "8=FIX.4.2|35=D|55=MSFT|54=1|38=200|40=2|10=129"
    print(f"Parsing: {msg4}")
    try:
        parsed4 = parser.parse(msg4)
        print(f"Parsed: {parsed4}\n")
    except ValueError as e:
        print(f"Error: {e}\n")