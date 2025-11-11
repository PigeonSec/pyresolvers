#!/usr/bin/env python3
"""PyResolvers CLI."""

from __future__ import annotations

import asyncio
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


async def output_results_async(validator: Validator, targets: List[str], args: Any, out: OutputHelper) -> None:
    """Output validation results."""
    fmt = args.output_format

    if fmt == 'json':
        result = await validator.to_json_async(targets, args.min_speed, args.max_speed)
        count = json.loads(result).get('count', 0)
        out.terminal(Level.INFO, 0, f"Found {count} valid servers")
        if not args.silent:
            print(f"\n{result}")
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)

    elif fmt == 'text-with-speed':
        result = await validator.to_text_async(targets, args.min_speed, args.max_speed, True)
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
        # Use streaming to show ALL results as they complete
        results = []
        tested = 0

        if not await validator._setup_baseline():
            raise RuntimeError("Baseline setup failed")

        semaphore = asyncio.Semaphore(validator.concurrency)

        async def test_and_show(server: str):
            nonlocal tested
            async with semaphore:
                # Fast validation first
                result = await validator._validate_server(server)
                tested += 1

                # Show progress every 100
                if tested % 100 == 0:
                    print(f"[Progress] {tested}/{len(targets)} tested", flush=True)

                # If valid, measure latency quickly
                if result.valid:
                    latency = await validator._measure_latency(server)

                    if latency > 0:
                        # Check speed filter
                        passes_filter = (not args.min_speed or latency >= args.min_speed) and \
                                       (not args.max_speed or latency <= args.max_speed)

                        if passes_filter:
                            if not args.silent:
                                out.terminal(Level.ACCEPTED, server, f"{latency:.2f}ms")
                            else:
                                print(server, flush=True)
                            return (server, latency)
                        elif args.verbose:
                            out.terminal(Level.REJECTED, server, f"Too slow: {latency:.2f}ms")
                elif args.verbose:
                    # Show failures in verbose mode
                    out.terminal(Level.REJECTED, server, result.error or "Invalid")

                return None

        tasks = [test_and_show(server) for server in targets]
        for coro in asyncio.as_completed(tasks):
            result = await coro
            if result:
                results.append(result)

        out.terminal(Level.INFO, 0, f"Found {len(results)} valid servers")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                for server, _ in results:
                    f.write(f"{server}\n")


async def main_async() -> None:
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
        use_fast_timeout=True,  # Enabled for better performance
        verbose=args.verbose
    )

    try:
        out.terminal(Level.INFO, 0, "Establishing baseline...")
        out.terminal(Level.INFO, 0, f"Validating with concurrency={int(args.threads)}...")
        await output_results_async(validator, targets, args, out)
    except RuntimeError as e:
        out.terminal(Level.ERROR, 0, str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        out.terminal(Level.ERROR, 0, "Interrupted")
        sys.exit(130)
    except Exception as e:
        out.terminal(Level.ERROR, 0, f"Error: {str(e)}")
        sys.exit(1)


def main() -> None:
    signal.signal(signal.SIGINT, handle_interrupt)
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
