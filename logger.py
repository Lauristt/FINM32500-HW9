"""
Part 4: Event Logger

This module provides a singleton Logger class to record all
system events (order creation, state changes, risk events)
to a JSON file.
"""

from datetime import datetime
import json
import atexit


class Logger:
    """
    A singleton logger that records events and saves them to a JSON file.

    The singleton pattern ensures all parts of the system
    use the same logging instance.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Implements the singleton pattern."""
        if not cls._instance:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self, path="events.json"):
        """
        Initializes the logger. This check ensures the constructor logic
        runs only once when the singleton instance is first created.

        Args:
            path: The file path to save the JSON log to.
        """
        # This flag prevents re-initialization every time Logger() is called
        if not hasattr(self, 'initialized'):
            self.path = path
            self.events = []
            self.initialized = True
            # Register save() to be called at program exit
            atexit.register(self.save)
            print(f"Logger initialized. Logging to {self.path}")

    def log(self, event_type: str, data: dict):
        """
        Logs a new event.

        Args:
            event_type: A string describing the event (e.g., "OrderCreated").
            data: A dictionary containing event-specific data.
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "data": data
        }
        self.events.append(log_entry)
        print(f"[LOG] {event_type} -> {data}")

    def save(self):
        """
        Saves all logged events to the specified JSON file.
        This is called automatically at exit.
        """
        try:
            with open(self.path, 'w') as f:
                json.dump(self.events, f, indent=4)
            print(f"\n[Logger] Saved {len(self.events)} events to {self.path}")
        except IOError as e:
            print(f"\n[Logger] CRITICAL: Failed to save log file: {e}")

    def clear(self):
        """Utility method (mostly for testing) to clear events."""
        self.events = []
        print("[Logger] Log cleared.")


if __name__ == "__main__":
    # Example usage

    # Get logger instance (will be created on first call)
    log1 = Logger("test_log.json")

    # Get logger instance again (will return the *same* instance)
    log2 = Logger()

    print(f"log1 is log2: {log1 is log2}")  # Demonstrates singleton

    log1.log("SystemStart", {"user": "test_user"})
    log1.log("OrderCreated", {"id": "C001", "symbol": "IBM"})

    log2.log("OrderAcked", {"id": "C001"})
    log2.log("OrderFilled", {"id": "C001", "fill_qty": 100})

    # The log.save() method will be called automatically when the script exits.
    # You can also call it manually if needed:
    # log1.save()

    print("\nScript finished. Logger will save automatically.")