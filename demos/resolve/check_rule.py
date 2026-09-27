#!/usr/bin/env python3
"""Compile and compare the original and patched FE8U attack calculation."""

from __future__ import annotations

import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import sys


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATCH = Path(__file__).with_name("source.patch")
BASE_REVISION = "d28f4241"
FUNCTION_MARKER = "void ComputeBattleUnitAttack("


HARNESS_PREFIX = r"""
#include <stdio.h>
#include <stdlib.h>

typedef signed char s8;
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;

enum {
    CHARACTER_EIRIKA = 1,
    CHARACTER_SETH = 2,
};

enum {
    ITEM_TEST_SWORD = 10,
    ITEM_TEST_EFFECTIVE_SWORD = 11,
    ITEM_SWORD_AUDHULMA = 20,
    ITEM_LANCE_VIDOFNIR = 21,
    ITEM_AXE_GARM = 22,
    ITEM_BOW_NIDHOGG = 23,
    ITEM_ANIMA_EXCALIBUR = 24,
    ITEM_LIGHT_IVALDI = 25,
    ITEM_SWORD_SIEGLINDE = 26,
    ITEM_LANCE_SIEGMUND = 27,
    ITEM_MONSTER_STONE = 30,
};

#define TRUE 1

struct CharacterData {
    u8 number;
};

struct Unit {
    struct CharacterData *pCharacterData;
    s8 curHP;
    s8 maxHP;
    s8 pow;
    u8 unitEffective;
    u8 itemEffective;
};

struct BattleUnit {
    struct Unit unit;
    u16 weapon;
    s8 wTriangleDmgBonus;
    s16 battleAttack;
};

#define UNIT_CHAR_ID(unit) ((unit)->pCharacterData->number)

int GetItemMight(u16 item);
u16 GetItemIndex(u16 item);
int IsUnitEffectiveAgainst(struct Unit *attacker, struct Unit *defender);
int IsItemEffectiveAgainst(u16 item, struct Unit *defender);

int GetItemMight(u16 item) {
    if (item == ITEM_SWORD_SIEGLINDE)
        return 8;
    if (item == ITEM_MONSTER_STONE)
        return 7;
    return 5;
}

u16 GetItemIndex(u16 item) {
    return item;
}

int IsUnitEffectiveAgainst(struct Unit *attacker, struct Unit *defender) {
    (void) attacker;
    return defender->unitEffective;
}

int IsItemEffectiveAgainst(u16 item, struct Unit *defender) {
    (void) item;
    return defender->itemEffective;
}
"""


HARNESS_SUFFIX = r"""
void ComputeBattleUnitAttack_original(struct BattleUnit *, struct BattleUnit *);
void ComputeBattleUnitAttack_patched(struct BattleUnit *, struct BattleUnit *);

struct TestCase {
    const char *name;
    int characterId;
    int curHP;
    int maxHP;
    u16 weapon;
    int triangleBonus;
    int unitEffective;
    int itemEffective;
    int expectedOriginal;
    int expectedDelta;
};

static const struct TestCase sCases[] = {
    {"eirika-full-normal", CHARACTER_EIRIKA, 16, 16, ITEM_TEST_SWORD, 1, 0, 0, 9, 0},
    {"eirika-one-above-half", CHARACTER_EIRIKA, 9, 16, ITEM_TEST_SWORD, 1, 0, 0, 9, 0},
    {"eirika-exact-half", CHARACTER_EIRIKA, 8, 16, ITEM_TEST_SWORD, 1, 0, 0, 9, 4},
    {"eirika-below-half", CHARACTER_EIRIKA, 7, 16, ITEM_TEST_SWORD, 1, 0, 0, 9, 4},
    {"eirika-zero-hp", CHARACTER_EIRIKA, 0, 16, ITEM_TEST_SWORD, 1, 0, 0, 9, 4},
    {"seth-exact-half", CHARACTER_SETH, 8, 16, ITEM_TEST_SWORD, 1, 0, 0, 9, 0},
    {"eirika-odd-max-at-floor-half", CHARACTER_EIRIKA, 8, 17, ITEM_TEST_SWORD, 1, 0, 0, 9, 4},
    {"eirika-odd-max-above-half", CHARACTER_EIRIKA, 9, 17, ITEM_TEST_SWORD, 1, 0, 0, 9, 0},
    {"eirika-half-unit-effective", CHARACTER_EIRIKA, 8, 16, ITEM_TEST_SWORD, 1, 1, 0, 21, 4},
    {"eirika-half-item-effective", CHARACTER_EIRIKA, 8, 16, ITEM_TEST_EFFECTIVE_SWORD, 1, 0, 1, 21, 4},
    {"eirika-half-sieg-linde-effective", CHARACTER_EIRIKA, 8, 16, ITEM_SWORD_SIEGLINDE, 1, 0, 1, 21, 4},
    {"eirika-full-sieg-linde-effective", CHARACTER_EIRIKA, 16, 16, ITEM_SWORD_SIEGLINDE, 1, 0, 1, 21, 0},
    {"eirika-half-monster-stone", CHARACTER_EIRIKA, 8, 16, ITEM_MONSTER_STONE, 1, 0, 0, 0, 0},
};

static int RunCase(const struct TestCase *testCase) {
    struct CharacterData character = {(u8) testCase->characterId};
    struct BattleUnit original = {0};
    struct BattleUnit patched = {0};
    struct BattleUnit defender = {0};
    int delta;

    original.unit.pCharacterData = &character;
    original.unit.curHP = (s8) testCase->curHP;
    original.unit.maxHP = (s8) testCase->maxHP;
    original.unit.pow = 3;
    original.weapon = testCase->weapon;
    original.wTriangleDmgBonus = (s8) testCase->triangleBonus;
    defender.unit.unitEffective = (u8) testCase->unitEffective;
    defender.unit.itemEffective = (u8) testCase->itemEffective;
    patched = original;

    ComputeBattleUnitAttack_original(&original, &defender);
    ComputeBattleUnitAttack_patched(&patched, &defender);

    delta = patched.battleAttack - original.battleAttack;
    if (original.battleAttack != testCase->expectedOriginal
        || delta != testCase->expectedDelta
        || patched.battleAttack != testCase->expectedOriginal + testCase->expectedDelta) {
        fprintf(stderr,
            "FAIL %s: original=%d patched=%d delta=%d expected-original=%d expected-delta=%d\n",
            testCase->name,
            original.battleAttack,
            patched.battleAttack,
            delta,
            testCase->expectedOriginal,
            testCase->expectedDelta);
        return 1;
    }

    printf("PASS %s: original=%d patched=%d delta=%d\n",
        testCase->name, original.battleAttack, patched.battleAttack, delta);
    return 0;
}

int main(void) {
    unsigned int i;
    int failures = 0;

    for (i = 0; i < sizeof(sCases) / sizeof(sCases[0]); ++i)
        failures += RunCase(&sCases[i]);

    if (failures != 0)
        return EXIT_FAILURE;

    printf("PASS all %u host-C cases\n", (unsigned int) (sizeof(sCases) / sizeof(sCases[0])));
    return EXIT_SUCCESS;
}
"""


