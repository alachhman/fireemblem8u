# Resolve: Eirika’s prf ability

Resolve is Eirika’s **prf ability**: she gains **+4 attack** when `2 * curHP <= maxHP`. The inclusive comparison handles odd maximum HP without rounding. The bonus is added after weapon effectiveness and before the existing Monster Stone override. It affects forecast and combat calculations, including Eirika's counterattacks; other characters receive no bonus.

The published patch combines three readable changes:

- [source.patch](source.patch): the four-line prf ability check in `ComputeBattleUnitAttack`.
- [encounter.patch](encounter.patch): a Prologue training fixture, setting Eirika to 8/16 HP and a nearby fighter to 11 HP, and moving that fighter to (6,6).
- [layout.patch](layout.patch): supports the changed source layout in the demo build. It removes the matching-only absolute sound-entry address pin while preserving relative position, size and alignment checks. It derives the duplicate-object copy addresses from fresh symbols, with bounded relocation checks. The tested build shifts the relevant data by 56 bytes and earlier read-only data by 32 bytes.

These changes are applied only by the [demo build runner](../build.py) in the selected checkout. The repository's default baseline keeps its original matching rules. The prf ability can be studied separately from the training fixture, but a source build with changed code still needs the layout support.

## Play the encounter

Apply [resolve.bps](../releases/resolve.bps) to a clean baseline and start a new Normal-mode game. At the first player phase, select Eirika, move two tiles right, then choose Attack against the fighter below her. The recorded forecast shows 9 damage per strike against this fighter on mountain terrain. The captured fight defeats the fighter and returns to the map with Eirika still at 8 HP. Different input timing may produce different combat rolls.

![Actual emulator capture](../media/resolve.gif)

## Boundary checks

Run `python3 demos/resolve/check_rule.py` from the repository root. The harness extracts the actual C function before and after the source patch, compiles it with host stubs, and checks 13 cases: full/half/above/below/zero HP, odd maximum HP, another character, effectiveness interactions, Sieglinde, and the Monster Stone override. Zero HP satisfies the arithmetic rule, although defeated units cannot initiate normal combat.

The host tests verify the bounded combat calculation; the footage verifies one playable opening encounter. Neither substitutes for a full campaign regression test.
