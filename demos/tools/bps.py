#!/usr/bin/env python3
"""Small BPS1 writer/applicator for the independently playable showcase patches."""
import argparse
from pathlib import Path
import struct
import zlib


def number(n):
    out = bytearray()
    while True:
        x = n & 127
        n >>= 7
        if not n:
            out.append(x | 128)
            return out
        out.append(x)
        n -= 1


def read_number(data, pos):
    value, shift = 0, 1
    while True:
        x = data[pos]
        pos += 1
        value += (x & 127) * shift
        if x & 128:
            return value, pos
        shift <<= 7
        value += shift


def create(source, target, metadata=b''):
    patch = bytearray(b'BPS1') + number(len(source)) + number(len(target))
    patch += number(len(metadata)) + metadata
    pos = 0
    while pos < len(target):
        same = pos < len(source) and source[pos] == target[pos]
        end = pos + 1
        while end < len(target) and (end < len(source) and source[end] == target[end]) == same:
            end += 1
        # SourceRead (0) or TargetRead (1); no copy search is needed.
        patch += number(((end - pos - 1) << 2) | (0 if same else 1))
        if not same:
            patch += target[pos:end]
        pos = end
    patch += struct.pack('<II', zlib.crc32(source), zlib.crc32(target))
    patch += struct.pack('<I', zlib.crc32(patch))
    return bytes(patch)


def apply(source, patch):
    if len(patch) < 16 or patch[:4] != b'BPS1':
        raise ValueError('Not a BPS1 patch')
    if zlib.crc32(patch[:-4]) != struct.unpack('<I', patch[-4:])[0]:
        raise ValueError('Patch CRC mismatch')
    source_crc, target_crc = struct.unpack('<II', patch[-12:-4])
    if zlib.crc32(source) != source_crc:
        raise ValueError('Wrong source ROM (source CRC mismatch)')
    source_size, pos = read_number(patch, 4)
    target_size, pos = read_number(patch, pos)
    metadata_size, pos = read_number(patch, pos)
    pos += metadata_size
    if source_size != len(source):
        raise ValueError('Source size mismatch')
    out = bytearray()
    source_relative = target_relative = 0
    while pos < len(patch) - 12:
        action, pos = read_number(patch, pos)
        size, mode = (action >> 2) + 1, action & 3
        if mode == 0:
            out += source[len(out):len(out) + size]
        elif mode == 1:
            out += patch[pos:pos + size]
            pos += size
        else:
            offset, pos = read_number(patch, pos)
            delta = -(offset >> 1) if offset & 1 else offset >> 1
            if mode == 2:
                source_relative += delta
                if source_relative < 0 or source_relative + size > len(source):
                    raise ValueError('SourceCopy out of bounds')
                out += source[source_relative:source_relative + size]
                source_relative += size
            else:
                target_relative += delta
                if target_relative < 0 or target_relative >= len(out):
                    raise ValueError('TargetCopy out of bounds')
                for _ in range(size):
                    out.append(out[target_relative])
                    target_relative += 1
        if len(out) > target_size:
            raise ValueError('Target size exceeded')
    if pos != len(patch) - 12 or len(out) != target_size or zlib.crc32(out) != target_crc:
        raise ValueError('Target size/CRC mismatch')
    return bytes(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['create', 'apply'])
    parser.add_argument('source', type=Path)
    parser.add_argument('input', type=Path, help='target ROM when creating; BPS patch when applying')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.resolve() in (args.source.resolve(), args.input.resolve()):
        parser.error('Output must not overwrite either input')
    source, data = args.source.read_bytes(), args.input.read_bytes()
    result = create(source, data) if args.mode == 'create' else apply(source, data)
    if args.mode == 'create' and apply(source, result) != data:
        raise ValueError('Round-trip verification failed')
    args.output.write_bytes(result)
    print(f'{args.output}: {len(result):,} bytes')


if __name__ == '__main__':
    main()
