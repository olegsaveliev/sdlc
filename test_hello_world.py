import unittest
from hello_world import say_hello

class TestHelloWorld(unittest.TestCase):
    def test_say_hello_returns_string(self):
        """Test that say_hello returns a string."""
        result = say_hello()
        self.assertIsInstance(result, str)

    def test_say_hello_returns_correct_message(self):
        """Test that say_hello returns the correct message."""
        result = say_hello()
        self.assertEqual(result, "Hello World")

    def test_say_hello_not_empty(self):
        """Test that say_hello doesn't return an empty string."""
        result = say_hello()
        self.assertTrue(len(result) > 0)

if __name__ == "__main__":
    unittest.main()
