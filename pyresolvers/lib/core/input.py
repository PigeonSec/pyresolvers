#!/usr/bin/env python3
"""Command-line argument parsing and input handling."""

from __future__ import annotations

import re
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
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
    def check_positive_float(parser, arg):
        """Validate positive float or integer."""
        try:
            value = float(arg)
            if value <= 0:
                parser.error(f"{arg} must be a positive number")
            return value
        except ValueError:
            parser.error(f"{arg} is not a valid number")

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
        parser = ArgumentParser(
            prog='pyresolvers',
            description='High-Performance Async DNS Resolver Validator & Speed Tester',
            epilog='''
Examples:
  pyresolvers -t 1.1.1.1                                    # Test single server
  pyresolvers -tL dns_list.txt --max-speed 50              # Test file, filter <50ms
  pyresolvers -tL url --max-speed 200 -threads 200 -timeout 0.5  # Fast scan
  pyresolvers -tL list.txt -v --max-speed 100              # Verbose with filtering
  pyresolvers -tL list.txt --format json -o results.json  # Export to JSON
  pyresolvers -tL list.txt --silent > fast.txt            # Pipe IPs only

For more info: https://github.com/PigeonSec/pyresolvers
            ''',
            formatter_class=lambda prog: RawDescriptionHelpFormatter(prog, max_help_position=35, width=100)
        )

        # INPUT OPTIONS
        input_group = parser.add_argument_group('Input Options')
        targets = input_group.add_mutually_exclusive_group(required=False)
        targets.add_argument(
            '-t', dest='target',
            metavar='IP',
            help='Test single DNS server (e.g., -t 1.1.1.1)'
        )
        targets.add_argument(
            '-tL', dest='target_list',
            default="https://public-dns.info/nameservers.txt",
            metavar='FILE/URL',
            type=lambda x: InputHelper.process_targets(parser, x),
            help='File or URL with DNS servers (default: public-dns.info list)'
        )

        exclusions = input_group.add_mutually_exclusive_group()
        exclusions.add_argument(
            '-e', dest='exclusion',
            metavar='IP',
            help='Exclude single server (e.g., -e 8.8.8.8)'
        )
        exclusions.add_argument(
            '-eL', dest='exclusions_list',
            metavar='FILE/URL',
            type=lambda x: InputHelper.process_targets(parser, x),
            help='File or URL with servers to exclude'
        )

        # VALIDATION OPTIONS
        valid_group = parser.add_argument_group('Validation Options')
        valid_group.add_argument(
            '-r', dest='rootdomain',
            default="bet365.com",
            metavar='DOMAIN',
            help='Baseline domain for validation (default: bet365.com)'
        )
        valid_group.add_argument(
            '-q', dest='query',
            default="dnsvalidator",
            metavar='PREFIX',
            help='NXDOMAIN test prefix (default: dnsvalidator)'
        )

        # PERFORMANCE OPTIONS
        perf_group = parser.add_argument_group('Performance Options')
        perf_group.add_argument(
            '-threads', dest='threads',
            default=50,
            metavar='N',
            type=lambda x: InputHelper.check_positive(parser, x),
            help='Concurrent workers (default: 50, recommended: 100-200 for speed)'
        )
        perf_group.add_argument(
            '-timeout', dest='timeout',
            default=1,
            metavar='SEC',
            type=lambda x: InputHelper.check_positive_float(parser, x),
            help='DNS timeout in seconds (default: 1, use 0.5 for speed)'
        )

        # FILTERING OPTIONS
        filter_group = parser.add_argument_group('Speed Filtering Options')
        filter_group.add_argument(
            '--max-speed', dest='max_speed',
            type=float,
            metavar='MS',
            help='Only show servers faster than MS milliseconds (e.g., --max-speed 50)'
        )
        filter_group.add_argument(
            '--min-speed', dest='min_speed',
            type=float,
            metavar='MS',
            help='Only show servers slower than MS milliseconds (for filtering out local)'
        )

        # OUTPUT OPTIONS
        output_group = parser.add_argument_group('Output Options')
        output_group.add_argument(
            '-o', '--output',
            metavar='FILE',
            help='Save results to file (format depends on --format flag)'
        )
        output_group.add_argument(
            '--format', dest='output_format',
            default='text',
            choices=['text', 'json', 'text-with-speed'],
            metavar='FMT',
            help='Output format: text (IPs only), json (with latency), text-with-speed (IP + latency)'
        )

        output_types = output_group.add_mutually_exclusive_group()
        output_types.add_argument(
            '-v', '--verbose', dest='verbose',
            action='store_true',
            help='Show rejected servers with reasons (Too slow, Timeout, Invalid, Poisoned)'
        )
        output_types.add_argument(
            '--silent', dest='silent',
            action='store_true',
            help='Only output valid IPs, no banners or progress (great for piping)'
        )

        output_group.add_argument(
            '--no-color', dest='nocolor',
            action='store_true',
            help='Disable colored terminal output'
        )

        return parser
