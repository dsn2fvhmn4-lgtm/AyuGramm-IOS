from pathlib import Path
import sys
import unittest
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preflight import contract_errors, reaction_dependency_errors


class UIContractTests(unittest.TestCase):
    def test_detects_the_missing_alert_import_that_broke_the_first_build(self):
        self.assertTrue(contract_errors('textAlertController(context: context, title: "AyuGram")'))
        self.assertFalse(contract_errors('import PresentationDataUtils\ntextAlertController(context: context, title: "AyuGram")'))

    def test_formatted_history_requires_its_actual_module(self):
        self.assertTrue(contract_errors('stringWithAppliedEntities(text, entities: [])'))
        self.assertFalse(contract_errors('import TextFormat\nstringWithAppliedEntities(text, entities: [])'))
        self.assertFalse(contract_errors('stringWithAppliedEntities(text, entities: [])', 'submodules/TextFormat/Sources/StringWithAppliedEntities.swift'))

    def test_reaction_helpers_require_the_declaring_module(self):
        call = 'item.context.ayuVisibleMessageReactionsAndPeers(accountPeer: peer, message: message)'
        self.assertTrue(contract_errors(call))
        self.assertFalse(contract_errors('import AccountContext\n' + call))

    def test_optional_chat_list_search_state_is_not_a_boolean(self):
        path = 'submodules/ChatListUI/Sources/ChatListControllerNode.swift'
        broken = 'if foldersAtBottom, !self.isSearchDisplayControllerActive { showFolders() }'
        self.assertTrue(contract_errors(broken, path))
        self.assertTrue(contract_errors(broken.replace('!self.', '! self.'), path))
        self.assertFalse(contract_errors(broken.replace('!self.isSearchDisplayControllerActive', 'self.isSearchDisplayControllerActive == nil'), path))
        self.assertFalse(contract_errors(broken, 'UnrelatedController.swift'))

    def test_ayugram_buttons_do_not_use_deprecated_edge_insets(self):
        path = 'submodules/TelegramUI/Sources/AyuAttachmentMenuController.swift'
        broken = 'row.contentEdgeInsets = UIEdgeInsets(top: 0.0, left: 62.0, bottom: 0.0, right: 12.0)'
        self.assertTrue(contract_errors(broken, path))
        self.assertTrue(contract_errors(broken.replace('content', 'title'), path))
        self.assertFalse(contract_errors('configuration.contentInsets = NSDirectionalEdgeInsets(top: 0.0, leading: 62.0, bottom: 0.0, trailing: 12.0)', path))
        self.assertFalse(contract_errors(broken, 'submodules/TelegramUI/Sources/ChatController.swift'))

    def test_ayugram_text_drawing_avoids_macos_temporary_attributes(self):
        path = 'submodules/TelegramUI/Sources/AyuLyricsLineLabel.swift'
        broken = 'self.manager.addTemporaryAttribute(.foregroundColor, value: UIColor.white, forCharacterRange: characters)'
        self.assertTrue(contract_errors(broken, path))
        self.assertTrue(contract_errors('self.manager.removeTemporaryAttribute(.foregroundColor, forCharacterRange: characters)', path))
        self.assertFalse(contract_errors('self.highlightManager.drawGlyphs(forGlyphRange: glyphs, at: .zero)', path))

    def test_reaction_helpers_require_a_direct_bazel_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            source = package / 'Sources' / 'Message.swift'
            source.parent.mkdir()
            source.write_text('import AccountContext\nitem.context.ayuVisibleMessageReactions(message: message)', encoding='utf-8')
            build = package / 'BUILD'
            build.write_text('deps = ["//submodules/TelegramCore"]', encoding='utf-8')
            self.assertTrue(reaction_dependency_errors(source))
            build.write_text('deps = ["//submodules/AccountContext"]', encoding='utf-8')
            self.assertFalse(reaction_dependency_errors(source))


if __name__ == '__main__':
    unittest.main()
