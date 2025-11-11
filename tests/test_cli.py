"""CLI integration tests for PyResolvers."""

import json
import os
import subprocess
import tempfile
import unittest


class TestCLI(unittest.TestCase):
    """Test CLI flags and combinations."""

    @classmethod
    def setUpClass(cls):
        """Create test data files."""
        cls.temp_dir = tempfile.mkdtemp()

        # Test servers file
        cls.test_servers_file = os.path.join(cls.temp_dir, "servers.txt")
        with open(cls.test_servers_file, "w") as f:
            f.write("1.1.1.1\n8.8.8.8\n9.9.9.9\n")

        # Exclusion file
        cls.exclude_file = os.path.join(cls.temp_dir, "exclude.txt")
        with open(cls.exclude_file, "w") as f:
            f.write("8.8.8.8\n")

    def run_cli(self, args, timeout=30):
        """Run CLI command and return result."""
        cmd = ["pyresolvers"] + args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return result
        except subprocess.TimeoutExpired:
            self.fail(f"Command timed out: {' '.join(cmd)}")

    def test_single_server(self):
        """Test -t flag with single server."""
        result = self.run_cli(["-t", "1.1.1.1"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("1.1.1.1", result.stdout)
        self.assertIn("Found", result.stdout)

    def test_server_list_from_file(self):
        """Test -tL flag with file input."""
        result = self.run_cli(["-tL", self.test_servers_file])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Testing 3 servers", result.stdout)
        self.assertIn("Found", result.stdout)

    def test_max_speed_filter(self):
        """Test --max-speed filtering."""
        result = self.run_cli(["-tL", self.test_servers_file, "--max-speed", "50"])
        self.assertEqual(result.returncode, 0)
        # Should have fewer or same results due to filtering
        self.assertIn("Found", result.stdout)

    def test_verbose_mode(self):
        """Test -v verbose output."""
        result = self.run_cli(
            ["-tL", self.test_servers_file, "--max-speed", "10", "-v"]
        )
        self.assertEqual(result.returncode, 0)
        # Verbose should show rejected servers
        self.assertTrue(
            "REJECTED" in result.stdout
            or "Too slow" in result.stdout
            or "Found 0" in result.stdout
        )

    def test_silent_mode(self):
        """Test --silent flag (IPs only)."""
        result = self.run_cli(["-tL", self.test_servers_file, "--silent"])
        self.assertEqual(result.returncode, 0)
        # Should not have banner
        self.assertNotIn("pyresolvers v", result.stdout)
        # Should have IP addresses
        lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        # All non-empty lines should look like IPs
        for line in lines:
            parts = line.split(".")
            if len(parts) == 4:  # Looks like an IP
                self.assertTrue(all(p.isdigit() for p in parts))

    def test_json_output_format(self):
        """Test --format json."""
        output_file = os.path.join(self.temp_dir, "output.json")
        result = self.run_cli(
            ["-tL", self.test_servers_file, "--format", "json", "-o", output_file]
        )
        self.assertEqual(result.returncode, 0)

        # Verify JSON file was created and is valid
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, "r") as f:
            data = json.load(f)
            self.assertIn("servers", data)
            self.assertIn("count", data)
            self.assertIn("filters", data)
            self.assertIsInstance(data["servers"], list)

    def test_text_with_speed_format(self):
        """Test --format text-with-speed."""
        output_file = os.path.join(self.temp_dir, "output_speed.txt")
        result = self.run_cli(
            [
                "-tL",
                self.test_servers_file,
                "--format",
                "text-with-speed",
                "-o",
                output_file,
            ]
        )
        self.assertEqual(result.returncode, 0)

        # Verify output file has IP and latency
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, "r") as f:
            content = f.read()
            # Should have format like "1.1.1.1 20.5ms"
            if content.strip():  # If there are results
                self.assertTrue("ms" in content)

    def test_text_output_to_file(self):
        """Test default text output to file."""
        output_file = os.path.join(self.temp_dir, "output_text.txt")
        result = self.run_cli(["-tL", self.test_servers_file, "-o", output_file])
        self.assertEqual(result.returncode, 0)

        # Verify text file has IPs
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, "r") as f:
            content = f.read()
            lines = [l.strip() for l in content.strip().split("\n") if l.strip()]
            # Should have IP addresses
            self.assertGreater(len(lines), 0)

    def test_exclusion_single(self):
        """Test -e flag to exclude single server."""
        result = self.run_cli(["-tL", self.test_servers_file, "-e", "8.8.8.8"])
        self.assertEqual(result.returncode, 0)
        # Should test fewer servers
        self.assertIn("Testing 2 servers", result.stdout)

    def test_exclusion_list(self):
        """Test -eL flag with exclusion file."""
        result = self.run_cli(["-tL", self.test_servers_file, "-eL", self.exclude_file])
        self.assertEqual(result.returncode, 0)
        # Should exclude 8.8.8.8
        self.assertIn("Testing 2 servers", result.stdout)

    def test_threads_parameter(self):
        """Test -threads flag."""
        result = self.run_cli(["-tL", self.test_servers_file, "-threads", "100"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("concurrency=100", result.stdout)

    def test_timeout_parameter(self):
        """Test -timeout flag with float value."""
        result = self.run_cli(["-tL", self.test_servers_file, "-timeout", "0.5"])
        self.assertEqual(result.returncode, 0)
        # Should complete without error

    def test_timeout_parameter_integer(self):
        """Test -timeout flag with integer value."""
        result = self.run_cli(["-tL", self.test_servers_file, "-timeout", "2"])
        self.assertEqual(result.returncode, 0)

    def test_min_speed_filter(self):
        """Test --min-speed filtering."""
        result = self.run_cli(["-tL", self.test_servers_file, "--min-speed", "5"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Found", result.stdout)

    def test_min_max_speed_combination(self):
        """Test both --min-speed and --max-speed together."""
        result = self.run_cli(
            ["-tL", self.test_servers_file, "--min-speed", "10", "--max-speed", "50"]
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Found", result.stdout)

    def test_no_color_flag(self):
        """Test --no-color flag."""
        result = self.run_cli(["-tL", self.test_servers_file, "--no-color"])
        self.assertEqual(result.returncode, 0)
        # Should not contain ANSI color codes
        self.assertNotIn("\033[", result.stdout)

    def test_help_flag(self):
        """Test --help flag."""
        result = self.run_cli(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("High-Performance", result.stdout)
        self.assertIn("Examples:", result.stdout)

    def test_cron_use_case(self):
        """Test typical cron use case: URL input, max-speed filter, silent output."""
        output_file = os.path.join(self.temp_dir, "cron_output.txt")
        # Use local file instead of URL for faster test
        result = self.run_cli(
            [
                "-tL",
                self.test_servers_file,
                "--max-speed",
                "200",
                "--silent",
                "-o",
                output_file,
            ]
        )
        self.assertEqual(result.returncode, 0)

        # Verify output file exists and has IPs
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, "r") as f:
            content = f.read().strip()
            if content:  # If there are results
                lines = content.split("\n")
                # Each line should be an IP
                for line in lines:
                    parts = line.strip().split(".")
                    self.assertEqual(len(parts), 4)

    def test_json_with_filters(self):
        """Test JSON output with speed filters."""
        output_file = os.path.join(self.temp_dir, "filtered.json")
        result = self.run_cli(
            [
                "-tL",
                self.test_servers_file,
                "--format",
                "json",
                "--max-speed",
                "100",
                "-o",
                output_file,
            ]
        )
        self.assertEqual(result.returncode, 0)

        with open(output_file, "r") as f:
            data = json.load(f)
            self.assertEqual(data["filters"]["max_ms"], 100.0)

    def test_verbose_with_output_file(self):
        """Test verbose mode with file output."""
        output_file = os.path.join(self.temp_dir, "verbose_out.txt")
        result = self.run_cli(
            [
                "-tL",
                self.test_servers_file,
                "-v",
                "--max-speed",
                "15",
                "-o",
                output_file,
            ]
        )
        self.assertEqual(result.returncode, 0)
        # Terminal should show verbose output
        self.assertTrue(
            "REJECTED" in result.stdout
            or "Too slow" in result.stdout
            or "ACCEPTED" in result.stdout
        )
        # File should still be created
        self.assertTrue(os.path.exists(output_file))

    @classmethod
    def tearDownClass(cls):
        """Clean up test files."""
        import shutil

        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)


if __name__ == "__main__":
    unittest.main()
