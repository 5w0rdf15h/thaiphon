"""Benchmark resident memory and lookup latency for the bundled lexicon.

Run twice — once before any changes, once after — to compare RSS and
per-lookup latency.

Usage:

    python scripts/bench_memory.py

Prints RSS (resident set size) at three checkpoints:

    1. Cold (right after Python starts, before any thaiphon import).
    2. After a single ``transcribe`` call (forces lexicon load).
    3. After 1000 random word lookups against the bundled lexicon.
"""

from __future__ import annotations

import random
import resource
import sys
import time


def _rss_bytes() -> int:
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is bytes on macOS, kilobytes on Linux.
    if sys.platform == "darwin":
        return int(usage)
    return int(usage) * 1024


def _fmt(n: int) -> str:
    return f"{n / (1024 * 1024):.1f} MiB"


def main() -> None:
    cold = _rss_bytes()
    print(f"[1] cold RSS                : {_fmt(cold)}")

    from thaiphon.api import transcribe_sentence  # noqa: PLC0415

    transcribe_sentence("สวัสดีครับ")
    after_first = _rss_bytes()
    print(f"[2] after first transcribe  : {_fmt(after_first)}  (+{_fmt(after_first - cold)})")

    from thaiphon.lexicons.exact import entries  # noqa: PLC0415

    lex = entries()
    keys = list(lex.keys())
    if not keys:
        print("    (lexicon is empty — skipping random lookups)")
        return
    print(f"    lexicon size            : {len(keys):,} entries")

    rng = random.Random(0xC0FFEE)
    sample = [rng.choice(keys) for _ in range(1000)]

    per_call: list[float] = []
    hits = 0
    t0 = time.perf_counter()
    for word in sample:
        s = time.perf_counter()
        v = lex.get(word)
        per_call.append(time.perf_counter() - s)
        if v is not None:
            hits += 1
    elapsed = time.perf_counter() - t0
    after_lookups = _rss_bytes()
    per_call.sort()
    median_us = per_call[len(per_call) // 2] * 1_000_000
    mean_us = (elapsed / len(per_call)) * 1_000_000
    print(f"[3] after 1000 lookups      : {_fmt(after_lookups)}  (+{_fmt(after_lookups - after_first)})")
    print(f"    1000 lookups            : {elapsed * 1000:.2f} ms total, "
          f"mean={mean_us:.3f} us/lookup, median={median_us:.3f} us/lookup, hits={hits}")


if __name__ == "__main__":
    main()
