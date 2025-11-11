<div align="center">

<img src="logo.png" alt="PyResolvers Logo" width="200" height="200">

# PyResolvers

**High-Performance Async DNS Resolver Validation & Speed Testing**

[![Tests](https://github.com/PigeonSec/pyresolvers/actions/workflows/test.yml/badge.svg)](https://github.com/PigeonSec/pyresolvers/actions/workflows/test.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![PyPI version](https://img.shields.io/pypi/v/pyresolvers.svg)](https://pypi.org/project/pyresolvers/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

*Validate DNS resolvers, measure response times, identify the fastest servers*

</div>

---

## Overview

PyResolvers is a high-performance async Python library and CLI tool for validating DNS resolvers. It performs comprehensive validation (baseline comparison, poisoning detection, NXDOMAIN verification) and orders results by speed.

### Features

- ⚡ **High-Performance Async** - 2-3x faster than thread-based validators
- 🚀 **Speed Testing** - Measures and orders resolvers by latency
- 🌐 **URL Support** - Download resolver lists from URLs (HTTP/HTTPS)
- 🔍 **Comprehensive Validation** - Multiple validation layers
- 🛡️ **Poisoning Detection** - Identifies DNS hijacking
- 📊 **Multiple Formats** - JSON, plain text, text+speed
- 🎯 **Speed Filtering** - Filter by min/max latency thresholds
- 📝 **Smart Parsing** - Auto-extracts IPs from CSV, text, and mixed formats

### Performance

| Method | Time (5 servers) | Improvement |
|--------|------------------|-------------|
| Original (unoptimized) | 5.36s | baseline |
| **PyResolvers** | **2.32s** | **56.7% faster** ⚡ |
| Speedup | | **2.31x** |

---

## Installation

```bash
git clone https://github.com/PigeonSec/pyresolvers.git
cd pyresolvers
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

**Or install from PyPI:**

```bash
pip install pyresolvers
```

**Requirements**: Python 3.8+, aiodns, pycares, colorclass

---

## Quick Start

### Command Line

```bash
# Test single resolver
pyresolvers -t 1.1.1.1

# Test from URL (public DNS list)
pyresolvers -tL https://public-dns.info/nameservers.txt --max-speed 50

# Test from file
pyresolvers -tL dns_servers.txt

# Get fastest resolvers (< 50ms) and save
pyresolvers -tL https://public-dns.info/nameservers.txt --max-speed 50 -o fast_dns.txt

# Export as JSON with speed data
pyresolvers -tL resolvers.txt --format json --max-speed 100 -o valid_dns.json
```

### Python Library

```python
from pyresolvers import Validator

# Basic usage
validator = Validator()
servers = ['1.1.1.1', '8.8.8.8', '9.9.9.9']
results = validator.validate_by_speed(servers)

for server, latency in results:
    print(f"{server}: {latency:.2f}ms")
```

```python
# High concurrency for large lists
validator = Validator(concurrency=100)
results = validator.validate_by_speed(large_server_list, max_ms=100)
```

```python
# Async usage
import asyncio

async def main():
    validator = Validator(concurrency=200)
    results = await validator.validate_by_speed_async(servers)
    return results

results = asyncio.run(main())
```

---

## Examples

### CLI Usage

```bash
# Use public DNS list from URL
pyresolvers -tL https://public-dns.info/nameservers.txt --max-speed 50

# Speed filtering (10ms-100ms range)
pyresolvers -tL resolvers.txt --min-speed 10 --max-speed 100

# Silent mode (IPs only) - great for piping
pyresolvers -tL https://public-dns.info/nameservers.txt --silent --max-speed 30 > fast.txt

# Exclude specific servers
pyresolvers -tL all_resolvers.txt -e 8.8.8.8

# Exclude servers from URL
pyresolvers -tL https://public-dns.info/nameservers.txt -eL blacklist.txt

# High performance (100 concurrent)
pyresolvers -tL large_list.txt -threads 100

# Get top 10 fastest worldwide resolvers
pyresolvers -tL https://public-dns.info/nameservers.txt -threads 200 --max-speed 30 --format text-with-speed | head -10
```

### Library Usage

**Filter by Speed:**
```python
validator = Validator(concurrency=50)
fast = validator.validate_by_speed(servers, max_ms=50)
```

**Detailed Results:**
```python
results = validator.validate(servers)
for r in results:
    if r.valid:
        print(f"✓ {r.server}: {r.latency_ms:.2f}ms")
    else:
        print(f"✗ {r.server}: {r.error}")
```

**JSON Export:**
```python
json_output = validator.to_json(servers, max_ms=100, pretty=True)
with open('valid_dns.json', 'w') as f:
    f.write(json_output)
```

**Streaming (Memory Efficient):**
```python
async def process_huge_list():
    validator = Validator(concurrency=100)
    async for server, latency in validator.validate_streaming_async(servers):
        print(f"{server}: {latency:.2f}ms")

asyncio.run(process_huge_list())
```

### Cronjob Example

**Bash Script:**
```bash
#!/bin/bash
# /usr/local/bin/dns_monitor.sh

API_URL="https://api.example.com/dns/update"
OUTPUT_DIR="/var/lib/dns-monitor"

mkdir -p "$OUTPUT_DIR"

# Validate and save
pyresolvers -tL https://public-dns.info/nameservers.txt \
    --max-speed 100 \
    --format json \
    -o "$OUTPUT_DIR/resolvers.json"

# Send to API
curl -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d @"$OUTPUT_DIR/resolvers.json"
```

**Crontab:**
```cron
# Run every 6 hours
0 */6 * * * /usr/local/bin/dns_monitor.sh >> /var/log/dns-monitor.log 2>&1
```

---

## Input Formats

PyResolvers supports multiple input methods for maximum flexibility.

### URL Input

Download resolver lists directly from URLs:

```bash
# Public DNS list (62,000+ resolvers)
pyresolvers -tL https://public-dns.info/nameservers.txt --max-speed 50

# Your own hosted list
pyresolvers -tL https://example.com/dns-servers.txt

# GitHub raw files
pyresolvers -tL https://raw.githubusercontent.com/user/repo/main/resolvers.txt
```

### File Input

Load from local files:

```bash
# Plain text file (one IP per line)
pyresolvers -tL resolvers.txt

# CSV format (automatically extracts IPs)
pyresolvers -tL servers.csv

# Mixed format with comments
pyresolvers -tL list.txt
```

### Supported File Formats

PyResolvers automatically extracts valid IPv4 addresses from:

**Plain Text:**
```
8.8.8.8
1.1.1.1
208.67.222.222
```

**CSV/TSV:**
```
8.8.8.8,Google,US,Fast
1.1.1.1,Cloudflare,US,Fast
208.67.222.222,OpenDNS,US,Moderate
```

**With Comments:**
```
# Google Public DNS
8.8.8.8
# Cloudflare
1.1.1.1
# OpenDNS
208.67.222.222
```

**Mixed Format:**
```
Server: 8.8.8.8 (Google)
dns1=1.1.1.1
208.67.222.222 # OpenDNS Primary
```

### Validation

All input is validated automatically:
- ✅ Extracts IPv4 addresses from any position in a line
- ✅ Validates IP format (0-255 per octet)
- ✅ Skips empty lines and comments (#)
- ✅ Handles CSV, TSV, and space-separated formats
- ✅ Removes duplicates automatically

### Exclusions

Exclude servers using the same formats:

```bash
# Exclude from URL
pyresolvers -tL all.txt -eL https://example.com/blacklist.txt

# Exclude from file
pyresolvers -tL https://public-dns.info/nameservers.txt -eL blocked.txt

# Exclude single IP
pyresolvers -tL resolvers.txt -e 8.8.8.8
```

---

## API Reference

### Validator

High-performance async DNS validator.

```python
Validator(
    trusted_resolvers: Optional[List[str]] = None,  # ["1.1.1.1", "8.8.8.8"]
    test_domains: Optional[List[str]] = None,       # ["bet365.com", "telegram.com"]
    poison_check_domains: Optional[List[str]] = None,
    baseline_domain: str = "bet365.com",
    query_prefix: str = "dnsvalidator",
    concurrency: int = 50,                          # Async concurrency
    timeout: int = 5,                               # DNS timeout (seconds)
    use_fast_timeout: bool = False,                 # Fast dead server detection (optional speedup)
    batch_size: int = 100,                          # Memory management
    verbose: bool = False
)
```

**Methods:**

- `validate(servers)` → `List[ValidationResult]` - Validate servers
- `validate_by_speed(servers, min_ms, max_ms)` → `List[Tuple[str, float]]` - Get valid servers ordered by speed
- `to_json(servers, min_ms, max_ms)` → `str` - Export as JSON
- `to_text(servers, min_ms, max_ms, show_speed)` → `str` - Export as text

**Async Methods:**

- `await validate_async(servers)` - Async validation
- `await validate_by_speed_async(servers, min_ms, max_ms)` - Async speed validation
- `async for server, latency in validate_streaming_async(servers)` - Async streaming

### ValidationResult

```python
@dataclass
class ValidationResult:
    server: str
    valid: bool
    latency_ms: float
    error: Optional[str] = None
```

---

## CLI Options

| Option | Description |
|--------|-------------|
| `-t SERVER` | Test single server |
| `-tL FILE/URL` | Test from file or URL |
| `-e SERVER` | Exclude server |
| `-eL FILE/URL` | Exclude from file/URL |
| `-r DOMAIN` | Baseline domain (default: bet365.com) |
| `-threads N` | Concurrency (default: 5) |
| `-timeout N` | Timeout seconds (default: 600) |
| `-o FILE` | Output file |
| `--format FORMAT` | text, json, text-with-speed |
| `--max-speed MS` | Max latency filter (ms) |
| `--min-speed MS` | Min latency filter (ms) |
| `--silent` | Only output IPs |
| `-v, --verbose` | Verbose output |
| `--no-color` | Disable colors |

---

## Performance Tips

- **Concurrency**: 50-100 for best performance on most systems
- **Timeout**: Lower (3s) for speed, higher (10s+) for thoroughness
- **Fast Timeout**: Enable (`use_fast_timeout=True`) for 30-50% speedup (may miss slow servers)
- **Batch Size**: Increase for more memory, decrease for less
- **Network**: Run from VPS to avoid ISP throttling

### Optimization Features

1. **Async I/O** - Non-blocking DNS queries with aiodns
2. **Parallel Baseline** - Queries trusted resolvers simultaneously
3. **Fast Timeout** - 1s initial timeout for dead server detection
4. **Combined Queries** - Reduces DNS round trips
5. **Batch Processing** - Memory-efficient for huge lists
6. **Streaming** - Progressive results without holding all in memory

---

## How It Works

1. **Baseline** - Query trusted DNS (Cloudflare, Google) for ground truth
2. **Poisoning Check** - Test random subdomains to detect hijacking
3. **NXDOMAIN** - Verify correct NXDOMAIN behavior
4. **Baseline Compare** - Ensure responses match baseline
5. **Speed Test** - Measure latency and order results

---

## Important Notes

### Thread Count

Keep concurrency reasonable (50-100) to avoid triggering rate limits. Very high concurrency may be blocked by ISPs or DNS providers.

### Domain Selection

Use **non-geolocated** domains for baseline (bet365.com works well). Avoid google.com, facebook.com as they return different IPs by location.

---

## Project Structure

```
pyresolvers/
├── pyresolvers/
│   ├── __init__.py          # Package exports
│   ├── __main__.py          # CLI entry
│   ├── validator.py         # Async validation
│   └── lib/core/
│       ├── input.py         # CLI args
│       ├── output.py        # Formatting
│       └── __version__.py
├── requirements.txt
├── setup.py
└── README.md
```

---

## License

GNU General Public License v3.0 - see [LICENSE](LICENSE)

---

## Acknowledgments

Based on [dnsvalidator](https://github.com/vortexau/dnsvalidator) by:
- **James McLean** ([@vortexau](https://twitter.com/vortexau))
- **Michael Skelton** ([@codingo_](https://twitter.com/codingo_))

Enhanced with async architecture, speed testing, and performance optimizations by Karl.

---

<div align="center">

**[⬆ back to top](#pyresolvers)**

Made with ❤️ by Karl | Based on dnsvalidator by @vortexau & @codingo_

</div>
