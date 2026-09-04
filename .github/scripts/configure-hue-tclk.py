#!/usr/bin/env python3
"""Install the Hue/ZLL commissioning trust-center key in preinclude.h.

The key is supplied through HUE_TCLK_HEX so it does not need to be committed
to the public firmware repository.  Its SHA-256 fingerprint is checked against
the independently published fingerprint before it can enter a build.
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path


EXPECTED_TEXT_FINGERPRINT = (
    "ce574642a3a8959b344796591321a155ae3bd25e4f5668602f6a33c06adbdf33"
)
HEADER_GUARD_END = "#endif /* HUE_ROUTER_PREINCLUDE_H_ */"
KEY_MACRO = "HUE_TCLK_KEY"


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} PREINCLUDE_H", file=sys.stderr)
        return 2

    raw_key = os.environ.get("HUE_TCLK_HEX", "")
    compact_key = re.sub(r"[^0-9A-Fa-f]", "", raw_key)
    if len(compact_key) != 32:
        print(
            "HUE_TCLK_HEX must contain exactly 16 hexadecimal bytes",
            file=sys.stderr,
        )
        return 2

    key_bytes = bytes.fromhex(compact_key)
    canonical_key = ":".join(f"{byte:02X}" for byte in key_bytes)
    fingerprint = hashlib.sha256((canonical_key + "\n").encode("ascii")).hexdigest()
    if fingerprint != EXPECTED_TEXT_FINGERPRINT:
        print(
            "HUE_TCLK_HEX does not match the published Hue/ZLL commissioning "
            "trust-center-key fingerprint",
            file=sys.stderr,
        )
        return 2

    header_path = Path(sys.argv[1])
    header = header_path.read_text(encoding="utf-8")
    if header.count(HEADER_GUARD_END) != 1:
        print(f"Could not find the preinclude header guard in {header_path}", file=sys.stderr)
        return 2

    if KEY_MACRO in header:
        print(f"{KEY_MACRO} is already defined in {header_path}", file=sys.stderr)
        return 2

    initializer = ",".join(f"0x{byte:02x}" for byte in key_bytes)
    key_define = (
        "// Hue Bridge classical commissioning uses the ZLL pre-installed TCLK.\n"
        f"#define {KEY_MACRO} {{{initializer}}}\n\n"
    )
    header = header.replace(HEADER_GUARD_END, key_define + HEADER_GUARD_END)
    header_path.write_text(header, encoding="utf-8", newline="\n")
    print("Configured verified Hue/ZLL commissioning trust-center key")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
