from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preflight import contract_errors


class UIContractTests(unittest.TestCase):
    def test_detects_the_missing_alert_import_that_broke_the_first_build(self):
        self.assertTrue(contract_errors('textAlertController(context: context, title: "AyuGram")'))
        self.assertFalse(contract_errors('import PresentationDataUtils\ntextAlertController(context: context, title: "AyuGram")'))

    def test_formatted_history_requires_its_actual_module(self):
        self.assertTrue(contract_errors('stringWithAppliedEntities(text, entities: [])'))
        self.assertFalse(contract_errors('import TextFormat\nstringWithAppliedEntities(text, entities: [])'))


if __name__ == '__main__':
    unittest.main()
