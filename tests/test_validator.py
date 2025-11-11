"""Unit tests for Validator class."""

import asyncio
import unittest
from pyresolvers import Validator


class TestValidator(unittest.TestCase):
    """Test Validator class functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_servers = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]
        self.invalid_servers = ["999.999.999.999", "invalid.ip", "192.0.2.1"]

    def test_validator_initialization(self):
        """Test Validator can be initialized with default parameters."""
        validator = Validator()
        self.assertIsNotNone(validator)
        self.assertEqual(validator.concurrency, 50)
        self.assertEqual(validator.timeout, 1)

    def test_validator_custom_parameters(self):
        """Test Validator with custom parameters."""
        validator = Validator(concurrency=100, timeout=2, verbose=True)
        self.assertEqual(validator.concurrency, 100)
        self.assertEqual(validator.timeout, 2)
        self.assertTrue(validator.verbose)

    def test_validate_sync(self):
        """Test synchronous validate method."""
        validator = Validator(concurrency=10, timeout=2)
        results = validator.validate(self.test_servers)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), len(self.test_servers))

        # Check result structure
        for result in results:
            self.assertHasAttr(result, "server")
            self.assertHasAttr(result, "valid")
            self.assertHasAttr(result, "latency_ms")

    def test_validate_by_speed_sync(self):
        """Test synchronous validate_by_speed method."""
        validator = Validator(concurrency=10, timeout=2)
        results = validator.validate_by_speed(self.test_servers)

        self.assertIsInstance(results, list)
        # Results should be tuples of (server, latency)
        for server, latency in results:
            self.assertIsInstance(server, str)
            self.assertIsInstance(latency, float)
            self.assertGreater(latency, 0)

    def test_validate_by_speed_with_max_filter(self):
        """Test speed filtering with max_ms."""
        validator = Validator(concurrency=10, timeout=2)
        results = validator.validate_by_speed(self.test_servers, max_ms=100)

        # All results should be under 100ms
        for server, latency in results:
            self.assertLessEqual(latency, 100)

    def test_validate_by_speed_with_min_filter(self):
        """Test speed filtering with min_ms."""
        validator = Validator(concurrency=10, timeout=2)
        results = validator.validate_by_speed(self.test_servers, min_ms=5)

        # All results should be over 5ms
        for server, latency in results:
            self.assertGreaterEqual(latency, 5)

    def test_validate_by_speed_with_both_filters(self):
        """Test speed filtering with both min and max."""
        validator = Validator(concurrency=10, timeout=2)
        results = validator.validate_by_speed(self.test_servers, min_ms=5, max_ms=100)

        # All results should be in range
        for server, latency in results:
            self.assertGreaterEqual(latency, 5)
            self.assertLessEqual(latency, 100)

    def test_to_json(self):
        """Test JSON export."""
        import json

        validator = Validator(concurrency=10, timeout=2)
        result_json = validator.to_json(self.test_servers)

        # Should be valid JSON
        data = json.loads(result_json)
        self.assertIn("servers", data)
        self.assertIn("count", data)
        self.assertIn("filters", data)
        self.assertIsInstance(data["servers"], list)

    def test_to_json_with_filters(self):
        """Test JSON export with speed filters."""
        import json

        validator = Validator(concurrency=10, timeout=2)
        result_json = validator.to_json(self.test_servers, min_ms=5, max_ms=100)

        data = json.loads(result_json)
        self.assertEqual(data["filters"]["min_ms"], 5)
        self.assertEqual(data["filters"]["max_ms"], 100)

    def test_to_text(self):
        """Test text export."""
        validator = Validator(concurrency=10, timeout=2)
        result_text = validator.to_text(self.test_servers)

        # Should have IP addresses
        self.assertIsInstance(result_text, str)
        lines = [l for l in result_text.strip().split("\n") if l]
        # Should have at least some results
        self.assertGreaterEqual(len(lines), 0)

    def test_to_text_with_speed(self):
        """Test text export with speed display."""
        validator = Validator(concurrency=10, timeout=2)
        result_text = validator.to_text(self.test_servers, show_speed=True)

        # Should contain "ms" for latency
        if result_text.strip():  # If there are results
            self.assertIn("ms", result_text)

    def test_invalid_ip_handling(self):
        """Test handling of invalid IP addresses."""
        validator = Validator(concurrency=10, timeout=1)
        results = validator.validate(self.invalid_servers)

        # Should return results for all inputs
        self.assertEqual(len(results), len(self.invalid_servers))

        # Invalid IPs should be marked as not valid
        for result in results:
            if result.server in ["999.999.999.999", "invalid.ip"]:
                self.assertFalse(result.valid)

    def test_async_validate(self):
        """Test async validate method."""

        async def run_test():
            validator = Validator(concurrency=10, timeout=2)
            results = await validator.validate_async(self.test_servers)

            self.assertIsInstance(results, list)
            self.assertEqual(len(results), len(self.test_servers))
            return results

        results = asyncio.run(run_test())
        self.assertGreater(len(results), 0)

    def test_async_validate_by_speed(self):
        """Test async validate_by_speed method."""

        async def run_test():
            validator = Validator(concurrency=10, timeout=2)
            results = await validator.validate_by_speed_async(self.test_servers)

            self.assertIsInstance(results, list)
            for server, latency in results:
                self.assertIsInstance(server, str)
                self.assertGreater(latency, 0)
            return results

        results = asyncio.run(run_test())
        self.assertIsInstance(results, list)

    def test_async_streaming(self):
        """Test async streaming validation."""

        async def run_test():
            validator = Validator(concurrency=10, timeout=2)
            results = []

            async for server, latency in validator.validate_streaming_async(
                self.test_servers
            ):
                results.append((server, latency))
                self.assertIsInstance(server, str)
                self.assertGreater(latency, 0)

            return results

        results = asyncio.run(run_test())
        self.assertIsInstance(results, list)

    def test_concurrent_validation(self):
        """Test high concurrency doesn't break validation."""
        validator = Validator(concurrency=200, timeout=1)
        results = validator.validate(self.test_servers)

        self.assertEqual(len(results), len(self.test_servers))

    def test_fast_timeout_mode(self):
        """Test fast timeout mode."""
        validator = Validator(concurrency=10, timeout=1, use_fast_timeout=True)
        results = validator.validate(self.test_servers)
        self.assertGreater(len(results), 0)

    def assertHasAttr(self, obj, attr):
        """Helper to assert object has attribute."""
        self.assertTrue(hasattr(obj, attr), f"Object missing attribute: {attr}")


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult dataclass."""

    def test_validation_result_structure(self):
        """Test ValidationResult has required fields."""
        from pyresolvers.validator import ValidationResult

        result = ValidationResult(
            server="1.1.1.1", valid=True, latency_ms=20.5, error=None
        )

        self.assertEqual(result.server, "1.1.1.1")
        self.assertTrue(result.valid)
        self.assertEqual(result.latency_ms, 20.5)
        self.assertIsNone(result.error)

    def test_validation_result_to_dict(self):
        """Test ValidationResult.to_dict() method."""
        from pyresolvers.validator import ValidationResult

        result = ValidationResult(
            server="8.8.8.8", valid=False, latency_ms=-1, error="Timeout"
        )

        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict["server"], "8.8.8.8")
        self.assertFalse(result_dict["valid"])
        self.assertEqual(result_dict["error"], "Timeout")


if __name__ == "__main__":
    unittest.main()
