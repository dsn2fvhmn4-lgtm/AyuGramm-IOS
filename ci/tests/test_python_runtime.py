"""CI check: run the embedded Python plugin runtime suite in the cheap phase.

This loads runtime/tests (the exteraGram SDK shim and the compatibility report)
and runs them, so a broken shim fails the Actions source checks in minutes,
before the native build. It does not touch the native patch or Bazel.
"""
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNTIME_TESTS = os.path.join(ROOT, "runtime", "tests")


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    if os.path.isdir(RUNTIME_TESTS):
        suite.addTests(loader.discover(start_dir=RUNTIME_TESTS, pattern="test_*.py", top_level_dir=RUNTIME_TESTS))
    return suite


class RuntimePresenceTest(unittest.TestCase):
    def test_runtime_tree_present(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, "runtime", "python", "_ayu_host.py")))
        self.assertTrue(os.path.exists(os.path.join(ROOT, "runtime", "hook_map.json")))


if __name__ == "__main__":
    unittest.main()
