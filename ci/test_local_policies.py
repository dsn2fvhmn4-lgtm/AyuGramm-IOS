"""Run actual Foundation-only policies; UIKit gate is stubbed, not the policies under test."""
import argparse
import os
from pathlib import Path
import platform
import subprocess
import tempfile


def run(source: Path):
    source = source.resolve()
    with tempfile.TemporaryDirectory(prefix="ayu-local-policy-tests-") as tmp:
        tmp = Path(tmp)
        # These final enums depend only on Foundation. The sole Display gate stays off in tests.
        policy = "import Foundation\nenum AyuDecoyMode { static let isActive = false }\n"
        for file, marker in [("AyuPluginBadges.swift", "public enum AyuPluginChatFilter {"), ("AyuExtras.swift", "public enum AyuPaidAds {")]:
            text = (source / "submodules/Display/Source" / file).read_text()
            policy += text[text.index(marker):] + "\n"
        (tmp / "DisplayPolicies.swift").write_text(policy)
        swiftc = [os.environ["SWIFTC"]] if "SWIFTC" in os.environ else (["xcrun", "swiftc"] if platform.system() == "Darwin" else ["swiftc"])
        subprocess.run([*swiftc, "-swift-version", "5", "-warnings-as-errors",
                        str(source / "submodules/TelegramCore/Sources/AyuGram/AyuLocalNotificationSettings.swift"),
                        str(source / "submodules/TelegramCore/Sources/SyncCore/SyncCore_LoggedOutAccountAttribute.swift"),
                        str(tmp / "DisplayPolicies.swift"),
                        str(source / "tools/ayu-tests/local-policies/main.swift"), "-o", str(tmp / "tests")], check=True)
        subprocess.run([str(tmp / "tests")], check=True, timeout=30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    run(parser.parse_args().source)
