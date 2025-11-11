#!/usr/bin/env python3
"""Command-line argument parsing and input handling."""

from __future__ import annotations

import re
import sys
from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.error import URLError, HTTPError


class InputHelper:
    """Helper for processing input targets."""

    @staticmethod
    def process_targets(parser, arg):
        """Process targets from URL or file."""
        if InputHelper.validate_url(arg):
            targets = InputHelper.process_url(parser, arg)
        else:
            filename = InputHelper.validate_filename(parser, arg)
            if filename:
                targets = InputHelper.process_file(filename)

        if not targets:
            raise ValueError("No targets provided or empty list")
        return targets

    @staticmethod
    def validate_url(string):
        """Check if string is a valid URL."""
        try:
            result = urlparse(string)
            return bool(result.scheme)
        except Exception:
            return False

    @staticmethod
    def validate_filename(parser, arg):
        """Validate and resolve file path."""
        try:
            path = Path(arg).expanduser().resolve()
            if not path.is_file():
                parser.error(f"File {arg} does not exist or is not a valid URL")
            return str(path)
        except Exception as e:
            parser.error(f"Invalid file path: {e}")

    @staticmethod
    def process_url(parser, url):
        """Fetch targets from URL and validate IP addresses."""
        try:
            with urlopen(url, timeout=30) as response:
                if response.status != 200:
                    parser.error(f"HTTP {response.status} from {url}")
                content = response.read().decode('utf-8')
                lines = content.splitlines()

                # Filter and validate IP addresses
                ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
                targets = []

                for line in lines:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    # Extract IP if line contains other data (e.g., CSV format)
                    parts = re.split(r'[,\s\t]+', line)
                    for part in parts:
                        if ip_pattern.match(part):
                            # Basic validation: octets should be 0-255
                            octets = [int(x) for x in part.split('.')]
                            if all(0 <= octet <= 255 for octet in octets):
                                targets.append(part)
                                break  # Only take first valid IP per line

                if not targets:
                    parser.error(f"No valid IP addresses found in {url}")

                return targets
        except HTTPError as e:
            parser.error(f"HTTP {e.code} from {url}")
        except URLError as e:
            parser.error(f"Failed to fetch {url}: {e.reason}")
        except Exception as e:
            parser.error(f"Error fetching {url}: {e}")

    @staticmethod
    def process_file(path):
        """Load targets from file and validate IP addresses."""
        ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        targets = []

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Extract IP if line contains other data
                parts = re.split(r'[,\s\t]+', line)
                for part in parts:
                    if ip_pattern.match(part):
                        # Basic validation: octets should be 0-255
                        octets = [int(x) for x in part.split('.')]
                        if all(0 <= octet <= 255 for octet in octets):
                            targets.append(part)
                            break  # Only take first valid IP per line

        return targets

    @staticmethod
    def check_positive(parser, arg):
        """Validate positive integer."""
        try:
            value = int(arg)
            if value <= 0:
                parser.error(f"{arg} must be a positive integer")
            return arg
        except ValueError:
            parser.error(f"{arg} is not a valid integer")

    @staticmethod
    def return_targets(arguments):
        """Return final target list with exclusions applied."""
        targets = set()
        exclusions = set()

        if arguments.target:
            targets.add(arguments.target)
        else:
            targets.update(arguments.target_list)

        if arguments.exclusion:
            exclusions.add(arguments.exclusion)
        elif arguments.exclusions_list:
            exclusions.update(arguments.exclusions_list)

        targets -= exclusions

        if not targets:
            raise ValueError("No targets remaining after exclusions")
        return targets


class InputParser:
    """Command-line argument parser."""

    def __init__(self):
        self._parser = self.setup_parser()

    def parse(self, argv):
        """Parse command-line arguments."""
        return self._parser.parse_args(argv)

    @staticmethod
    def setup_parser():
        """Setup argument parser."""
        parser = ArgumentParser(description='DNS Resolver Validator with Speed Testing')

        targets = parser.add_mutually_exclusive_group(required=False)
        targets.add_argument('-t', dest='target', help='Target DNS server IP')
        targets.add_argument(
            '-tL', dest='target_list',
            default="https://public-dns.info/nameservers.txt",
            type=lambda x: InputHelper.process_targets(parser, x),
            help='File or URL with DNS server IPs (default: public-dns.info)'
        )

        exclusions = parser.add_mutually_exclusive_group()
        exclusions.add_argument('-e', dest='exclusion', help='Exclude specific server')
        exclusions.add_argument(
            '-eL', dest='exclusions_list',
            type=lambda x: InputHelper.process_targets(parser, x),
            help='File or URL with servers to exclude'
        )

        parser.add_argument('-o', '--output', help='Output file for results')
        parser.add_argument('-r', dest='rootdomain', default="bet365.com",
                          help='Root domain for testing (default: bet365.com)')
        parser.add_argument('-q', dest='query', default="dnsvalidator",
                          help='Query prefix for NXDOMAIN testing')
        parser.add_argument('-threads', dest='threads', default=5,
                          type=lambda x: InputHelper.check_positive(parser, x),
                          help='Max concurrent threads (default: 5)')
        parser.add_argument('-timeout', dest='timeout', default=600,
                          type=lambda x: InputHelper.check_positive(parser, x),
                          help='Timeout in seconds (default: 600)')
        parser.add_argument('--no-color', dest='nocolor', action='store_true',
                          help='Disable colored output')

        output_types = parser.add_mutually_exclusive_group()
        output_types.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                                help='Enable verbose output')
        output_types.add_argument('--silent', dest='silent', action='store_true',
                                help='Only output valid server IPs')

        parser.add_argument('--format', dest='output_format', default='text',
                          choices=['text', 'json', 'text-with-speed'],
                          help='Output format (default: text)')
        parser.add_argument('--max-speed', dest='max_speed', type=float,
                          help='Max response time in ms (filter slower servers)')
        parser.add_argument('--min-speed', dest='min_speed', type=float,
                          help='Min response time in ms (filter faster servers)')

        return parser
