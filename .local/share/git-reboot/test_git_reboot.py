"""Behavior tests: all Git writes and fake Herdr operations stay in temp dirs."""
import json
import os
from pathlib import Path
import pty
import selectors
import subprocess
import sys
import tempfile
import time
import unittest

TOOL = Path(os.environ.get('GIT_REBOOT_TOOL', Path(__file__).with_name('git-reboot')))


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='git reboot test ')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / 'checkout'
        self.remote = self.root / 'origin.git'
        self.home = self.root / 'home'
        self.home.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.state = self.root / 'herdr.json'
        self.state.write_text(json.dumps({'open': {}, 'calls': []}))
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_', 'HERDR_'))}
        self.env.update(HOME=str(self.home), GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1',
                        GIT_AUTHOR_NAME='Test', GIT_AUTHOR_EMAIL='test@example.invalid',
                        GIT_COMMITTER_NAME='Test', GIT_COMMITTER_EMAIL='test@example.invalid',
                        HERDR_ENV='1', REBOOT_HERDR_STATE=str(self.state),
                        PATH=str(self.bin) + os.pathsep + os.environ['PATH'])
        fake = '''#!PYTHON
import json, os, subprocess, sys
p=os.environ['REBOOT_HERDR_STATE']; s=json.load(open(p)); args=sys.argv[1:]
s['calls'].append(args)
def save():
    with open(p,'w') as f: json.dump(s,f)
if args[:2]==['worktree','list']:
    if s.get('post_open_fail') and any(c[:2]==['worktree','open'] for c in s['calls']):
        save(); sys.exit(1)
    if s.get('replace_after_open') and any(c[:2]==['worktree','open'] for c in s['calls']):
        s['open']={p:'replacement-workspace' for p in s['open']}
    cwd=args[args.index('--cwd')+1]
    out=subprocess.check_output(['git','-C',cwd,'worktree','list','--porcelain'],text=True)
    rows=[]
    for record in out.strip().split('\\n\\n'):
        path=record.splitlines()[0][9:]
        row={'path':path}
        if path in s['open']: row['open_workspace_id']=s['open'][path]
        rows.append(row)
    save(); print(json.dumps({'result':{'worktrees':rows}}))
elif args[:2]==['worktree','open']:
    path=args[args.index('--path')+1]; s['open'][path]='temporary-test-workspace'
    save(); print(json.dumps({'result':{'workspace':{'workspace_id':'temporary-test-workspace'},
                                       'already_open':s.get('open_race',False),'worktree':{'path':path}}}))
elif args[:2]==['worktree','remove']:
    wid=args[args.index('--workspace')+1]
    path=next(p for p,v in s['open'].items() if v==wid)
    subprocess.run(['git','worktree','remove','--',path],check=True)
    del s['open'][path]; save(); print(json.dumps({'result':{'removed':True}}))
else:
    sys.exit(2)
'''.replace('PYTHON', sys.executable)
        (self.bin / 'herdr').write_text(fake)
        (self.bin / 'herdr').chmod(0o755)
        self.git('init', '--bare', str(self.remote), cwd=self.root)
        self.git('init', '-b', 'main', str(self.repo), cwd=self.root)
        (self.repo / 'base').write_text('base\n')
        self.git('add', '.')
        self.git('commit', '-m', 'base')
        self.git('remote', 'add', 'origin', str(self.remote))
        self.git('push', '-u', 'origin', 'main')
        self.git('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')
        self.git('symbolic-ref', 'HEAD', 'refs/heads/main', cwd=self.remote)

    def git(self, *args, cwd=None, check=True):
        return subprocess.run(['git', *args], cwd=cwd or self.repo, env=self.env,
                              text=True, capture_output=True, check=check).stdout.strip()

    def worktree(self, branch='topic', integrated=True, squash=False, owned=False):
        path = (self.home / '.herdr/worktrees/repo' if owned else self.root) / branch
        path.parent.mkdir(parents=True, exist_ok=True)
        self.git('worktree', 'add', '-b', branch, str(path))
        if squash:
            (path / 'feature').write_text('one\n')
            self.git('add', '.', cwd=path)
            self.git('commit', '-m', 'one', cwd=path)
            (path / 'feature').write_text('two\n')
            self.git('commit', '-am', 'two', cwd=path)
            self.git('merge', '--squash', branch)
            self.git('commit', '-m', 'squashed feature')
        elif not integrated:
            (path / 'unique').write_text('keep me\n')
            self.git('add', '.', cwd=path)
            self.git('commit', '-m', 'unmerged', cwd=path)
        return path

    def invoke(self, *args, answers=None, before_answer=None, cwd=None):
        cmd = [sys.executable, str(TOOL), *args]
        if answers is None:
            p = subprocess.run(cmd, cwd=cwd or self.repo, env=self.env,
                               input='', text=True, capture_output=True, timeout=15)
            return p.returncode, p.stdout + p.stderr
        master, slave = pty.openpty()
        p = subprocess.Popen(cmd, cwd=cwd or self.repo, env=self.env, stdin=slave,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        os.close(slave)
        output = b''
        answered = 0
        deadline = time.monotonic() + 20
        selector = selectors.DefaultSelector()
        selector.register(p.stdout, selectors.EVENT_READ)
        try:
            while time.monotonic() < deadline:
                if selector.select(0.1):
                    data = os.read(p.stdout.fileno(), 65536)
                    if not data:
                        break
                    output += data
                    while output.count(b'[y/N/q] ') > answered:
                        if before_answer:
                            before_answer(answered)
                        answer = answers[answered] if answered < len(answers) else 'q'
                        os.write(master, (answer + '\n').encode())
                        answered += 1
            else:
                p.kill()
                self.fail('interactive command timed out: ' + output.decode())
            return p.wait(timeout=5), output.decode()
        finally:
            selector.close()
            p.stdout.close()
            os.close(master)
            if p.poll() is None:
                p.kill()
                p.wait()

    def exists(self, branch):
        return bool(self.git('show-ref', '--verify', 'refs/heads/' + branch, check=False))

    def test_default_prompts_and_removes_worktree_and_branch(self):
        path = self.worktree()
        code, out = self.invoke(answers=['y'])
        self.assertEqual(code, 0, out)
        self.assertFalse(path.exists(), out)
        self.assertFalse(self.exists('topic'), out)
        self.assertIn('ancestor', out)

    def test_noninteractive_keeps_everything(self):
        path = self.worktree()
        code, out = self.invoke('--cleanup-only')
        self.assertEqual(code, 0, out)
        self.assertTrue(path.exists())
        self.assertTrue(self.exists('topic'))
        self.assertIn('noninteractive', out.lower())

    def test_no_and_quit_are_honored(self):
        paths = [self.worktree(n) for n in ['one', 'two', 'three']]
        code, out = self.invoke('--cleanup-only', answers=['', 'q'])
        self.assertEqual(code, 0, out)
        self.assertTrue(all(p.exists() for p in paths))
        self.assertEqual(out.count('[y/N/q] '), 2, out)

    def test_standalone_branch_needs_confirmation(self):
        self.git('branch', 'orphan-name')
        code, out = self.invoke('--cleanup-only', answers=['y'])
        self.assertEqual(code, 0, out)
        self.assertFalse(self.exists('orphan-name'))
        self.assertIn('Remove branch', out)

    def test_dirty_untracked_locked_divergent_and_detached_are_kept(self):
        dirty = self.worktree('dirty')
        (dirty / 'base').write_text('changed\n')
        untracked = self.worktree('untracked')
        (untracked / 'notes').write_text('save\n')
        locked = self.worktree('locked')
        self.git('worktree', 'lock', str(locked))
        divergent = self.worktree('divergent', integrated=False)
        detached = self.root / 'detached'
        self.git('worktree', 'add', '--detach', str(detached))
        code, out = self.invoke('--cleanup-only', answers=['y'] * 10)
        self.assertEqual(code, 0, out)
        self.assertTrue(all(p.exists() for p in [dirty, untracked, locked, divergent, detached]))
        self.assertNotIn('[y/N/q]', out)

    def test_deleted_upstream_does_not_prove_integration(self):
        path = self.worktree(integrated=False)
        self.git('config', 'branch.topic.remote', 'origin')
        self.git('config', 'branch.topic.merge', 'refs/heads/gone')
        code, out = self.invoke('--cleanup-only', answers=['y'])
        self.assertEqual(code, 0, out)
        self.assertTrue(path.exists())
        self.assertIn('unproven', out.lower())

    def test_squash_match_requires_explicit_confirmation(self):
        path = self.worktree(squash=True)
        code, out = self.invoke('--cleanup-only', answers=['y'])
        self.assertEqual(code, 0, out)
        self.assertFalse(path.exists(), out)
        self.assertFalse(self.exists('topic'), out)
        self.assertIn('exact tree', out.lower())
        self.assertIn('history', out.lower())

    def test_ignored_files_are_disclosed_before_removal(self):
        (self.repo / '.gitignore').write_text('cache/\n')
        self.git('add', '.')
        self.git('commit', '-m', 'ignore cache')
        path = self.worktree()
        (path / 'cache').mkdir()
        (path / 'cache/data').write_text('ignored\n')
        code, out = self.invoke('--cleanup-only', answers=['y'])
        self.assertEqual(code, 0, out)
        self.assertFalse(path.exists(), out)
        self.assertIn('cache/', out)
        self.assertIn('ignored', out.lower())

    def test_open_workspace_and_invoking_checkout_are_kept(self):
        active = self.worktree('active')
        invoking = self.worktree('invoking')
        state = json.loads(self.state.read_text())
        state['open'][str(active)] = 'already-open'
        self.state.write_text(json.dumps(state))
        code, out = self.invoke('--cleanup-only', cwd=invoking, answers=['y'] * 3)
        self.assertEqual(code, 0, out)
        self.assertTrue(active.exists())
        self.assertTrue(invoking.exists())
        self.assertNotIn('[y/N/q]', out)

    def test_closed_herdr_worktree_uses_herdr(self):
        path = self.worktree(owned=True)
        code, out = self.invoke('--cleanup-only', answers=['y'])
        self.assertEqual(code, 0, out)
        self.assertFalse(path.exists(), out)
        calls = json.loads(self.state.read_text())['calls']
        self.assertTrue(any(c[:2] == ['worktree', 'open'] and '--no-focus' in c for c in calls))
        self.assertTrue(any(c[:2] == ['worktree', 'remove'] and '--force' not in c for c in calls))

    def test_herdr_failure_keeps_worktrees(self):
        path = self.worktree()
        (self.bin / 'herdr').write_text('#!/bin/sh\nexit 1\n')
        code, out = self.invoke('--cleanup-only', answers=['y'])
        self.assertEqual(code, 0, out)
        self.assertTrue(path.exists())
        self.assertIn('Herdr', out)

    def test_protected_branches_are_kept(self):
        self.git('branch', 'backup/snapshot')
        self.git('branch', 'personal-keep')
        self.git('config', '--add', 'reboot.protectBranch', 'personal-*')
        code, out = self.invoke('--cleanup-only', answers=['y'] * 5)
        self.assertEqual(code, 0, out)
        self.assertTrue(self.exists('main'))
        self.assertTrue(self.exists('backup/snapshot'))
        self.assertTrue(self.exists('personal-keep'))
        self.assertNotIn('[y/N/q]', out)

    def test_new_changes_while_prompting_prevent_removal(self):
        path = self.worktree()
        def change(_):
            (path / 'new-work').write_text('keep\n')
        code, out = self.invoke('--cleanup-only', answers=['y'], before_answer=change)
        self.assertEqual(code, 0, out)
        self.assertTrue(path.exists(), out)
        self.assertTrue(self.exists('topic'))
        self.assertIn('changed', out.lower())

    def test_changed_branch_tip_while_prompting_prevents_deletion(self):
        self.git('branch', 'topic')
        def change(_):
            self.git('switch', '-c', 'new-tip')
            (self.repo / 'later').write_text('later\n')
            self.git('add', '.')
            self.git('commit', '-m', 'later')
            self.git('branch', '-f', 'topic', 'HEAD')
            self.git('switch', 'main')
        code, out = self.invoke('--cleanup-only', answers=['y'], before_answer=change)
        self.assertEqual(code, 0, out)
        self.assertTrue(self.exists('topic'))
        self.assertIn('changed', out.lower())

    def test_dry_run_does_not_fetch_switch_update_or_prune(self):
        self.worktree()
        self.git('switch', '-c', 'invoker')
        before = self.git('show-ref')
        gitdir = self.repo / '.git'
        snapshot = {str(p.relative_to(gitdir)): p.read_bytes() for p in gitdir.rglob('*') if p.is_file()}
        code, out = self.invoke('--dry-run', answers=['y'] * 5)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.git('branch', '--show-current'), 'invoker')
        self.assertEqual(self.git('show-ref'), before)
        self.assertEqual(snapshot, {str(p.relative_to(gitdir)): p.read_bytes() for p in gitdir.rglob('*') if p.is_file()})
        self.assertNotIn('[y/N/q]', out)

    def test_no_cleanup_updates_without_prompting(self):
        path = self.worktree()
        code, out = self.invoke('--no-cleanup', answers=['y'] * 5)
        self.assertEqual(code, 0, out)
        self.assertTrue(path.exists())
        self.assertNotIn('[y/N/q]', out)

    def test_failed_fetch_stops_cleanup(self):
        path = self.worktree()
        self.git('remote', 'set-url', 'origin', str(self.root / 'missing.git'))
        code, out = self.invoke(answers=['y'] * 5)
        self.assertNotEqual(code, 0, out)
        self.assertTrue(path.exists())
        self.assertNotIn('[y/N/q]', out)

    def test_worktree_path_with_spaces(self):
        path = self.root / 'work tree with spaces'
        self.git('worktree', 'add', '-b', 'topic', str(path))
        code, out = self.invoke('--cleanup-only', answers=['y'])
        self.assertEqual(code, 0, out)
        self.assertFalse(path.exists(), out)

    def test_worktree_opened_while_prompting_is_kept(self):
        path = self.worktree()
        def change(_):
            state = json.loads(self.state.read_text())
            state['open'][str(path)] = 'newly-open'
            self.state.write_text(json.dumps(state))
        code, out = self.invoke('--cleanup-only', answers=['y'], before_answer=change)
        self.assertEqual(code, 0, out)
        self.assertTrue(path.exists(), out)
        self.assertIn('changed', out)

    def test_launcher_reference_protects_worktree(self):
        path = self.worktree()
        local_bin = self.home / '.local/bin'
        local_bin.mkdir(parents=True)
        (local_bin / 'my-app').symlink_to(path / 'base')
        code, out = self.invoke('--cleanup-only', answers=['y'])
        self.assertEqual(code, 0, out)
        self.assertTrue(path.exists(), out)
        self.assertIn('referenced by launcher', out)

    def test_dirty_default_checkout_stops_update_and_cleanup(self):
        path = self.worktree()
        (self.repo / 'base').write_text('unsaved\n')
        code, out = self.invoke(answers=['y'])
        self.assertNotEqual(code, 0, out)
        self.assertTrue(path.exists(), out)
        self.assertNotIn('[y/N/q]', out)

    def test_eof_stops_cleanup(self):
        path = self.worktree()
        code, out = self.invoke('--cleanup-only', answers=['\x04'])
        self.assertEqual(code, 0, out)
        self.assertTrue(path.exists(), out)
        self.assertIn('stopped', out)

    def test_updates_existing_main_checkout_without_switching_invoker(self):
        path = self.worktree('invoker')
        other = self.root / 'other'
        self.git('clone', str(self.remote), str(other), cwd=self.root)
        (other / 'remote-update').write_text('new\n')
        self.git('add', '.', cwd=other)
        self.git('commit', '-m', 'remote update', cwd=other)
        self.git('push', cwd=other)
        code, out = self.invoke('--no-cleanup', cwd=path)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.repo / 'remote-update').exists())
        self.assertEqual(self.git('branch', '--show-current', cwd=path), 'invoker')

    def test_non_fast_forward_update_stops_cleanup(self):
        path = self.worktree()
        other = self.root / 'other'
        self.git('clone', str(self.remote), str(other), cwd=self.root)
        for cwd, name in [(self.repo, 'local'), (other, 'remote')]:
            (cwd / name).write_text(name)
            self.git('add', '.', cwd=cwd)
            self.git('commit', '-m', name, cwd=cwd)
        self.git('push', cwd=other)
        code, out = self.invoke(answers=['y'])
        self.assertNotEqual(code, 0, out)
        self.assertTrue(path.exists(), out)
        self.assertNotIn('[y/N/q]', out)

    def test_integrated_branch_ahead_of_its_upstream_is_removed(self):
        path = self.worktree()
        self.git('push', '-u', 'origin', 'topic', cwd=path)
        (path / 'new-feature').write_text('merged\n')
        self.git('add', '.', cwd=path)
        self.git('commit', '-m', 'feature not pushed to topic', cwd=path)
        self.git('merge', '--ff-only', 'topic')
        code, out = self.invoke('--cleanup-only', answers=['y'])
        self.assertEqual(code, 0, out)
        self.assertFalse(path.exists(), out)
        self.assertFalse(self.exists('topic'), out)
        self.assertFalse(self.git('config', '--get-regexp', '^branch\\.topic\\.', check=False))

    def test_herdr_replacement_workspace_is_not_removed(self):
        path = self.worktree(owned=True)
        state = json.loads(self.state.read_text())
        state['replace_after_open'] = True
        self.state.write_text(json.dumps(state))
        code, out = self.invoke('--cleanup-only', answers=['y'])
        self.assertNotEqual(code, 0, out)
        self.assertTrue(path.exists(), out)
        calls = json.loads(self.state.read_text())['calls']
        self.assertFalse(any(c[:2] == ['worktree', 'remove'] for c in calls), out)
        self.assertIn('temporary-test-workspace', out)

    def test_herdr_post_open_failure_reports_temporary_workspace(self):
        path = self.worktree(owned=True)
        state = json.loads(self.state.read_text())
        state['post_open_fail'] = True
        self.state.write_text(json.dumps(state))
        code, out = self.invoke('--cleanup-only', answers=['y'])
        self.assertNotEqual(code, 0, out)
        self.assertTrue(path.exists(), out)
        self.assertIn('temporary-test-workspace', out)

    def test_herdr_open_race_does_not_remove_existing_workspace(self):
        path = self.worktree(owned=True)
        state = json.loads(self.state.read_text())
        state['open_race'] = True
        self.state.write_text(json.dumps(state))
        code, out = self.invoke('--cleanup-only', answers=['y'])
        self.assertNotEqual(code, 0, out)
        self.assertTrue(path.exists(), out)
        calls = json.loads(self.state.read_text())['calls']
        self.assertFalse(any(c[:2] == ['worktree', 'remove'] for c in calls), out)


if __name__ == '__main__':
    unittest.main(verbosity=2)
