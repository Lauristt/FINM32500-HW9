"""
Unit Tests for the Mini Trading System.

This test suite covers all components:
- FixParser
- Order
- RiskEngine
- Logger

Run with: python -m unittest test_trading_system.py
"""

import unittest
import os
import json
from io import StringIO
import sys
from collections import defaultdict

# Import all components
from fix_parser import FixParser
from order import Order, OrderState
from risk_engine import RiskEngine
from logger import Logger


class TestFixParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.parser = FixParser()

    def test_parse_valid_limit_order(self):
        msg = "8=FIX.4.2|35=D|55=AAPL|54=1|38=100|40=2|44=150.25|10=128"
        parsed = self.parser.parse(msg)
        self.assertEqual(parsed['8'], 'FIX.4.2')
        self.assertEqual(parsed['55'], 'AAPL')
        self.assertEqual(parsed['38'], '100')
        self.assertEqual(parsed['44'], '150.25')

    def test_parse_valid_market_order(self):
        msg = "8=FIX.4.2|35=D|55=GOOG|54=2|38=50|40=1|10=130"
        parsed = self.parser.parse(msg)
        self.assertEqual(parsed['55'], 'GOOG')
        self.assertEqual(parsed['40'], '1')
        self.assertNotIn('44', parsed)  # No price for market order

    def test_parse_missing_required_tag(self):
        # Missing 55 (Symbol)
        msg = "8=FIX.4.2|35=D|54=1|38=100|40=2|44=150.25|10=128"
        with self.assertRaisesRegex(ValueError, "Missing required tags:.*'55'"):
            self.parser.parse(msg)

    def test_parse_missing_price_for_limit_order(self):
        # 40=2 (Limit) but missing 44 (Price)
        msg = "8=FIX.4.2|35=D|55=MSFT|54=1|38=200|40=2|10=129"
        with self.assertRaisesRegex(ValueError, "Missing required tag: 44"):
            self.parser.parse(msg)

    def test_parse_non_order_message(self):
        # 35=8 (Execution Report) - should parse without validation error
        msg = "8=FIX.4.2|35=8|55=AAPL|38=100|150=F|10=130"
        parsed = self.parser.parse(msg)
        self.assertEqual(parsed['35'], '8')
        self.assertEqual(parsed['150'], 'F')


class TestOrder(unittest.TestCase):

    def setUp(self):
        # Redirect stderr to capture invalid transition messages
        self.held_stderr = sys.stderr
        sys.stderr = StringIO()

    def tearDown(self):
        sys.stderr.close()
        sys.stderr = self.held_stderr  # Restore stderr

    def test_order_creation_valid(self):
        order = Order("A001", "AAPL", 100, '1')
        self.assertEqual(order.order_id, "A001")
        self.assertEqual(order.symbol, "AAPL")
        self.assertEqual(order.qty, 100)
        self.assertEqual(order.side, '1')
        self.assertEqual(order.state, OrderState.NEW)

    def test_order_creation_invalid_qty(self):
        with self.assertRaises(ValueError):
            Order("A002", "MSFT", 0, '1')
        with self.assertRaises(ValueError):
            Order("A003", "GOOG", -50, '2')
        with self.assertRaises(ValueError):
            Order("A004", "TSLA", "100", '1')  # Qty not int

    def test_order_creation_invalid_side(self):
        with self.assertRaises(ValueError):
            Order("A005", "IBM", 100, '3')
        with self.assertRaises(ValueError):
            Order("A006", "NVDA", 100, 'BUY')

    def test_valid_transitions(self):
        order = Order("B001", "AAPL", 100, '1')
        self.assertEqual(order.state, OrderState.NEW)

        order.transition(OrderState.ACKED)
        self.assertEqual(order.state, OrderState.ACKED)

        order.transition(OrderState.FILLED)
        self.assertEqual(order.state, OrderState.FILLED)

    def test_valid_rejection_flow(self):
        order = Order("B002", "AAPL", 100, '1')
        self.assertEqual(order.state, OrderState.NEW)
        order.transition(OrderState.REJECTED)
        self.assertEqual(order.state, OrderState.REJECTED)

    def test_invalid_transition_new_to_filled(self):
        order = Order("C001", "MSFT", 50, '2')
        order.transition(OrderState.FILLED)
        # State should not change
        self.assertEqual(order.state, OrderState.NEW)
        # Check that an error was printed to stderr
        self.assertIn("INVALID TRANSITION", sys.stderr.getvalue())

    def test_invalid_transition_filled_to_acked(self):
        order = Order("C002", "GOOG", 10, '1')
        order.transition(OrderState.ACKED)
        order.transition(OrderState.FILLED)
        self.assertEqual(order.state, OrderState.FILLED)

        # Clear stderr buffer
        sys.stderr = StringIO()

        order.transition(OrderState.ACKED)  # Attempt invalid move
        self.assertEqual(order.state, OrderState.FILLED)  # State unchanged
        self.assertIn("INVALID TRANSITION", sys.stderr.getvalue())


