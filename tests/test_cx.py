import os
from pathlib import Path
import subprocess
import tempfile
import unittest

CX = Path(__file__).resolve().parents[1] / 'cx'
UUID = '11111111-1111-1111-1111-111111111111'


class CxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.legacy = self.base / 'legacy'
        self.legacy.mkdir()
        (self.legacy / 'auth.json').write_text('original')
        self.root = self.base / 'cx'
        self.stub = self.base / 'codex-stub'
        self.stub.write_text('''#!/usr/bin/env python3
import os
from pathlib import Path
import sys
home = Path(os.environ['CODEX_HOME'])
if 'resume' in sys.argv and home.name in ('legacy', 'first'):
    auth = home / 'auth.json'
    assert auth.read_text() == 'second'
    auth.write_text('refreshed')
''')
        self.stub.chmod(0o755)
        self.env = os.environ | {
            'CX_ROOT': str(self.root),
            'CX_LEGACY_HOME': str(self.legacy),
            'CX_CODEX_BIN': str(self.stub),
        }

    def call(self, *args):
        return subprocess.run([str(CX), *args], env=self.env, text=True, capture_output=True)

    def test_import_and_isolated_run(self):
        self.assertEqual(self.call('import-current', 'main').returncode, 0)
        self.assertEqual(self.call('run', 'main').returncode, 0)
        self.assertEqual((self.root / 'accounts/main/auth.json').read_text(), 'original')
        self.assertEqual((self.root / 'accounts/main/config.toml').read_text(), 'model_context_window = 500000\n')
        self.assertNotEqual(self.call('import-current', 'main').returncode, 0)
        (self.legacy / 'auth.json').write_text('new-login')
        self.assertEqual(self.call('import-current', 'main', '--replace').returncode, 0)
        self.assertEqual((self.root / 'accounts/main/auth.json').read_text(), 'new-login')

    def test_switch_restores_original_and_saves_refresh(self):
        profile = self.root / 'accounts/second'
        profile.mkdir(parents=True)
        (profile / 'auth.json').write_text('second')
        sessions = self.legacy / 'sessions'
        sessions.mkdir()
        (sessions / f'rollout-{UUID}.jsonl').write_text('')
        self.assertEqual(self.call('switch', UUID, '--to', 'second').returncode, 0)
        self.assertEqual((self.legacy / 'auth.json').read_text(), 'original')
        self.assertEqual((profile / 'auth.json').read_text(), 'refreshed')
        self.assertFalse((self.root / 'shared-backup/account.json').exists())

    def test_resume_from_another_profile(self):
        source = self.root / 'accounts/first'
        target = self.root / 'accounts/second'
        source.mkdir(parents=True)
        target.mkdir(parents=True)
        (source / 'auth.json').write_text('original')
        (target / 'auth.json').write_text('second')
        sessions = source / 'sessions'
        sessions.mkdir()
        (sessions / f'rollout-{UUID}.jsonl').write_text('')
        self.assertEqual(self.call('resume', 'second', UUID).returncode, 0)
        self.assertEqual((source / 'auth.json').read_text(), 'original')
        self.assertEqual((target / 'auth.json').read_text(), 'refreshed')

    def test_link_current_uses_live_login(self):
        self.assertEqual(self.call('import-current', 'main').returncode, 0)
        self.assertEqual(self.call('link-current', 'main').returncode, 0)
        self.assertFalse((self.root / 'accounts/main/auth.json').exists())
        self.assertEqual(self.call('run', 'main').returncode, 0)
        self.assertEqual(self.call('import-current', 'main', '--replace').returncode, 0)
        self.assertEqual((self.legacy / 'auth.json').read_text(), 'original')

    def test_linked_profile_refreshes_live_login_after_switch(self):
        self.assertEqual(self.call('link-current', 'main').returncode, 0)
        source = self.root / 'accounts/first'
        source.mkdir(parents=True)
        (source / 'auth.json').write_text('source-login')
        sessions = source / 'sessions'
        sessions.mkdir()
        (sessions / f'rollout-{UUID}.jsonl').write_text('')
        self.stub.write_text('''#!/usr/bin/env python3
import os
from pathlib import Path
import sys
home = Path(os.environ['CODEX_HOME'])
assert home.name == 'first'
auth = home / 'auth.json'
assert auth.read_text() == 'original'
auth.write_text('refreshed')
''')
        self.assertEqual(self.call('resume', 'main', UUID).returncode, 0)
        self.assertEqual((source / 'auth.json').read_text(), 'source-login')
        self.assertEqual((self.legacy / 'auth.json').read_text(), 'refreshed')


if __name__ == '__main__':
    unittest.main()
