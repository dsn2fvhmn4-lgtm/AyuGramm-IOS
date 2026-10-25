# AyuGram iOS artwork

`AyuGram-logo.png` is the owner-provided Apple/airplane artwork with the exterior black surround removed and real alpha transparency around its purple rounded square. It is suitable for the project README and channel artwork. The original upload is preserved separately by the owner.

The native app uses a separate full-bleed PNG in `Telegram/Telegram-iOS/Telegram.icon/Assets/AyuGram.png`, delivered inside `patches/ayugram-ghost-mode.patch`. Its purple background fills the square, with no black surround or pre-applied rounded mask. Icon Composer applies the platform mask. The previous foreground/watch scaling overrides were removed for this complete artwork layer.

Both generated assets are 1254 × 1254 pixels. The standalone logo is RGBA with transparent exterior; the app artwork is opaque RGB. No source image resizing is performed in the CI pipeline. The PNG resource is included by the existing native `.icon/**/*` resource glob.

Local verification covers PNG decoding/integrity, alpha/background properties, JSON asset references and applying the binary patch to pinned upstream source. Native Icon Composer compilation and iPhone rendering remain pending the owner's manual Codemagic build. The published build 8 IPA still has the previous artwork.
