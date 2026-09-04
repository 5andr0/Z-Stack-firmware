#!/usr/bin/env python3
"""Strict validation for the flashable Sonoff ZBDongle-P Intel HEX image."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def parse_number(value: str) -> int:
    return int(value, 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--min-data-bytes", type=parse_number, default=0)
    parser.add_argument("--bootloader-config-address", type=parse_number)
    parser.add_argument(
        "--bootloader-config-bytes",
        help="four bytes in flash order, for example C50FFEC5",
    )
    args = parser.parse_args()

    raw = args.image.read_bytes()
    if not raw:
        raise SystemExit("Intel HEX image is empty")

    memory: dict[int, int] = {}
    upper_address = 0
    eof_count = 0
    record_count = 0

    for line_number, raw_line in enumerate(raw.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if eof_count:
            raise SystemExit(f"record found after EOF at line {line_number}")
        if not line.startswith(b":"):
            raise SystemExit(f"line {line_number} is not an Intel HEX record")

        try:
            record = bytes.fromhex(line[1:].decode("ascii"))
        except (UnicodeDecodeError, ValueError) as error:
            raise SystemExit(f"invalid hexadecimal data at line {line_number}: {error}")

        if len(record) < 5 or len(record) != record[0] + 5:
            raise SystemExit(f"invalid record length at line {line_number}")
        if sum(record) & 0xFF:
            raise SystemExit(f"checksum failure at line {line_number}")

        count = record[0]
        address = int.from_bytes(record[1:3], "big")
        record_type = record[3]
        data = record[4 : 4 + count]
        record_count += 1

        if record_type == 0x00:
            absolute = upper_address + address
            for offset, byte in enumerate(data):
                byte_address = absolute + offset
                previous = memory.get(byte_address)
                if previous is not None and previous != byte:
                    raise SystemExit(
                        f"conflicting data at address 0x{byte_address:08X}"
                    )
                memory[byte_address] = byte
        elif record_type == 0x01:
            if count or address:
                raise SystemExit(f"malformed EOF record at line {line_number}")
            eof_count += 1
        elif record_type == 0x02:
            if count != 2 or address:
                raise SystemExit(
                    f"malformed extended-segment-address record at line {line_number}"
                )
            upper_address = int.from_bytes(data, "big") << 4
        elif record_type == 0x04:
            if count != 2 or address:
                raise SystemExit(
                    f"malformed extended-linear-address record at line {line_number}"
                )
            upper_address = int.from_bytes(data, "big") << 16
        elif record_type in (0x03, 0x05):
            if count != 4 or address:
                raise SystemExit(f"malformed start-address record at line {line_number}")
        else:
            raise SystemExit(
                f"unsupported Intel HEX record type 0x{record_type:02X} "
                f"at line {line_number}"
            )

    if eof_count != 1:
        raise SystemExit(f"expected exactly one EOF record, found {eof_count}")
    if len(memory) < args.min_data_bytes:
        raise SystemExit(
            f"image contains only {len(memory)} data bytes; "
            f"expected at least {args.min_data_bytes}"
        )

    if (args.bootloader_config_address is None) != (
        args.bootloader_config_bytes is None
    ):
        raise SystemExit("bootloader address and bytes must be supplied together")

    if args.bootloader_config_address is not None:
        address = args.bootloader_config_address
        try:
            expected = bytes.fromhex(args.bootloader_config_bytes)
        except ValueError as error:
            raise SystemExit(f"invalid bootloader byte sequence: {error}")
        if len(expected) != 4:
            raise SystemExit("bootloader byte sequence must contain exactly four bytes")
        try:
            actual = bytes(memory[address + i] for i in range(4))
        except KeyError as error:
            missing = int(error.args[0])
            raise SystemExit(
                f"bootloader configuration is missing byte 0x{missing:08X}"
            )
        if actual != expected:
            raise SystemExit(
                f"bootloader configuration at 0x{address:08X} is {actual.hex().upper()}; "
                f"expected {expected.hex().upper()}"
            )

    lowest = min(memory)
    highest = max(memory)
    digest = hashlib.sha256(raw).hexdigest()
    print(
        f"Validated {args.image}: {record_count} records, {len(memory)} data bytes, "
        f"addresses 0x{lowest:08X}-0x{highest:08X}, sha256 {digest}"
    )


if __name__ == "__main__":
    main()
