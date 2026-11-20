# Composition workflow storyboards

The [editable scenario manifest](../visual/storyboards.json) follows a shared
synthetic task, host, native session, artifact, trace and clock across these
references. The [contact sheet](../visual/reference/contact-sheet.png) shows the
complete sequence. Use the [standalone HTML](../visual/reference/index.html)
locally for the responsive layout and keyboard navigation.

| Scenario | Reference | Review focus |
| --- | --- | --- |
| [H01](https://github.com/newdarwindev/runspindle/issues/8) | [Progress](../visual/reference/h01.png) | Duplicate intake, native identity and interrupted progress |
| [H06](https://github.com/newdarwindev/runspindle/issues/13) | [Takeover](../visual/reference/h06.png) | Passive viewing, denied takeover and interrupted handback |
| [H07](https://github.com/newdarwindev/runspindle/issues/14) | [Artifact receipt](../visual/reference/h07.png) | Exact acceptance, uncertain delivery and independent readback |
| [H09](https://github.com/newdarwindev/runspindle/issues/16) | [Fleet](../visual/reference/h09.png) | Fresh, stale and disconnected observations |
| [H08](https://github.com/newdarwindev/runspindle/issues/15) | [Telemetry](../visual/reference/h08.png) | The Console model for queue, export, persistence and readback |

Each frame names its canonical Tether or Console state. The renderer checks
those states at their recorded commits. Tether screenshots are linked in place.
The Console visual family comes from a separate exact visual reference commit
because the runtime gitlink predates it. Composition's seven runtime pins
remain the pins recorded in `composition.lock.json`.

## Reproduce or compare

Initialize the composition submodules. Keep a local clone of
`newdarwindev/runspindle-console` containing the reference commit from the
manifest. Use Python 3.13 with `requirements-visual.txt`, and a local
Chromium headless-shell binary matching the render profile. The profile
records the platform, browser hash, font hashes, viewport, locale and device
scale used for this candidate. Other render stacks need a separate reviewed
profile and comparison.

```sh
python3 tools/render_storyboards.py \
  --console-source /path/to/console \
  --browser /path/to/chrome-headless-shell \
  --output /path/to/empty/scratch \
  --compare visual/reference
```

The command requires committed rendering inputs, denies external page requests,
and verifies two independent renders before writing outputs to the empty
directory. It checks 320, 390, 768 and 1440 px widths, keyboard focus and
activation, and long content at 200% CSS zoom. A deliberately wide frame must
fail the layout check. The [repeat diff](../visual/reference/repeat-diff.png)
records the zero-pixel comparison. Remove the scratch directory after review.

The [evidence manifest](../visual/reference/evidence.json) includes a later
actual-render slot for each story. Review approval is pending. Actual-product
screenshots, keyboard audit of the implemented product, document slide review,
runtime behavior and live acceptance are separate evidence.
