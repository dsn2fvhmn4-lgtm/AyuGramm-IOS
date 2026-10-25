# Original AyuGram icon presets

The native source patch includes original artwork copied from AyuGram Desktop's
`Telegram/Resources/art/ayu/<id>/app.svg` or `app.png`. The picker order comes from
`Telegram/SourceFiles/ayu/ui/components/icon_picker.cpp`:

1. default
2. alt
3. discord
4. spotify
5. extera
6. nothing
7. bard
8. yaplus
9. win95
10. chibi
11. chibi2
12. extera2

Original project: [AyuGram Desktop](https://github.com/AyuGram/AyuGramDesktop).
Original AyuGram attribution, including Radolyn and the upstream project's artwork
contributors, is retained. These are upstream presets, not newly generated artwork.
The SVG/PNG bytes are unchanged. Corresponding upstream `AppIcon-*.icon` layer
scale and position are retained in the iOS bundles; platform/background metadata
is adapted for the iOS target.

The owner's three Apple/airplane variants remain separate choices. The shared
native `AyuAppIconCatalog` supplies all fifteen choices to both SettingsUI and the
application icon bindings. The generated Blue/Graphite prompts remain documented
in [variant-prompts.md](variant-prompts.md).
