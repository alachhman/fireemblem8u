#!/usr/bin/env python3
"""Install or restore the source-only Eirika recolor portrait palette demo."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys


BASE_SHA256 = "57f5452cd80eab121de8a46287d522281c978c6ef0159b08740ff9837f7a3fe4"
PALETTE_RELATIVE_PATH = Path("graphics/portrait/portrait_Eirika_palette.agbpal")
VARIANT_RELATIVE_PATH = Path("assets/portrait_Eirika_palette_twilight.agbpal")

# GBA palette words, stored little-endian. Entries 7–10 are the cool hair
# ramp; 11–13 are the warm costume ramp. Skin, index 0, and pale highlights
# (14–15) remain byte-for-byte unchanged.
BASE_WORDS = (
    0x4F34, 0x6FDF, 0x473F, 0x2E7D, 0x25D3, 0x252C, 0x2087, 0x7763,
    0x62A2, 0x4145, 0x6162, 0x33FE, 0x235B, 0x10BA, 0x7353, 0x7FFE,
)
RECOLOR_WORDS = {
    7: 0x561A,  # mauve highlight
    8: 0x3D53,  # aubergine midtone
    9: 0x2488,  # deep plum shadow
    10: 0x356D,  # violet-blue shadow
    11: 0x3A1F,  # warm red highlight
    12: 0x311A,  # crimson midtone
    13: 0x24B1,  # dark crimson shadow
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def words_to_bytes(words: tuple[int, ...]) -> bytes:
    return b"".join(word.to_bytes(2, "little") for word in words)


def build_variant(source: bytes) -> bytes:
    if len(source) != 32:
        raise ValueError(f"Expected a 32-byte portrait palette; got {len(source)} bytes")
    if sha256(source) != BASE_SHA256:
        raise ValueError("Source palette hash does not match the recorded baseline")
    if source != words_to_bytes(BASE_WORDS):
        raise ValueError("Source palette words do not match the recorded baseline")

    result = bytearray(source)
    for index, word in RECOLOR_WORDS.items():
        result[index * 2 : index * 2 + 2] = word.to_bytes(2, "little")
    return bytes(result)


def print_values(before: bytes, after: bytes) -> None:
    print("Changed source palette entries (index: before -> after):")
    for index in RECOLOR_WORDS:
        old_word = int.from_bytes(before[index * 2 : index * 2 + 2], "little")
        new_word = int.from_bytes(after[index * 2 : index * 2 + 2], "little")
        print(f"  {index:2}: 0x{old_word:04X} -> 0x{new_word:04X}")


def run(command: str, repo: Path) -> int:
    target = repo / PALETTE_RELATIVE_PATH
    # The asset lives in assets/; resolve it relative to this script.
    bundled_variant = Path(__file__).resolve().parent / VARIANT_RELATIVE_PATH

    if not target.is_file():
        print(f"Missing source palette: {target}", file=sys.stderr)
        return 2
    current = target.read_bytes()

    if command == "apply":
        if sha256(current) == BASE_SHA256:
            expected = build_variant(current)
            if not bundled_variant.is_file() or bundled_variant.read_bytes() != expected:
                print("Bundled palette asset does not match the deterministic edit", file=sys.stderr)
                return 2
            target.write_bytes(expected)
            print_values(current, expected)
            print(f"Installed Eirika recolor palette at {target}")
            return 0
        if bundled_variant.is_file() and current == bundled_variant.read_bytes():
            print(f"Eirika recolor palette is already installed at {target}")
            return 0
        print("Source palette has changed; refusing to overwrite it", file=sys.stderr)
        return 2

    if command == "restore":
        if not bundled_variant.is_file():
            print(f"Missing bundled palette asset: {bundled_variant}", file=sys.stderr)
            return 2
        variant = bundled_variant.read_bytes()
        if current != variant:
            print("Installed palette does not match this demo; refusing to overwrite it", file=sys.stderr)
            return 2
        original = bytearray(current)
        for index, word in enumerate(BASE_WORDS):
            original[index * 2 : index * 2 + 2] = word.to_bytes(2, "little")
        restored = bytes(original)
        if sha256(restored) != BASE_SHA256:
            print("Restored palette failed its baseline hash check", file=sys.stderr)
            return 2
        target.write_bytes(restored)
        print_values(current, restored)
        print(f"Restored baseline palette at {target}")
        return 0

    # status is read-only and accepts only either known state.
    if sha256(current) == BASE_SHA256:
        print(f"Baseline palette present at {target}")
        return 0
    if bundled_variant.is_file() and current == bundled_variant.read_bytes():
        print(f"Eirika recolor palette installed at {target}")
        return 0
    print("Source palette matches neither the baseline nor this demo", file=sys.stderr)
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("apply", "restore", "status"))
    parser.add_argument("repo", type=Path, help="path to the FE8U checkout")
    args = parser.parse_args()
    return run(args.command, args.repo.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
