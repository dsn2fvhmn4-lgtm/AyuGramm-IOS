import json
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class SupporterBadgeTests(unittest.TestCase):
    def test_compact_seed_keeps_custom_badge_metadata(self):
        data = json.loads((ROOT / "assets" / "ayu_supporters_seed.json").read_text())
        badges = {item["id"]: item["badge"] for item in data["customBadges"]}

        self.assertEqual(badges[1226061708]["documentId"], 5266966399934291023)
        self.assertIn("text", badges[1226061708])
        self.assertIn(5800413909, data["developers"])

    def test_port_preserves_badge_types_and_premium_slot(self):
        patch = (ROOT / "patches" / "ayugram-custom-features.patch").read_text()

        self.assertIn('json["customBadges"]', patch)
        self.assertIn('json["supporterChannels"]', patch)
        self.assertIn("case custom(documentId: Int64, text: String?)", patch)
        self.assertIn("statusIcon = credibilityIcon", patch)
        self.assertIn("titleStatusIcon = .premium", patch)
        self.assertIn("currentStatusIconContent = currentCredibilityIconContent", patch)

    def test_static_badge_assets_use_centerable_square_canvases(self):
        expected = {
            "extera_badge.png": (16, 16),
            "extera_badge@2x.png": (32, 32),
            "extera_badge@3x.png": (48, 48),
        }

        for name, size in expected.items():
            data = (ROOT / "assets" / "branding" / "ExteraBadge.imageset" / name).read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", data[16:24]), size)

        developer_expected = {
            "extera_developer_badge.png": (16, 16),
            "extera_developer_badge@2x.png": (32, 32),
            "extera_developer_badge@3x.png": (48, 48),
        }
        for name, size in developer_expected.items():
            data = (ROOT / "assets" / "branding" / "ExteraDeveloperBadge.imageset" / name).read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", data[16:24]), size)

    def test_developer_and_supporter_badges_use_distinct_assets(self):
        patch = (ROOT / "patches" / "ayugram-custom-features.patch").read_text()

        self.assertIn("case exteraDeveloper", patch)
        self.assertIn('case .developer:', patch)
        self.assertIn('AyuGram/ExteraDeveloperBadge', patch)
        self.assertIn('case .supporter:', patch)
        self.assertIn('AyuGram/ExteraBadge', patch)

    def test_ios_developer_registry_has_unique_valid_entries(self):
        registry = json.loads((ROOT / "assets" / "ayugram_ios_badges.json").read_text())
        badges = registry["badges"]
        ids = [badge["id"] for badge in badges]

        self.assertEqual(registry["version"], 1)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(badge["documentId"] > 0 and badge["title"] for badge in badges))
        by_id = {badge["id"]: badge for badge in badges}
        self.assertEqual(by_id[8276132300]["documentId"], 5341356487631448969)
        self.assertEqual(by_id[7556953433]["documentId"], 5208467231670812677)
        self.assertEqual(by_id[7864640050]["documentId"], 5341356487631448969)
        self.assertTrue(all("(name)" in by_id[user_id]["title"] for user_id in (8276132300, 7556953433, 7864640050)))

    def test_followup_patch_has_conditional_opacity_slider(self):
        patch = (ROOT / "patches" / "ayugram-followup-features.patch").read_text()

        self.assertIn("deletedMessageTransparency", patch)
        self.assertIn("entries.append(.slider(0, 6", patch)
        self.assertIn("value.semiTransparentDeletedMessages", patch)
        slider_handler = patch.index("}, slider: { id, value in")
        interface_controller = patch.index("func ayuInterfacePageController")
        material_controller = patch.find("func ayuMaterialDesignController")
        self.assertGreater(slider_handler, interface_controller)
        self.assertEqual(material_controller, -1)
        self.assertIn("+        var entries: [AyuSectionedEntry]", patch)
        self.assertIn("let remainingEntries: [AyuSectionedEntry]", patch)
        self.assertIn("entries.append(contentsOf: remainingEntries)", patch)
        self.assertIn("minimumValue: minimumValue, maximumValue: maximumValue", patch)
        self.assertIn("raw.githubusercontent.com/dsn2fvhmn4-lgtm/AyuGramm-IOS/main/assets/ayugram_ios_badges.json", patch)

    def test_ios_developer_badges_use_the_leading_name_slot(self):
        patch = (ROOT / "patches" / "ayugram-developer-badges.patch").read_text()

        self.assertIn("case ayuDeveloper(documentId: Int64, text: String?)", patch)
        self.assertIn("verifiedIcon = .ayuDeveloper", patch)
        self.assertIn("titleVerifiedIcon = .emojiStatus", patch)
        self.assertIn("currentVerifiedIconContent = .animation", patch)
        self.assertIn('replacingOccurrences(of: "(name)"', patch)


if __name__ == "__main__":
    unittest.main()
