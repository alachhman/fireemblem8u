# Quick Start

This guide covers building the source tree and checking the resulting ROM image. The build does not need a copy of the original game: tracked assets and the expected checksum are included in the repository.

## Restore the embedded payload on a fresh clone

The FE6 serial-link payload is a Git submodule with a locally pinned source revision. That revision is stored in the repository's source-only bundle and may not be available from the submodule's upstream remote. On a fresh checkout, run the restore helper from the repository root:

```sh
python3 tools/mgfembp-source/restore.py
```

The helper initializes or clones the configured submodule, fetches the pinned commit from the local bundle if needed, and checks it out. It stops if the submodule contains uncommitted changes. A plain `git submodule update --init` does not fetch the local bundle commit.

Run this helper before `scripts/quickstart.sh`: that script performs a regular submodule update before it reaches the build. The Makefile also calls the helper automatically when `mgfembp/Makefile` is missing.

## Build

The convenience script can install common system packages on apt, pacman, or Homebrew systems, install Python image libraries, and clone/build agbcc if it is missing:

```sh
./scripts/quickstart.sh
```

The original ROM is optional. To copy one into the checkout for `asmdiff.sh`, pass `--rom /path/to/baserom.gba` or set `FIREEMBLEM8U_ROM`. The `--refresh-agbcc` option forces the helper to fetch and rebuild agbcc from the current `pret/agbcc` `origin/master`; it is not a pinned source revision. By default an existing `tools/agbcc` install is reused.

If dependencies are already installed, the equivalent manual build is:

```sh
./build_tools.sh
make -j4 compare
```

The output is `fireemblem8.gba`. The `compare` target checks its SHA-1 against `checksum.sha1`; on macOS it uses `shasum`, and on other systems it uses `sha1sum`.

## Toolchain notes

Most game C files use agbcc. Selected matching routines use an isolated GNU ARM GCC 16.2.0 backend that Make builds under the ignored `.deps/gcc16-matching/` directory. The backend builder downloads GCC source from GNU, verifies its pinned SHA-256, applies the repository's checked backend changes, then builds the compiler and matching plugins. The first full build therefore includes this compiler bootstrap and can need substantially more time and disk space than an incremental build. No fixed time or disk estimate is published here.

The current backend bootstrap targets Apple Silicon macOS. It expects `clang`, `clang++`, `make`, and `tar`, along with Homebrew GMP, MPFR, MPC, ISL, and ARM binutils under `/opt/homebrew`. The convenience script's package-manager setup does not install all of these backend prerequisites. Other systems may need adjustments to `tools/arm-dispatch/build_backend.py` and their compiler dependencies before the matching build works.

The FE6 payload has its own pinned agbcc variant. Its compiler installer and payload sources come from the restored submodule revision; the first payload build may bootstrap that compiler too.

The convenience script calls `nproc` and `sha1sum` directly. If those command names are unavailable on your system, install compatible command-line tools or use the manual `make -j4 compare` path after dependencies are ready.

## Common setup issues

- **Missing `png.h`:** install the libpng development package, then rerun `./build_tools.sh`.
- **Payload submodule cannot be checked out:** run `python3 tools/mgfembp-source/restore.py` from the repository root. Check that `mgfembp/` has no local modifications if the helper refuses to proceed.
- **Missing ARM tools:** install an ARM GNU toolchain that provides `arm-none-eabi-as`, `ld`, `objcopy`, `cpp`, and `gcc`.
- **Pinned GCC bootstrap fails:** check the host compiler and library paths described above. The backend build log is under `.deps/gcc16-matching/`.