def git_bytes(*args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def extract_function(source: str) -> str:
    start = source.find(FUNCTION_MARKER)
    if start < 0:
        raise RuntimeError(f"could not find {FUNCTION_MARKER!r}")

    opening = source.find("{", start)
    if opening < 0:
        raise RuntimeError("function has no opening brace")

    depth = 0
    for offset in range(opening, len(source)):
        if source[offset] == "{":
            depth += 1
        elif source[offset] == "}":
            depth -= 1
            if depth == 0:
                return source[start : offset + 1]

    raise RuntimeError("function body has no matching closing brace")


def renamed_function(source: str, new_name: str) -> str:
    function = extract_function(source)
    return function.replace(FUNCTION_MARKER, f"void {new_name}(", 1)


def compile_and_run(compiler: str) -> None:
    base_source = git_bytes("show", f"{BASE_REVISION}:src/bmbattle.c").decode("utf-8")
    baseline_function = renamed_function(base_source, "ComputeBattleUnitAttack_original")

    with tempfile.TemporaryDirectory(prefix="resolve-rule-") as temp_name:
        temp_root = Path(temp_name)
        temp_source = temp_root / "src" / "bmbattle.c"
        temp_source.parent.mkdir(parents=True)
        temp_source.write_text(base_source, encoding="utf-8")

        subprocess.run(["git", "init", "--quiet", str(temp_root)], check=True)
        subprocess.run(
            ["git", "-C", str(temp_root), "add", "--", "src/bmbattle.c"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(temp_root), "apply", "--check", str(SOURCE_PATCH)],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(temp_root), "apply", str(SOURCE_PATCH)],
            check=True,
        )

        patched_source = temp_source.read_text(encoding="utf-8")
        patched_function = renamed_function(patched_source, "ComputeBattleUnitAttack_patched")
        c_source = temp_root / "check_rule.c"
        executable = temp_root / "check_rule"
        c_source.write_text(
            HARNESS_PREFIX + "\n" + baseline_function + "\n" + patched_function + "\n" + HARNESS_SUFFIX,
            encoding="utf-8",
        )

        subprocess.run(
            [*shlex.split(compiler), "-std=c99", "-Wall", "-Wextra", "-Werror", str(c_source), "-o", str(executable)],
            check=True,
        )
        subprocess.run([str(executable)], check=True)


def main() -> int:
    compiler = os.environ.get("CC") or shutil.which("cc") or shutil.which("clang")
    if not compiler:
        print("No C compiler found; set CC to a host C compiler.", file=sys.stderr)
        return 2
    if not SOURCE_PATCH.is_file():
        print(f"Missing source patch: {SOURCE_PATCH}", file=sys.stderr)
        return 2

    try:
        compile_and_run(compiler)
    except subprocess.CalledProcessError as error:
        print(f"command failed with exit status {error.returncode}: {error.cmd}", file=sys.stderr)
        if error.stderr:
            print(error.stderr.decode("utf-8", errors="replace"), file=sys.stderr)
        return error.returncode or 1
    except (OSError, RuntimeError, UnicodeError) as error:
        print(f"harness setup failed: {error}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
