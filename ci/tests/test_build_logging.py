import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_logging import run_logged_build


class BuildLoggingTests(unittest.TestCase):
    def test_stdout_and_stderr_are_redacted_in_console_and_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / 'build.log'
            console = io.StringIO()
            with contextlib.redirect_stdout(console):
                run_logged_build([sys.executable, '-c', 'import sys; print("id=TEST_API_ID"); print("hash=TEST_API_HASH", file=sys.stderr)'],
                                 temp, log, ('TEST_API_ID', 'TEST_API_HASH', ''))
            for output in (log.read_text(), console.getvalue()):
                self.assertNotIn('TEST_API_ID', output)
                self.assertNotIn('TEST_API_HASH', output)
                self.assertEqual(output.count('[REDACTED]'), 2)

    def test_failure_retains_diagnostics_and_exit_code(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / 'build.log'
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(subprocess.CalledProcessError) as error:
                    run_logged_build([sys.executable, '-c', 'import sys; print("compile failed"); sys.exit(7)'], temp, log)
            self.assertEqual(error.exception.returncode, 7)
            self.assertIn('compile failed', log.read_text())


if __name__ == '__main__':
    unittest.main()
