# Real emulator captures

The GIFs and silent MP4s are mGBA software framebuffer captures, rendered from the compiled demo ROMs. There are no synthetic game frames or RAM edits. Labels and side-by-side composition were added outside the game viewport; pixels were enlarged with nearest-neighbor scaling. Output is 20 fps, sampling every third emulator frame (nominal 60 Hz). The comparison clips last 3 seconds; Resolve shows movement, forecast and combat, then returns to the map.

mGBA version: **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`.

Build mGBA's static library with frontends/dependencies disabled, then compile [capture.c](../tools/capture.c) against its include directories and `libmgba.a`. On the tested macOS host, linking additionally required `-lm -lpthread -framework CoreFoundation -framework OpenGL`. No emulator binary is bundled.

The capture runner accepts a ROM, input state (`-` for a fresh reset), and output state (`-` to skip saving). Input scripts contain frame counts and hexadecimal GBA key masks: A=1, Start=8, Right=10, Down=80, R=100. `step N MASK` advances the real emulator, `dump PATH.ppm` saves a framebuffer, and `video PATH.rgba` records subsequent steps as 240×160 RGBA frames. `record N MASK PATH.rgba` records a fixed segment. Start without an external save file for reproducibility.

- `portrait.txt`: reaches the opening portrait dialogue; record 180 idle frames afterward for original and visual variants.
- `inventory.txt`: reaches Eirika's inventory; record 180 idle frames afterward for original and balance variants.
- `resolve.txt`: reaches the first player phase, approaches the training fighter and resolves combat. The published clip begins after the common `prologue.txt` prefix.

The scripts use only ordinary controller input. The runner also exposes memory diagnostics for development, but none were used to alter the recorded game state. Recorded Resolve inputs produce a successful fight; other input sequences can change the random-number state.