class TestRiskEngine(unittest.TestCase):

    def setUp(self):
        # Create a fresh risk engine for each test
        self.risk = RiskEngine(max_order_size=100, max_position=200)

    def test_check_valid_order_empty_positions(self):
        order = Order("R001", "AAPL", 50, '1')
        self.assertTrue(self.risk.check(order))

    def test_check_order_size_exceeded(self):
        order = Order("R002", "MSFT", 101, '1')  # 101 > 100 limit
        with self.assertRaisesRegex(ValueError, "Order size 101 exceeds limit 100"):
            self.risk.check(order)

    def test_check_position_limit_exceeded_buy(self):
        # Pre-load position
        self.risk.positions['GOOG'] = 180

        order = Order("R003", "GOOG", 30, '1')  # 180 + 30 = 210 > 200 limit
        with self.assertRaisesRegex(ValueError, "New position 210 for GOOG exceeds limit 200"):
            self.risk.check(order)

    def test_check_position_limit_exceeded_sell(self):
        # Pre-load position
        self.risk.positions['TSLA'] = -180

        order = Order("R004", "TSLA", 30, '2')  # -180 - 30 = -210. abs(-210) > 200 limit
        with self.assertRaisesRegex(ValueError, "New position -210 for TSLA exceeds limit 200"):
            self.risk.check(order)

    def test_check_order_at_limit(self):
        order = Order("R005", "IBM", 100, '1')  # At size limit
        self.assertTrue(self.risk.check(order))

        self.risk.update_position(order)  # Pos = 100

        order2 = Order("R006", "IBM", 100, '1')  # Pos = 100 + 100 = 200 (at pos limit)
        self.assertTrue(self.risk.check(order2))

    def test_update_position(self):
        self.assertEqual(self.risk.get_position('NVDA'), 0)

        # Buy order
        buy_order = Order("R007", "NVDA", 75, '1')
        self.risk.update_position(buy_order)
        self.assertEqual(self.risk.get_position('NVDA'), 75)

        # Another buy order
        buy_order_2 = Order("R008", "NVDA", 25, '1')
        self.risk.update_position(buy_order_2)
        self.assertEqual(self.risk.get_position('NVDA'), 100)

        # Sell order
        sell_order = Order("R009", "NVDA", 40, '2')
        self.risk.update_position(sell_order)
        self.assertEqual(self.risk.get_position('NVDA'), 60)


class TestLogger(unittest.TestCase):
    LOG_FILE = "test_events.json"

    def setUp(self):
        # Reset the singleton instance to ensure isolation
        Logger._instance = None
        self.logger = Logger(self.LOG_FILE)
        self.logger.clear()

        # Suppress print output during tests
        self.held_stdout = sys.stdout
        sys.stdout = StringIO()

    def tearDown(self):
        sys.stdout.close()
        sys.stdout = self.held_stdout  # Restore stdout

        # Clean up the log file
        if os.path.exists(self.LOG_FILE):
            os.remove(self.LOG_FILE)

    def test_singleton_instance(self):
        logger2 = Logger()
        self.assertIs(self.logger, logger2)

    def test_log_event(self):
        self.assertEqual(len(self.logger.events), 0)
        self.logger.log("TestEvent", {"data": 123})
        self.assertEqual(len(self.logger.events), 1)
        self.assertEqual(self.logger.events[0]['event'], 'TestEvent')
        self.assertEqual(self.logger.events[0]['data']['data'], 123)
        self.assertIn('timestamp', self.logger.events[0])

    def test_save_log(self):
        self.logger.log("EventA", {"id": 1})
        self.logger.log("EventB", {"id": 2})

        # Manually save
        self.logger.save()

        self.assertTrue(os.path.exists(self.LOG_FILE))

        with open(self.LOG_FILE, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]['event'], 'EventA')
            self.assertEqual(data[1]['data']['id'], 2)


if __name__ == "__main__":
    unittest.main()