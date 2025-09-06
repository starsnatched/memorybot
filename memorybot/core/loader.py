from __future__ import annotations

import importlib
import logging
import pkgutil
from typing import Iterable, List, Tuple
import time


def discover_extensions(package: str) -> List[str]:
    log = logging.getLogger("memorybot.loader")
    mods: List[str] = []
    pkg = importlib.import_module(package)
    for m in pkgutil.walk_packages(pkg.__path__, prefix=pkg.__name__ + "."):
        if m.ispkg:
            continue
        name = m.name
        leaf = name.rsplit(".", 1)[-1]
        if leaf.startswith("_") or leaf.endswith("__init__"):
            continue
        mods.append(name)
    mods = sorted(mods)
    log.debug("discovered %d extensions in %s", len(mods), package)
    return mods


async def load_extensions(client, modules: Iterable[str]) -> Tuple[list[str], list[tuple[str, Exception]]]:
    log = logging.getLogger("memorybot.loader")
    loaded: list[str] = []
    failed: list[tuple[str, Exception]] = []
    for m in modules:
        start = time.perf_counter()
        log.debug("loading extension %s", m)
        try:
            if m in getattr(client, "extensions", {}):
                client.reload_extension(m)
            else:
                client.load_extension(m)
            loaded.append(m)
            elapsed = (time.perf_counter() - start) * 1000
            log.debug("loaded extension %s in %.0fms", m, elapsed)
        except Exception as e:
            failed.append((m, e))
            elapsed = (time.perf_counter() - start) * 1000
            log.error("failed loading extension %s after %.0fms", m, elapsed, exc_info=e)
    return loaded, failed
