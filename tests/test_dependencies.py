"""Every import must be something Home Assistant will actually have installed.

manifest.json declares no requirements, so the integration may only import the
standard library and packages Home Assistant core installs itself. A module-level
import of anything else makes the whole integration fail to load on a user's
install, while CI -- where the test harness pulls in plenty of extra packages --
stays green.

Adapted from smarthomesec_ha, where exactly that happened with `async_timeout`
on HA 2026.10 (Python 3.14, no longer pulled in by aiohttp).
"""

import ast
import json
import sys
from pathlib import Path

COMPONENT = Path("custom_components/hra_renovasjon")

# Third-party packages Home Assistant core installs itself. `voluptuous` is no
# longer installed since 2026.9, but HA aliases it to probatio in sys.modules
# and documents that custom integrations may keep using it.
SHIPPED_BY_HA = {"homeassistant", "voluptuous", "aiohttp", "yarl"}


def _top_level_imports():
    found = {}
    for path in sorted(COMPONENT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                found.setdefault(name.split(".")[0], set()).add(path.name)
    return found


def _declared_modules():
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    return {
        requirement.split("==")[0].split(">=")[0].strip().lower().replace("-", "_")
        for requirement in manifest.get("requirements", [])
    }


def test_every_import_is_available_on_a_current_home_assistant():
    allowed = set(sys.stdlib_module_names) | SHIPPED_BY_HA | _declared_modules() | {
        "custom_components",
        "__future__",
    }
    unknown = {
        name: sorted(files) for name, files in _top_level_imports().items() if name not in allowed
    }

    assert not unknown, (
        "These imports are neither stdlib, shipped by Home Assistant, nor declared in "
        f"manifest.json requirements: {unknown}"
    )


def test_async_timeout_is_not_used():
    """asyncio.timeout (stdlib since 3.11) replaces it; HA no longer ships it."""
    assert "async_timeout" not in _top_level_imports()
