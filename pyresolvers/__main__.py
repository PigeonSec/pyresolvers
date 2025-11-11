#!/usr/bin/env python3
"""PyResolvers CLI."""

from __future__ import annotations

import json
import os
import signal
import sys
from typing import Any, List

from .lib.core.input import InputHelper, InputParser
from .lib.core.output import Level, OutputHelper
from .validator import Validator


def handle_interrupt(signum: int, frame: Any) -> None:
    os._exit(0)


def output_results(validator: Validator, targets: List[str], args: Any, out: OutputHelper) -> None:
    """Output validation results."""
    fmt = args.output_format

    if fmt == 'json':
        result = validator.to_json(targets, args.min_speed, args.max_speed)
        count = json.loads(result).get('count', 0)
        out.terminal(Level.INFO, 0, f"Found {count} valid servers")
        if not args.silent:
            print(f"\n{result}")
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)

    elif fmt == 'text-with-speed':
        result = validator.to_text(targets, args.min_speed, args.max_speed, True)
        lines = [l for l in result.strip().split('\n') if l]
        out.terminal(Level.INFO, 0, f"Found {len(lines)} valid servers")
        if not args.silent:
            for line in lines:
                if parts := line.split():
                    out.terminal(Level.ACCEPTED, parts[0], parts[1] if len(parts) > 1 else "")
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)

    else:  # text
        results = validator.validate_by_speed(targets, args.min_speed, args.max_speed)
        out.terminal(Level.INFO, 0, f"Found {len(results)} valid servers")

        if results and not args.silent:
            for server, latency in results:
                out.terminal(Level.ACCEPTED, server, f"{latency:.2f}ms")

        if args.output:
            text = validator.to_text(targets, args.min_speed, args.max_speed)
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(text)
        elif args.silent:
            for server, _ in results:
                print(server, flush=True)


def main() -> None:
    signal.signal(signal.SIGINT, handle_interrupt)

    args = InputParser().parse(sys.argv[1:])
    out = OutputHelper(args)
    out.print_banner()

    targets = list(InputHelper.return_targets(args))
    out.terminal(Level.INFO, 0, f"Testing {len(targets)} servers")

    if args.max_speed:
        out.terminal(Level.INFO, 0, f"Max speed filter: {args.max_speed}ms")
    if args.min_speed:
        out.terminal(Level.INFO, 0, f"Min speed filter: {args.min_speed}ms")

    validator = Validator(
        baseline_domain=args.rootdomain,
        query_prefix=args.query,
        concurrency=int(args.threads),
        timeout=int(args.timeout),
        use_fast_timeout=False,  # Disabled for maximum coverage
        verbose=args.verbose
    )

    try:
        out.terminal(Level.INFO, 0, "Establishing baseline...")
        output_results(validator, targets, args, out)
    except RuntimeError as e:
        out.terminal(Level.ERROR, 0, str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        out.terminal(Level.ERROR, 0, "Interrupted")
        sys.exit(130)
    except Exception as e:
        out.terminal(Level.ERROR, 0, f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
