# Balance demo

`source.patch` targets FE8U baseline `d28f4241ad4a64f93707a7db7d4c325847d8a123`.
From the FE8U source root, apply it with `git apply demos/balance/source.patch`.

The patch makes five small balance changes:

| Value | Before | After |
| --- | ---: | ---: |
| Iron Sword might | 5 | 6 |
| Rapier might | 7 | 9 |
| Rapier hit | 95 | 105 |
| Eirika HP growth | 70% | 80% |
| Eirika power/strength growth | 40% | 50% |

To see the weapon remix in play, build the patched source, start a new Eirika route,
and play the Prologue through the opening movement tutorial. Seth gives Eirika the
Rapier there; inspect it in her inventory to see its updated might and hit. The Iron
Sword change applies wherever that weapon appears. Eirika's growth changes affect
future level-ups and are not directly shown in the Prologue.

The patch changes only those five numeric fields; the Rapier's effectiveness,
critical rate, weight, durability, and other item data stay as before.

See the [demo guide](../README.md) for the downloadable patch and reversible build runner. The real inventory comparison confirms attack 11 → 13 and hit 113 → 123; growth rates are source changes and were not statistically playtested.
