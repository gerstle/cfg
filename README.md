# dotfile management

Uses the bare repo approach outlined here: https://www.atlassian.com/git/tutorials/dotfiles

1. `echo ".cfg" >> .gitignore`
2. `git clone --bare git@github.com:gerstle/cfg.git $HOME/.cfg`
3. `alias config='/usr/bin/git --git-dir=$HOME/.cfg/ --work-tree=$HOME'`
4. `config checkout`
5. delete any conflicts, re-run checkout
6. `config config --local status.showUntrackedFiles no`

