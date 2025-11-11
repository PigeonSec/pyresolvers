<div align="center">

<img src="logo.png" alt="PyResolvers Logo" width="200" height="200">

# PyResolvers

**High-Performance Async DNS Resolver Validation & Speed Testing**

[![Tests](https://github.com/PigeonSec/pyresolvers/actions/workflows/test-and-publish.yml/badge.svg?branch=master)](https://github.com/PigeonSec/pyresolvers/actions/workflows/test-and-publish.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![PyPI version](https://img.shields.io/pypi/v/pyresolvers.svg)](https://pypi.org/project/pyresolvers/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

*Validate DNS resolvers, measure response times, identify the fastest servers*

</div>

---

## Overview

PyResolvers is a high-performance async Python library and CLI tool for validating DNS resolvers. It performs comprehensive validation (baseline comparison, poisoning detection, NXDOMAIN verification) and orders results by speed.

### Features

- ⚡ **High-Performance Async** - Up to 3x faster than thread-based validators
- 🚀 **Speed Testing** - Measures and orders resolvers by latency
- 🌐 **URL Support** - Download resolver lists from URLs (HTTP/HTTPS)
- 🔍 **Comprehensive Validation** - Baseline, poisoning, NXDOMAIN checks
- 🛡️ **Poisoning Detection** - 3-domain check (Amazon, PayPal, Netflix)
- 📊 **Multiple Formats** - JSON, plain text, text+speed
- 🎯 **Speed Filtering** - Filter by min/max latency thresholds
- 📝 **Smart Parsing** - Auto-extracts IPs from CSV, text, and mixed formats
- 🔊 **Verbose Mode** - See rejected/filtered servers with reasons
- 💨 **Streaming Results** - Real-time output as servers are validated

### Performance

**Benchmark (500 servers from public-dns.info):**

| Concurrency | Timeout | Time | Test Rate | Speedup |
|-------------|---------|------|-----------|---------|
| 50 (default) | 1.0s | 36.7s | 13.6/sec | baseline |
| 100 | 1.0s | 18.3s | 27.3/sec | **2.0x** ⚡ |
| 200 | 0.5s | 14.5s | 34.6/sec | **2.5x** 🚀 |

**Estimated time for 62,607 servers:**
- Default (50 threads): ~77 minutes
- Optimized (200 threads, 0.5s timeout): **~30 minutes**

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

**Requirements**: Python 3.12+, aiodns, pycares, colorclass

---

## Quick Start

### CLI Commands

**Basic validation:**
```bash
$ pyresolvers -t 1.1.1.1
=======================================================
pyresolvers v2.0.1 - DNS Resolver Validator
=======================================================
[10:25:04] [INFO] Testing 1 servers
[10:25:04] [INFO] Establishing baseline...
[10:25:04] [INFO] Validating with concurrency=50...
[10:25:04] [ACCEPTED] [1.1.1.1] 20.49ms
[10:25:04] [INFO] Found 1 valid servers
```

**Test multiple servers from file:**
```bash
$ pyresolvers -tL dns_servers.txt
[10:25:11] [INFO] Testing 3 servers
[10:25:11] [INFO] Establishing baseline...
[10:25:11] [INFO] Validating with concurrency=50...
[10:25:11] [ACCEPTED] [9.9.9.9] 9.00ms
[10:25:11] [ACCEPTED] [8.8.8.8] 15.79ms
[10:25:11] [ACCEPTED] [1.1.1.1] 19.69ms
[10:25:11] [INFO] Found 3 valid servers
```

**Silent mode (IPs only, perfect for piping):**
```bash
$ pyresolvers -tL dns_servers.txt --silent
9.9.9.9
8.8.8.8
1.1.1.1
```

**Verbose mode with speed filtering:**
```bash
$ pyresolvers -tL dns_servers.txt --max-speed 15 -v
[10:25:27] [INFO] Testing 3 servers
[10:25:27] [INFO] Max speed filter: 15.0ms
[10:25:28] [ACCEPTED] [9.9.9.9] 9.05ms
[10:25:28] [REJECTED] [1.1.1.1] Too slow: 20.30ms
[10:25:28] [REJECTED] [8.8.8.8] Too slow: 20.22ms
[10:25:28] [INFO] Found 1 valid servers
```

**JSON output format:**
```bash
$ pyresolvers -tL dns_servers.txt --format json
{
  "servers": [
    {"ip": "9.9.9.9", "latency_ms": 10.3},
    {"ip": "8.8.8.8", "latency_ms": 15.96},
    {"ip": "1.1.1.1", "latency_ms": 20.35}
  ],
  "count": 3,
  "filters": {"min_ms": null, "max_ms": null}
}
```

**More examples:**
```bash
# Test from URL
pyresolvers -tL https://public-dns.info/nameservers.txt

# Speed filtering and save to file
pyresolvers -tL resolvers.txt --max-speed 50 -o fast_dns.txt
pyresolvers -tL resolvers.txt --min-speed 10 --max-speed 100

# Text with speed output
pyresolvers -tL resolvers.txt --format text-with-speed -o dns_with_speed.txt

# Exclusions
pyresolvers -tL all_resolvers.txt -e 8.8.8.8
pyresolvers -tL resolvers.txt -eL blacklist.txt

# Performance tuning
pyresolvers -tL large_list.txt -threads 200 -timeout 0.5
pyresolvers -tL https://public-dns.info/nameservers.txt -threads 200 --max-speed 30 | head -10
```

### Library Usage

```python
from pyresolvers import Validator

# Basic usage - get valid servers ordered by speed
validator = Validator()
servers = ['1.1.1.1', '8.8.8.8', '9.9.9.9']
results = validator.validate_by_speed(servers)

for server, latency in results:
    print(f"{server}: {latency:.2f}ms")

# High concurrency with speed filtering
validator = Validator(concurrency=100)
fast = validator.validate_by_speed(servers, max_ms=50)

# Detailed results with error information
results = validator.validate(servers)
for r in results:
    if r.valid:
        print(f"✓ {r.server}: {r.latency_ms:.2f}ms")
    else:
        print(f"✗ {r.server}: {r.error}")

# JSON export
json_output = validator.to_json(servers, max_ms=100, pretty=True)
with open('valid_dns.json', 'w') as f:
    f.write(json_output)

# Async usage
import asyncio

async def main():
    validator = Validator(concurrency=200)
    results = await validator.validate_by_speed_async(servers)
    return results

results = asyncio.run(main())

# Streaming for huge lists (memory efficient)
async def process_huge_list():
    validator = Validator(concurrency=100)
    async for server, latency in validator.validate_streaming_async(servers):
        print(f"{server}: {latency:.2f}ms")

asyncio.run(process_huge_list())
```

### Cronjob Examples

**Daily DNS validation with API upload:**
```bash
#!/bin/bash
# /usr/local/bin/dns_monitor.sh

OUTPUT_DIR="/var/lib/dns-monitor"
mkdir -p "$OUTPUT_DIR"

# Validate and save to JSON
pyresolvers -tL https://public-dns.info/nameservers.txt \
    --max-speed 100 \
    --format json \
    -o "$OUTPUT_DIR/resolvers.json"

# Upload to API
curl -X POST "https://api.example.com/dns/update" \
    -H "Content-Type: application/json" \
    -d @"$OUTPUT_DIR/resolvers.json"
```

**Fast resolver discovery and update:**
```bash
#!/bin/bash
# /usr/local/bin/update_fast_dns.sh

# Get fastest resolvers (< 30ms) and update system config
pyresolvers -tL https://public-dns.info/nameservers.txt \
    --max-speed 30 \
    --silent \
    -threads 200 \
    -timeout 0.5 \
    -o /tmp/fast_dns.txt

# Use top 3 fastest
head -3 /tmp/fast_dns.txt > /etc/my_app/dns_servers.conf
```

**Crontab entries:**
```cron
# Daily API sync at 2 AM
0 2 * * * /usr/local/bin/dns_monitor.sh >> /var/log/dns-monitor.log 2>&1

# Update fast DNS every 6 hours
0 */6 * * * /usr/local/bin/update_fast_dns.sh >> /var/log/dns-update.log 2>&1
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
| `-threads N` | Concurrency (default: 50) |
| `-timeout N` | Timeout seconds (default: 1) |
| `-o FILE` | Output file |
| `--format FORMAT` | text, json, text-with-speed |
| `--max-speed MS` | Max latency filter (ms) |
| `--min-speed MS` | Min latency filter (ms) |
| `--silent` | Only output IPs |
| `-v, --verbose` | Verbose output |
| `--no-color` | Disable colors |

---

## Performance Tips

### Recommended Settings

**For 60K+ servers (fastest):**
```bash
pyresolvers -tL https://public-dns.info/nameservers.txt -threads 200 -timeout 0.5 --max-speed 200 -o results.txt
```

**For balanced speed/accuracy:**
```bash
pyresolvers -tL large_list.txt -threads 100 -timeout 1 --max-speed 100
```

**For verbose debugging:**
```bash
pyresolvers -tL resolvers.txt -threads 50 -v
```

### Configuration Guide

- **Concurrency**:
  - 50-100 for stable performance
  - 200-300 for maximum speed (requires good network)
  - Higher may trigger rate limits

- **Timeout**:
  - 0.5s for fast dead server detection
  - 1s for balanced performance (default)
  - 2s+ for slow/distant servers

- **Verbose Mode**: Use `-v` to see rejected servers with reasons:
  - "Too slow: XXms" - Exceeded max-speed filter
  - "Timeout" - Server didn't respond
  - "Invalid" - Failed validation checks
  - "DNS poisoning" - Detected hijacking

### Optimization Features

1. **Async I/O** - Non-blocking DNS queries with aiodns
2. **Parallel Validation** - All checks run simultaneously
3. **Streaming Output** - Results appear in real-time
4. **Smart Poisoning** - 3 diverse domains (Amazon, PayPal, Netflix)
5. **Optimized Defaults** - 50 threads, 1s timeout, fast mode enabled
6. **Progress Indicators** - Shows validation progress every 100 servers

---

## How It Works

1. **Baseline Setup** - Query trusted resolvers (1.1.1.1, 8.8.8.8) for ground truth
2. **Parallel Validation** - For each server, run simultaneously:
   - **Poisoning Check** - Test 3 random subdomains (amazon.com, paypal.com, netflix.com)
   - **NXDOMAIN Check** - Verify correct NXDOMAIN behavior
   - **Baseline Compare** - Ensure responses match trusted resolvers
3. **Latency Measurement** - Measure DNS query speed for valid servers
4. **Real-time Output** - Stream results as validation completes
5. **Speed Filtering** - Apply min/max latency filters and output sorted results

---

## Important Notes

### Thread Count

Keep concurrency reasonable (50-100) to avoid triggering rate limits. Very high concurrency may be blocked by ISPs or DNS providers.

### Domain Selection

Use **non-geolocated** domains for baseline (bet365.com works well). Avoid google.com, facebook.com as they return different IPs by location.

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
