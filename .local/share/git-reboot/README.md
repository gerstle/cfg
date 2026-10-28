# git-reboot

Personal shell tooling; Python 3.9+ and Git are required. Herdr integration uses the installed `herdr` CLI.

```sh
git-reboot                  # update, then ask about each eligible worktree/branch
git-reboot --dry-run        # offline preview; no writes, fetch, switch, or prune
git-reboot --no-cleanup     # update only
git-reboot --cleanup-only   # interactive cleanup using existing local refs
```

`git-reboot` runs directly from `~/.local/bin`; no shell aliases or functions are required. `git reboot` also works.

For each eligible worktree, one `[y/N/q]` prompt covers the checkout directory and its branch. Enter accepts No; `q`, EOF, or Ctrl-C stops cleanup. Noninteractive stdin only lists cleanup candidates. Updating the default branch still runs unless `--dry-run` or `--cleanup-only` was given.

The update fetches/prunes **origin**, resolves its advertised default branch (or `reboot.defaultBranch`), updates an existing checkout of that branch with `pull --ff-only`, and prunes stale worktree records. If the default branch has no checkout, it switches the invoking checkout to that branch. Dirty or locked target checkouts and update failures stop the command. An existing default-branch checkout is updated in place; the invoking worktree is preserved.

Cleanup accepts two kinds of integration evidence:

- The branch tip is an ancestor of the local default branch.
- The branch's complete tracked tree exactly matches a commit reachable from the local default branch. The prompt discloses that deleting the branch discards its distinct history. Tree identity proves file equivalence at that historical commit, not that its behavior is still present today.

After confirmation, a Git ref transaction verifies the reviewed default-branch tip and deletes the candidate only if its tip still matches. This checks integration against the default branch rather than `git branch -d`'s potentially stale configured upstream. Branch configuration is removed after successful ref deletion.

A missing upstream does not prove integration. Branches with no upstream can qualify. No remote branches are deleted by cleanup; normal fetch pruning removes stale remote-tracking refs.

Primary and invoking checkouts, dirty/untracked/locked/detached worktrees, open Herdr workspaces, and protected branches are skipped. Ignored files/directories are listed before confirmation; accepting removes those along with the worktree. Symlinks under `~/.local/bin` and `~/bin` pointing into a worktree protect it. This is a targeted launcher check, not a general dependency or process detector.

Herdr state is queried when its CLI is installed. Unknown/unavailable state prevents worktree removal; run from a Herdr terminal when Herdr is configured. Herdr ownership is recognized at its standard `~/.herdr/worktrees` location; the CLI does not expose an ownership flag for closed worktrees elsewhere. For a selected, closed worktree there, the helper opens a temporary workspace with `--no-focus`, verifies the returned ID and `already_open=false`, and invokes `herdr worktree remove` without `--force`. Already-open workspaces are protected. If removal fails after opening, the command reports the workspace to inspect. Herdr operations have no fallback to direct Git removal.

The helper rechecks worktree registration, branch tips, default-branch tip, local files, launchers, and Herdr state after confirmation. It does not detect every editor, terminal, external reference, or background process; the individual prompts remain part of deciding whether a checkout is unused.

Default protected branch patterns: `main`, `master`, `trunk`, `develop`, `development`, `backup/*`, `release/*`, plus the resolved default branch. Add repository-local patterns or override default-branch discovery with:

```sh
git config --add reboot.protectBranch 'personal-*'
git config reboot.defaultBranch main
```

Read-only previews use `origin/HEAD`, or the only local branch named `main`/`master`, unless configured. They explicitly use existing local refs; normal execution refreshes origin first.

Run the integration suite (temporary repositories only):

```sh
GIT_REBOOT_TOOL="$HOME/.local/bin/git-reboot" python3 "$HOME/.local/share/git-reboot/test_git_reboot.py"
```

After removing legacy shell wrappers, start a new shell to clear any definitions still loaded in an existing terminal.
