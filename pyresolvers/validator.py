#!/usr/bin/env python3
"""High-performance async DNS resolver validation."""

from __future__ import annotations

import asyncio
import json
import random
import string
import time
from dataclasses import asdict, dataclass
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import AsyncIterator, Dict, List, Optional, Tuple

try:
    import dns.asyncresolver
    import dns.exception
    import dns.resolver
    DNSPYTHON_AVAILABLE = True
except ImportError:
    DNSPYTHON_AVAILABLE = False

# Configuration
TRUSTED_RESOLVERS = ["1.1.1.1", "8.8.8.8"]
TEST_DOMAINS = ["bet365.com", "telegram.com"]
POISON_CHECK_DOMAINS = ["amazon.com", "paypal.com", "netflix.com"]  # 3 diverse domains for security
BASELINE_DOMAIN = "bet365.com"
QUERY_PREFIX = "dnsvalidator"
DEFAULT_CONCURRENCY = 50  # Balanced concurrency for async performance
DEFAULT_TIMEOUT = 1  # Fast timeout for responsiveness
FAST_TIMEOUT = 0.5  # Very quick timeout for dead server detection
SUBDOMAIN_LENGTH = 10
BATCH_SIZE = 500  # Larger batches for better throughput


@dataclass
class ValidationResult:
    """DNS resolver validation result."""
    server: str
    valid: bool
    latency_ms: float
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class Validator:
    """High-performance async DNS resolver validator."""

    def __init__(
        self,
        trusted_resolvers: Optional[List[str]] = None,
        test_domains: Optional[List[str]] = None,
        poison_check_domains: Optional[List[str]] = None,
        baseline_domain: str = BASELINE_DOMAIN,
        query_prefix: str = QUERY_PREFIX,
        concurrency: int = DEFAULT_CONCURRENCY,
        timeout: int = DEFAULT_TIMEOUT,
        use_fast_timeout: bool = False,
        batch_size: int = BATCH_SIZE,
        verbose: bool = False
    ) -> None:
        if not DNSPYTHON_AVAILABLE:
            raise ImportError(
                "dnspython required for Validator. Install with: pip install dnspython\n"
                "Or: pip install -r requirements.txt"
            )

        self.trusted_resolvers = trusted_resolvers or TRUSTED_RESOLVERS
        self.test_domains = test_domains or TEST_DOMAINS
        self.poison_check_domains = poison_check_domains or POISON_CHECK_DOMAINS
        self.baseline_domain = baseline_domain
        self.query_prefix = query_prefix
        self.concurrency = concurrency
        self.timeout = timeout
        self.use_fast_timeout = use_fast_timeout
        self.batch_size = batch_size
        self.verbose = verbose
        self._baseline_ip = ""
        self._baseline_data: Dict[str, Dict] = {}

    @staticmethod
    def _random_subdomain(length: int = SUBDOMAIN_LENGTH) -> str:
        """Generate random subdomain for testing."""
        return ''.join(random.choices(string.ascii_lowercase, k=length))

    @staticmethod
    def _is_valid_ip(ip_str: str) -> bool:
        """Validate IPv4/IPv6 address format."""
        try:
            return isinstance(ip_address(ip_str), (IPv4Address, IPv6Address))
        except ValueError:
            return False

    def _log(self, msg: str) -> None:
        """Log message if verbose mode enabled."""
        if self.verbose:
            print(msg)

    def _create_resolver(self, nameserver: str, timeout: Optional[float] = None) -> dns.asyncresolver.Resolver:
        """Create a DNS resolver using dnspython (no inotify watches).

        dnspython doesn't use c-ares, so it avoids inotify watch exhaustion.
        """
        resolver = dns.asyncresolver.Resolver()
        resolver.nameservers = [nameserver]
        resolver.timeout = timeout or self.timeout
        resolver.lifetime = timeout or self.timeout
        return resolver

    async def _setup_baseline_single(self, resolver_ip: str) -> bool:
        """Setup baseline from single trusted resolver."""
        self._log(f"[INFO] {resolver_ip} - Establishing baseline")
        try:
            resolver = self._create_resolver(resolver_ip)
            data = {}

            # Get baseline IP
            result = await resolver.resolve(self.baseline_domain, 'A')
            data["ip"] = self._baseline_ip = str(result[0])

            # Test domains in parallel
            domain_tasks = [resolver.resolve(domain, 'A') for domain in self.test_domains]
            domain_results = await asyncio.gather(*domain_tasks, return_exceptions=True)

            data["domains"] = {}
            for domain, result in zip(self.test_domains, domain_results):
                if not isinstance(result, Exception):
                    data["domains"][domain] = str(result[0])

            # NXDOMAIN check
            try:
                await resolver.resolve(self.query_prefix + self.baseline_domain, 'A')
                data["nxdomain"] = False
            except (dns.exception.DNSException, dns.resolver.NXDOMAIN):
                data["nxdomain"] = True

            self._baseline_data[resolver_ip] = data
            return True
        except Exception as e:
            self._log(f"[ERROR] {resolver_ip} - {str(e)}")
            return False

    async def _setup_baseline(self) -> bool:
        """Setup baseline from all trusted resolvers in parallel."""
        tasks = [self._setup_baseline_single(ip) for ip in self.trusted_resolvers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for r in results if r is True)
        return success_count == len(self.trusted_resolvers)

    async def _check_poisoning(self, resolver: dns.asyncresolver.Resolver, server: str) -> Optional[str]:
        """Check for DNS poisoning with parallel queries.

        All poison domains are checked in parallel for maximum speed.
        Returns immediately if ANY domain resolves (indicating poisoning).
        """
        subdomains = [f"{self._random_subdomain()}.{domain}" for domain in self.poison_check_domains]
        tasks = [resolver.resolve(subdomain, 'A') for subdomain in subdomains]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for subdomain, result in zip(subdomains, results):
            if not isinstance(result, Exception):
                self._log(f"[ERROR] {server} - Poisoning detected: {subdomain}")
                return "DNS poisoning"
        return None

    async def _check_nxdomain_and_baseline(
        self, resolver: dns.asyncresolver.Resolver, server: str
    ) -> Tuple[bool, bool, Optional[str]]:
        """Combined NXDOMAIN and baseline validation check. Returns (has_nxdomain, baseline_matches, error)."""
        subdomain = f"{self._random_subdomain()}.{self.baseline_domain}"

        try:
            # Check NXDOMAIN and baseline in parallel
            nxdomain_task = resolver.resolve(subdomain, 'A')
            baseline_task = resolver.resolve(self.baseline_domain, 'A')

            nxdomain_result, baseline_result = await asyncio.gather(
                nxdomain_task, baseline_task, return_exceptions=True
            )

            # NXDOMAIN should fail
            has_nxdomain = isinstance(nxdomain_result, Exception)

            # Baseline should match
            baseline_matches = False
            if not isinstance(baseline_result, Exception):
                resolved_ip = str(baseline_result[0])
                baseline_matches = resolved_ip == self._baseline_ip

            return has_nxdomain, baseline_matches, None

        except Exception as e:
            return False, False, f"Error: {str(e)}"

    def _matches_baseline(self, has_nxdomain: bool) -> bool:
        """Verify resolver matches baseline behavior."""
        matches = sum(
            1 for data in self._baseline_data.values()
            if data.get("ip") == self._baseline_ip and data.get("nxdomain") == has_nxdomain
        )
        return matches == len(self.trusted_resolvers)

    async def _measure_latency(self, server: str) -> float:
        """Measure simple DNS query latency."""
        try:
            resolver = self._create_resolver(server, timeout=1)
            start = time.time()
            await resolver.resolve(self.baseline_domain, 'A')
            return (time.time() - start) * 1000
        except:
            return -1

    async def _validate_server(self, server: str) -> ValidationResult:
        """Fast validation - just check if server is valid, no latency measurement."""
        if not self._is_valid_ip(server):
            return ValidationResult(server, False, -1, "Invalid IP")

        try:
            timeout = FAST_TIMEOUT if self.use_fast_timeout else self.timeout
            resolver = self._create_resolver(server, timeout=timeout)

            # Run ALL checks in parallel for max speed
            poison_task = self._check_poisoning(resolver, server)
            nxdomain_task = self._check_nxdomain_and_baseline(resolver, server)

            poison_error, (has_nxdomain, baseline_matches, nxdomain_error) = await asyncio.gather(
                poison_task, nxdomain_task
            )

            if poison_error:
                return ValidationResult(server, False, -1, poison_error)
            if nxdomain_error:
                return ValidationResult(server, False, -1, nxdomain_error)

            valid = baseline_matches and self._matches_baseline(has_nxdomain)
            return ValidationResult(server, valid, -1, None if valid else "Invalid")

        except asyncio.TimeoutError:
            return ValidationResult(server, False, -1, "Timeout")
        except Exception as e:
            return ValidationResult(server, False, -1, str(e))

    async def _validate_batch(self, servers: List[str]) -> List[ValidationResult]:
        """Validate batch of servers with concurrency limit."""
        semaphore = asyncio.Semaphore(self.concurrency)
        completed = 0
        total = len(servers)
        lock = asyncio.Lock()
        last_report = 0

        async def bounded_validate(server: str) -> ValidationResult:
            nonlocal completed, last_report
            async with semaphore:
                result = await self._validate_server(server)

                # Thread-safe progress tracking
                async with lock:
                    completed += 1
                    # Show progress every 100 servers (more frequent updates)
                    if completed - last_report >= 100 or completed == total:
                        print(f"[Progress] {completed}/{total} servers validated ({completed*100//total}%)", flush=True)
                        last_report = completed

                return result

        tasks = [bounded_validate(server) for server in servers]
        return await asyncio.gather(*tasks)

    async def validate_async(self, servers: List[str]) -> List[ValidationResult]:
        """Validate multiple DNS servers asynchronously."""
        if not await self._setup_baseline():
            raise RuntimeError("Baseline setup failed")

        # Process ALL servers concurrently - semaphore limits actual concurrency
        results = await self._validate_batch(servers)
        return results

    async def validate_by_speed_async(
        self, servers: List[str], min_ms: Optional[float] = None, max_ms: Optional[float] = None
    ) -> List[Tuple[str, float]]:
        """Get valid servers ordered by speed."""
        results = await self.validate_async(servers)

        # Measure latency for valid servers
        valid_servers = [r.server for r in results if r.valid]

        # Measure latencies in parallel
        latency_tasks = [self._measure_latency(server) for server in valid_servers]
        latencies = await asyncio.gather(*latency_tasks)

        # Combine servers with their latencies
        filtered = [
            (server, latency)
            for server, latency in zip(valid_servers, latencies)
            if latency > 0
        ]

        if min_ms:
            filtered = [(s, t) for s, t in filtered if t >= min_ms]
        if max_ms:
            filtered = [(s, t) for s, t in filtered if t <= max_ms]

        return sorted(filtered, key=lambda x: x[1])

    async def validate_streaming_async(
        self, servers: List[str], min_ms: Optional[float] = None, max_ms: Optional[float] = None
    ) -> AsyncIterator[Tuple[str, float]]:
        """Stream valid servers as they're validated (memory efficient)."""
        if not await self._setup_baseline():
            raise RuntimeError("Baseline setup failed")

        semaphore = asyncio.Semaphore(self.concurrency)

        async def validate_and_filter(server: str) -> Optional[Tuple[str, float]]:
            async with semaphore:
                result = await self._validate_server(server)
                if result.valid and result.latency_ms > 0:
                    if (not min_ms or result.latency_ms >= min_ms) and \
                       (not max_ms or result.latency_ms <= max_ms):
                        return (result.server, result.latency_ms)
                return None

        # Stream results as they complete - no batching delay!
        tasks = [validate_and_filter(server) for server in servers]
        for coro in asyncio.as_completed(tasks):
            result = await coro
            if result is not None:
                yield result

    async def to_json_async(
        self, servers: List[str], min_ms: Optional[float] = None, max_ms: Optional[float] = None, pretty: bool = True
    ) -> str:
        """Export validation results as JSON."""
        results = await self.validate_by_speed_async(servers, min_ms, max_ms)
        output = {
            "servers": [{"ip": s, "latency_ms": round(t, 2)} for s, t in results],
            "count": len(results),
            "filters": {"min_ms": min_ms, "max_ms": max_ms}
        }
        return json.dumps(output, indent=2 if pretty else None)

    async def to_text_async(
        self, servers: List[str], min_ms: Optional[float] = None, max_ms: Optional[float] = None, show_speed: bool = False
    ) -> str:
        """Export validation results as plain text."""
        results = await self.validate_by_speed_async(servers, min_ms, max_ms)
        if show_speed:
            return '\n'.join(f"{s} {t:.2f}ms" for s, t in results)
        return '\n'.join(s for s, _ in results)

    # Sync wrappers for compatibility
    def validate(self, servers: List[str]) -> List[ValidationResult]:
        """Validate servers (sync wrapper)."""
        return asyncio.run(self.validate_async(servers))

    def validate_by_speed(
        self, servers: List[str], min_ms: Optional[float] = None, max_ms: Optional[float] = None
    ) -> List[Tuple[str, float]]:
        """Get valid servers ordered by speed (sync wrapper)."""
        return asyncio.run(self.validate_by_speed_async(servers, min_ms, max_ms))

    def to_json(
        self, servers: List[str], min_ms: Optional[float] = None, max_ms: Optional[float] = None, pretty: bool = True
    ) -> str:
        """Export as JSON (sync wrapper)."""
        return asyncio.run(self.to_json_async(servers, min_ms, max_ms, pretty))

    def to_text(
        self, servers: List[str], min_ms: Optional[float] = None, max_ms: Optional[float] = None, show_speed: bool = False
    ) -> str:
        """Export as text (sync wrapper)."""
        return asyncio.run(self.to_text_async(servers, min_ms, max_ms, show_speed))
