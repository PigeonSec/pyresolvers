"""Output formatting and terminal display."""

from __future__ import annotations

from enum import IntEnum
from time import localtime, strftime
from typing import Any, Union

from colorclass import Color, disable_all_colors

from pyresolvers.lib.core.__version__ import __version__


class Level(IntEnum):
    """Log level enumeration."""
    VERBOSE, INFO, ACCEPTED, REJECTED, ERROR = range(5)


class OutputHelper:
    """Formatted terminal output handler."""

    _FORMATS = {
        Level.VERBOSE: '{autoblue}[VERBOSE]{/autoblue}',
        Level.INFO: '{autoyellow}[INFO]{/autoyellow}',
        Level.ACCEPTED: '{autogreen}[ACCEPTED]{/autogreen}',
        Level.REJECTED: '{autored}[REJECTED]{/autored}',
        Level.ERROR: '{autobgyellow}{autored}[ERROR]{/autored}{/autobgyellow}'
    }
    _SEP = "=" * 55

    def __init__(self, arguments: Any) -> None:
        self.nocolor = getattr(arguments, 'nocolor', False)
        if self.nocolor:
            disable_all_colors()
        self.verbose = getattr(arguments, 'verbose', False)
        self.silent = getattr(arguments, 'silent', False)
        self.output = getattr(arguments, 'output', None)

    def print_banner(self) -> None:
        """Print application banner."""
        if not self.silent:
            print(f"{self._SEP}\npyresolvers v{__version__} - DNS Resolver Validator\n{self._SEP}", flush=True)

    def terminal(self, level: Level, target: Union[str, int], message: str = "") -> None:
        """Print formatted message."""
        if level == Level.VERBOSE and not self.verbose:
            return

        if self.silent:
            if level == Level.ACCEPTED:
                print(target, flush=True)
            return

        leader_fmt = self._FORMATS.get(level, '[#]')
        if self.nocolor:
            # Extract just the label text (e.g., "[INFO]") without color codes
            if leader_fmt != '[#]':
                leader = '[' + leader_fmt.split('[')[1].split(']')[0] + ']'
            else:
                leader = '[#]'
        else:
            leader = Color(leader_fmt)

        time_str = strftime("%H:%M:%S", localtime())

        if target == 0 or target == "0":
            print(f'[{time_str}] {leader} {message}', flush=True)
        else:
            print(f'[{time_str}] {leader} [{target}] {message}', flush=True)

        if self.output and level == Level.ACCEPTED:
            try:
                with open(self.output, 'a', encoding='utf-8') as f:
                    f.write(f"{target}\n")
            except IOError:
                pass
