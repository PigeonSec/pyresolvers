# Changelog

All notable changes to PyResolvers will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.2] - 2025-01-11

### Fixed
- Fixed latency measurement to measure only the baseline DNS query time
- Previously measured all validation checks together, now accurately reports raw DNS query latency
- Latency is now measured during validation instead of as a separate query

## [2.4.1] - 2025-01-11

### Added
- Added `--version` and `-V` flags to display installed version

## [2.4.0] - 2025-01-11

### Changed
- **BREAKING**: Replaced aiodns/pycares with dnspython for DNS resolution
- Completely eliminates inotify watch exhaustion issues on Linux systems
- No more "Failed to initialize c-ares channel" errors
- Resolvers now scale to process 65k+ servers without resource limits

### Fixed
- Fixed functionality breaking when processing large resolver lists
- Resolved incomplete validation results (was only getting ~350/65k resolvers)
- Eliminated system resource exhaustion during large batch processing

## [2.3.1] - 2025-01-11

### Fixed
- Fixed inotify watch exhaustion when processing large resolver lists (65k+)
- Implemented DNS resolver instance caching to prevent resource exhaustion
- Resolvers are now reused per unique server, reducing system resource usage
- Eliminated "Failed to initialize c-ares channel" errors on large batches

## [1.1.0] - 2025-01-11

### Added
- Enhanced URL input parsing with smart IP extraction
- CSV and TSV format support (comma/tab separated)
- Mixed format support (extracts IPs from any text format)
- Comment support in input files (lines starting with #)
- Improved IP validation (validates octets are 0-255)
- Better error messages for URL fetch failures
- Input format documentation in README
- Comprehensive examples for all input formats

### Changed
- File and URL processing now use unified IP extraction logic
- More robust parsing handles edge cases better

### Fixed
- IP extraction from complex formats (e.g., "Server: 8.8.8.8 (Provider)")
- Handling of empty lines and whitespace

## [1.0.0] - 2025-01-10

### Added
- Initial release
- Async DNS resolver validation
- Speed testing and latency measurement
- Multiple output formats (text, JSON, text-with-speed)
- Speed filtering (--min-speed, --max-speed)
- CLI and Python library interfaces
- URL and file input support
- Exclusion lists (servers to skip)
- Concurrent validation with configurable threads
- Comprehensive validation (baseline, poisoning, NXDOMAIN)
- Python 3.8-3.14 support
- GitHub Actions CI/CD
- PyPI publishing automation

[1.1.0]: https://github.com/PigeonSec/pyresolvers/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/PigeonSec/pyresolvers/releases/tag/v1.0.0
