#!/usr/bin/env python3
"""Patch chromadb for Python 3.14 compatibility.

ChromaDB ≤1.4.1 has two issues on Python 3.14:
1. Uses pydantic.v1 compat layer (crashes on 3.14)
2. Three Settings fields lack type annotations (crashes pydantic v2)

This script patches chromadb/config.py in the venv to fix both.
Re-run after `pip install --upgrade chromadb` until PR #6356 is merged.

See: https://github.com/chroma-core/chroma/issues/5996
"""

import sys
from pathlib import Path

def patch():
    venv = Path(__file__).parent / ".venv"
    configs = list(venv.glob("lib/python*/site-packages/chromadb/config.py"))
    if not configs:
        print("chromadb/config.py not found in venv")
        return False

    config_path = configs[0]
    text = config_path.read_text()
    patched = False

    # Patch 1: Fix BaseSettings import to use pydantic-settings
    old_import = """in_pydantic_v2 = False
try:
    from pydantic import BaseSettings
except ImportError:
    in_pydantic_v2 = True
    from pydantic.v1 import BaseSettings
    from pydantic.v1 import validator

if not in_pydantic_v2:
    from pydantic import validator  # type: ignore # noqa"""

    new_import = """in_pydantic_v2 = False
try:
    from pydantic_settings import BaseSettings  # pydantic v2 + pydantic-settings
    in_pydantic_v2 = True
    from pydantic import validator  # type: ignore # noqa
except ImportError:
    try:
        from pydantic import BaseSettings  # pydantic v1
    except (ImportError, Exception):
        in_pydantic_v2 = True
        from pydantic.v1 import BaseSettings  # type: ignore
        from pydantic.v1 import validator  # type: ignore
    else:
        from pydantic import validator  # type: ignore # noqa"""

    if old_import in text:
        text = text.replace(old_import, new_import)
        patched = True
        print("  Patched: BaseSettings import -> pydantic-settings")

    # Patch 2: Add type annotations to 3 untyped fields
    annotations = {
        '    chroma_coordinator_host = "localhost"': '    chroma_coordinator_host: str = "localhost"',
        '    chroma_logservice_host = "localhost"': '    chroma_logservice_host: str = "localhost"',
        '    chroma_logservice_port = 50052': '    chroma_logservice_port: int = 50052',
    }
    for old, new in annotations.items():
        if old in text:
            text = text.replace(old, new)
            patched = True
            field = old.split("=")[0].strip()
            print(f"  Patched: {field} -> added type annotation")

    if patched:
        config_path.write_text(text)
        print(f"Saved: {config_path}")
        return True
    else:
        print("Already patched or different chromadb version")
        return False


if __name__ == "__main__":
    print("Patching chromadb for Python 3.14 compatibility...")
    if patch():
        print("Done. ChromaDB should now import on Python 3.14.")
    else:
        print("No changes needed.")
