# In-app logo previews

`Brand.png`, `Blue.png` and `Graphite.png` are 300 × 300 RGBA previews of the
corresponding full-resolution Icon Composer artwork. The original source hashes,
dimensions and file sizes are in `manifest.json`.

They were resized from 1254 × 1254 with Pillow's Lanczos resampler, keeping the
embedded colour profile if present, and saved as optimized PNGs. `ci/prepare.py`
installs them into the three VoidGram image sets with a `3x` scale.

The largest in-app use is the 100 pt settings header; the picker uses up to 72 pt,
Telegram's theme picker uses 63 pt, and update information uses 62 pt. These previews
therefore cover the largest use at 3 pixels per point. If a larger view is added,
regenerate them at that view's maximum size × 3.

The three files total 223,145 bytes, down from 4,188,615 bytes. Their uncompressed
RGBA pixel storage totals 1,080,000 bytes instead of 18,870,192. These are resource
and pixel-buffer figures, not a measured reduction of the compiled asset catalog
or an Instruments memory measurement.
