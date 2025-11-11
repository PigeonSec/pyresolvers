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
    import aiodns
    AIODNS_AVAILABLE = True
except ImportError:
    AIODNS_AVAILABLE = False

# Configuration
TRUSTED_RESOLVERS = ["1.1.1.1", "8.8.8.8"]
TEST_DOMAINS = ["bet365.com", "telegram.com"]
POISON_CHECK_DOMAINS = ["facebook.com", "paypal.com", "google.com", "bet365.com", "wikileaks.com"]
BASELINE_DOMAIN = "bet365.com"
QUERY_PREFIX = "dnsvalidator"
DEFAULT_CONCURRENCY = 50
DEFAULT_TIMEOUT = 5
FAST_TIMEOUT = 1  # Quick timeout for dead server detection
SUBDOMAIN_LENGTH = 10
BATCH_SIZE = 100


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
        if not AIODNS_AVAILABLE:
            raise ImportError(
                "aiodns required for Validator. Install with: pip install aiodns\n"
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

    async def _setup_baseline_single(self, resolver_ip: str) -> bool:
        """Setup baseline from single trusted resolver."""
        self._log(f"[INFO] {resolver_ip} - Establishing baseline")
        try:
            resolver = aiodns.DNSResolver(nameservers=[resolver_ip], timeout=self.timeout)
            data = {}

            # Get baseline IP
            result = await resolver.query(self.baseline_domain, 'A')
            data["ip"] = self._baseline_ip = result[0].host

            # Test domains in parallel
            domain_tasks = [resolver.query(domain, 'A') for domain in self.test_domains]
            domain_results = await asyncio.gather(*domain_tasks, return_exceptions=True)

            data["domains"] = {}
            for domain, result in zip(self.test_domains, domain_results):
                if not isinstance(result, Exception):
                    data["domains"][domain] = result[0].host

            # NXDOMAIN check
            try:
                await resolver.query(self.query_prefix + self.baseline_domain, 'A')
                data["nxdomain"] = False
            except aiodns.error.DNSError:
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

    async def _check_poisoning(self, resolver: aiodns.DNSResolver, server: str) -> Optional[str]:
        """Check for DNS poisoning with parallel queries."""
        subdomains = [f"{self._random_subdomain()}.{domain}" for domain in self.poison_check_domains]
        tasks = [resolver.query(subdomain, 'A') for subdomain in subdomains]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for subdomain, result in zip(subdomains, results):
            if not isinstance(result, Exception):
                self._log(f"[ERROR] {server} - Poisoning detected: {subdomain}")
                return "DNS poisoning"
        return None

    async def _check_nxdomain_and_baseline(
        self, resolver: aiodns.DNSResolver, server: str
    ) -> Tuple[bool, bool, float, Optional[str]]:
        """Combined NXDOMAIN and baseline validation check. Returns (has_nxdomain, baseline_matches, latency_ms, error)."""
        subdomain = f"{self._random_subdomain()}.{self.baseline_domain}"

        try:
            # Check NXDOMAIN and baseline in parallel
            nxdomain_task = resolver.query(subdomain, 'A')

            # Measure latency for baseline query only
            baseline_start = time.time()
            baseline_task = resolver.query(self.baseline_domain, 'A')

            nxdomain_result, baseline_result = await asyncio.gather(
                nxdomain_task, baseline_task, return_exceptions=True
            )

            # Calculate latency from baseline query only
            latency_ms = (time.time() - baseline_start) * 1000

            # NXDOMAIN should fail
            has_nxdomain = isinstance(nxdomain_result, Exception)

            # Baseline should match
            baseline_matches = False
            if not isinstance(baseline_result, Exception):
                resolved_ip = baseline_result[0].host
                baseline_matches = resolved_ip == self._baseline_ip

            return has_nxdomain, baseline_matches, latency_ms, None

        except Exception as e:
            return False, False, -1, f"Error: {str(e)}"

    def _matches_baseline(self, has_nxdomain: bool) -> bool:
        """Verify resolver matches baseline behavior."""
        matches = sum(
            1 for data in self._baseline_data.values()
            if data.get("ip") == self._baseline_ip and data.get("nxdomain") == has_nxdomain
        )
        return matches == len(self.trusted_resolvers)

    async def _validate_server(self, server: str) -> ValidationResult:
        """Validate single DNS server with fast timeout."""
        if not self._is_valid_ip(server):
            return ValidationResult(server, False, -1, "Invalid IP")

        self._log(f"[INFO] {server} - Validating...")

        # Use fast timeout for quick dead server detection
        timeout = FAST_TIMEOUT if self.use_fast_timeout else self.timeout

        try:
            resolver = aiodns.DNSResolver(nameservers=[server], timeout=timeout)

            # Check poisoning
            error = await self._check_poisoning(resolver, server)
            if error:
                return ValidationResult(server, False, -1, error)

            # If fast timeout worked, use full timeout for validation
            if self.use_fast_timeout and timeout < self.timeout:
                resolver = aiodns.DNSResolver(nameservers=[server], timeout=self.timeout)

            # Combined NXDOMAIN and baseline check (measure latency for baseline query only)
            has_nxdomain, baseline_matches, latency, error = await self._check_nxdomain_and_baseline(resolver, server)
            if error:
                return ValidationResult(server, False, -1, error)

            valid = baseline_matches and self._matches_baseline(has_nxdomain)

            self._log(f"[{'OK' if valid else 'FAIL'}] {server} - {latency:.2f}ms")
            return ValidationResult(server, valid, latency, None if valid else "Invalid")

        except asyncio.TimeoutError:
            return ValidationResult(server, False, -1, "Timeout")
        except Exception as e:
            return ValidationResult(server, False, -1, str(e))

    async def _validate_batch(self, servers: List[str]) -> List[ValidationResult]:
        """Validate batch of servers with concurrency limit."""
        semaphore = asyncio.Semaphore(self.concurrency)

        async def bounded_validate(server: str) -> ValidationResult:
            async with semaphore:
                return await self._validate_server(server)

        tasks = [bounded_validate(server) for server in servers]
        return await asyncio.gather(*tasks)

    async def validate_async(self, servers: List[str]) -> List[ValidationResult]:
        """Validate multiple DNS servers asynchronously."""
        if not await self._setup_baseline():
            raise RuntimeError("Baseline setup failed")

        # Process in batches for memory efficiency
        all_results = []
        for i in range(0, len(servers), self.batch_size):
            batch = servers[i:i + self.batch_size]
            results = await self._validate_batch(batch)
            all_results.extend(results)

        return all_results

    async def validate_by_speed_async(
        self, servers: List[str], min_ms: Optional[float] = None, max_ms: Optional[float] = None
    ) -> List[Tuple[str, float]]:
        """Get valid servers ordered by speed."""
        results = await self.validate_async(servers)

        # Filter and sort
        filtered = [
            (r.server, r.latency_ms)
            for r in results
            if r.valid and r.latency_ms > 0
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

        # Process in batches and yield results
        for i in range(0, len(servers), self.batch_size):
            batch = servers[i:i + self.batch_size]
            tasks = [validate_and_filter(server) for server in batch]
            results = await asyncio.gather(*tasks)

            for result in results:
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
