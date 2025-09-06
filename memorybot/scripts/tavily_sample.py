from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

from memorybot.services.tavily_search import TavilySearchService, TavilySearchOptions


async def _amain() -> int:
    parser = argparse.ArgumentParser(prog="tavily-sample", add_help=True)
    parser.add_argument("query", nargs="?", default="What are AI startups that are based in NYC?")
    parser.add_argument("--include-answer", dest="include_answer", choices=["none", "basic", "advanced"], default="advanced")
    parser.add_argument("--search-depth", dest="search_depth", choices=["basic", "advanced"], default="advanced")
    parser.add_argument("--max-results", dest="max_results", type=int, default=7)
    parser.add_argument("--timeout", dest="timeout", type=float, default=20.0)
    args = parser.parse_args()

    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        sys.stderr.write("TAVILY_API_KEY is not set.\n")
        return 2

    service = TavilySearchService(api_key=api_key)
    options = TavilySearchOptions(
        include_answer=args.include_answer,
        search_depth=args.search_depth,
        max_results=args.max_results,
    )
    result = await service.search(args.query, options=options, timeout=args.timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_amain()))


if __name__ == "__main__":
    main()

