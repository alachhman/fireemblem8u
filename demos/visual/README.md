# Twilight Eirika

This demo recolors Eirika's normal dialogue portrait through its indexed 16-color GBA palette. It shifts the blue/cyan ramp at palette indices 7–10 toward aubergine and purple, and the warm costume ramp at 11–13 toward crimson. Palette indices 0–6 (including transparency and skin), plus the pale highlights at 14–15, stay unchanged.

The portrait is wired through `src/portrait_data.c` to `portrait_Eirika_palette`, and `src/data/data_portrait.c` includes `graphics/portrait/portrait_Eirika_palette.agbpal`. Start a new game and look for Eirika during the opening/prologue dialogue. The flashback portrait uses a separate palette and is not changed.

Apply the palette to a checkout with:

```sh
python3 demos/visual/install_twilight_eirika.py apply /path/to/fireemblem8u
```

The installer accepts only the recorded baseline palette hash (`57f5452cd80eab121de8a46287d522281c978c6ef0159b08740ff9837f7a3fe4`) or this demo's exact variant. It reports every changed index's before/after RGB555 word. To restore the baseline palette, run:

```sh
python3 demos/visual/install_twilight_eirika.py restore /path/to/fireemblem8u
```

Use `status` to check either state without writing. Exact before/after palette words and hashes are recorded in `manifest.json`; the modified 32-byte palette asset is in `assets/portrait_Eirika_palette_twilight.agbpal`.

See the [demo guide](../README.md) for the playable patch, before/after footage, and build runner.
