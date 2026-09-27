#!/usr/bin/env python3
"""Build one independent showcase in a prepared checkout, then restore its baseline."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

DEMO = Path(__file__).resolve().parent
sys.path.insert(0, str(DEMO / 'tools'))
from bps import create, apply
BASE_SHA1 = 'c25b145e37456171ada4b0d440bf88a19f4d509f'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('variant', choices=['balance', 'resolve', 'visual'])
    p.add_argument('--checkout', type=Path, required=True,
                   help='Prepared build checkout; affected sources must match the baseline')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--jobs', type=int, default=4)
    p.add_argument('--flips', type=Path, help='Optional Floating IPS executable for compact BPS delta patches')
    args = p.parse_args()
    root, out = args.checkout.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    patches = [] if args.variant == 'visual' else [DEMO / args.variant / 'source.patch']
    if args.variant == 'resolve':
        patches += [DEMO / 'resolve/layout.patch', DEMO / 'resolve/encounter.patch']
    paths = set()
    for patch in patches:
        paths.update(re.findall(r'^\+\+\+ b/(.+)$', patch.read_text(), re.M))
    if args.variant == 'visual':
        paths.add('graphics/portrait/portrait_Eirika_palette.agbpal')
    paths.add('docs/orphan-object-rebuild.json')
    if any(Path(path).is_absolute() or '..' in Path(path).parts for path in paths):
        raise SystemExit('Unexpected patch path')
    backups = {path: (root / path).read_bytes() for path in paths}
    env = os.environ.copy()
    for var in ('C_INCLUDE_PATH', 'CPATH', 'CPLUS_INCLUDE_PATH'):
        env.pop(var, None)
    def build(logname, target):
        with (out / logname).open('w') as log:
            subprocess.run(['make', f'-j{args.jobs}', target], cwd=root, env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
    build(args.variant + '-baseline.log', 'compare')
    original = (root / 'fireemblem8.gba').read_bytes()
    if hashlib.sha1(original).hexdigest() != BASE_SHA1:
        raise SystemExit('Checkout is not the verified matching baseline')
    try:
        for patch in patches:
            subprocess.run(['git', 'apply', '--check', str(patch)], cwd=root, check=True)
            subprocess.run(['git', 'apply', str(patch)], cwd=root, check=True)
        if args.variant == 'visual':
            subprocess.run([sys.executable, str(DEMO / 'visual/install_twilight_eirika.py'),
                            'apply', str(root)], check=True)
        build(args.variant + '-build.log', 'fireemblem8.gba')
        target = (root / 'fireemblem8.gba').read_bytes()
        if target == original:
            raise RuntimeError('Demo produced no ROM changes')
        metadata = json.dumps({'demo': args.variant, 'source': 'alachhman/fireemblem8u',
                               'baseline_sha1': BASE_SHA1}, separators=(',', ':')).encode()
        (out / (args.variant + '.gba')).write_bytes(target)
        if args.flips:
            baseline_file = out / 'baseline.gba'
            baseline_file.write_bytes(original)
            patch_file = out / (args.variant + '.bps')
            subprocess.run([str(args.flips.resolve()), '--create', '--bps-delta',
                            str(baseline_file), str(out / (args.variant + '.gba')),
                            str(patch_file)], check=True)
            patch_data = patch_file.read_bytes()
        else:
            patch_data = create(original, target, metadata)
        if apply(original, patch_data) != target:
            raise RuntimeError('BPS application does not reproduce the built target')
        (out / (args.variant + '.elf')).write_bytes((root / 'fireemblem8.elf').read_bytes())
        (out / (args.variant + '.map')).write_bytes((root / 'fireemblem8.map').read_bytes())
        (out / (args.variant + '.bps')).write_bytes(patch_data)
        receipt = {'variant': args.variant, 'source_sha1': BASE_SHA1,
                   'target_sha1': hashlib.sha1(target).hexdigest(), 'target_sha256': sha(target),
                   'target_bytes': len(target), 'patch_sha256': sha(patch_data),
                   'patch_bytes': len(patch_data), 'bps_round_trip': True,
                   'patch_encoder': 'Floating IPS BPS delta' if args.flips else 'portable BPS linear',
                   'source_patches': {str(x.relative_to(DEMO)): sha(x.read_bytes()) for x in patches}}
    finally:
        for path, content in backups.items():
            (root / path).write_bytes(content)
        build(args.variant + '-restored.log', 'compare')
        # The generator's receipt includes a checkout-specific output path.
        (root / 'docs/orphan-object-rebuild.json').write_bytes(backups['docs/orphan-object-rebuild.json'])
    receipt['baseline_restored_and_compared'] = True
    (out / (args.variant + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
